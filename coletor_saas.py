import csv
import json
import logging
import os
import re
import signal
import socket
import ssl
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlsplit

import oracledb
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

STOP_REQUESTED = False


# ============================================================
# HELPERS DE CONFIGURAÇÃO
# ============================================================

def utc_now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def now_local_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def env_str(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        raise ValueError(f"Variável obrigatória ausente: {name}")
    return "" if value is None else str(value)


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "sim", "s"}


def env_json_list(name: str) -> List[Dict[str, Any]]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} precisa conter JSON válido. Erro: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"{name} precisa ser uma lista JSON.")

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{name}[{idx}] precisa ser um objeto JSON.")
    return data


def resolve_output_dir(raw_value: str) -> Path:
    raw = raw_value.strip()
    if not raw:
        return BASE_DIR / "saida"

    path = Path(raw).expanduser()
    if path.is_absolute():
        return path

    parts = list(path.parts)
    if parts and parts[0] == BASE_DIR.name:
        path = Path(*parts[1:]) if len(parts) > 1 else Path("saida")

    return (BASE_DIR / path).resolve()


def resolve_config_dir(raw_value: str, default_dir_name: str) -> Path:
    raw = raw_value.strip()
    path = Path(raw).expanduser() if raw else Path(default_dir_name)

    if path.is_absolute():
        return path

    parts = list(path.parts)
    if parts and parts[0] == BASE_DIR.name:
        path = Path(*parts[1:]) if len(parts) > 1 else Path(default_dir_name)

    return (BASE_DIR / path).resolve()


def normalize_oracle_dsn(raw_value: str) -> str:
    dsn = raw_value.strip()
    if not dsn or ":" in dsn or "/" not in dsn:
        return dsn

    host_and_port, service = dsn.split("/", 1)
    port_digits = ""
    for char in reversed(host_and_port):
        if char.isdigit():
            port_digits = char + port_digits
        else:
            break

    if len(port_digits) not in {4, 5}:
        return dsn

    host = host_and_port[: -len(port_digits)].rstrip(":")
    if not host:
        return dsn

    return f"{host}:{port_digits}/{service}"


def find_oracle_client_lib_dir() -> Optional[Path]:
    configured = env_str("ORACLE_CLIENT_LIB_DIR", "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.exists():
            return candidate

    for part in os.getenv("PATH", "").split(os.pathsep):
        if not part:
            continue
        candidate = Path(part)
        if (candidate / "oci.dll").exists():
            return candidate

    local_appdata = os.getenv("LOCALAPPDATA", "").strip()
    if local_appdata:
        winget_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_root.exists():
            matches = sorted(winget_root.glob("Oracle.InstantClient.Basic*"))
            for match in reversed(matches):
                instant_clients = sorted(match.glob("instantclient_*"))
                for instant_client in reversed(instant_clients):
                    if (instant_client / "oci.dll").exists():
                        return instant_client

    return None


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").strip()


def iter_config_files(directory: Path, extensions: Sequence[str]) -> List[Path]:
    if not directory.exists():
        return []

    normalized = {ext.lower() for ext in extensions}
    files: List[Path] = []

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith("_") for part in path.relative_to(directory).parts):
            continue
        if path.suffix.lower() not in normalized:
            continue
        files.append(path)

    return files


def default_item_name(base_dir: Path, path: Path) -> str:
    relative = path.relative_to(base_dir)
    parts = list(relative.parts[:-1]) + [path.stem]
    clean_parts = [part.strip().replace(" ", "_") for part in parts if part.strip()]
    return "__".join(clean_parts) if clean_parts else path.stem


def relative_config_path(base_dir: Path, path: Path) -> str:
    return path.relative_to(base_dir).as_posix()


def slugify_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return cleaned or fallback


def default_http_target_name(source_name: str, url: str, index: int, multi_entries: bool) -> str:
    parsed = urlsplit(url)
    host_part = slugify_name(parsed.hostname or "", f"url_{index:02d}")
    path_part = slugify_name(parsed.path.strip("/"), "root")
    suffix = f"{host_part}_{path_part}"
    return f"{source_name}__{suffix}" if multi_entries else source_name


def parse_http_text_entries(base_dir: Path, path: Path, content: str) -> List[Dict[str, Any]]:
    source_name = default_item_name(base_dir, path)
    source_file = relative_config_path(base_dir, path)
    raw_entries: List[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        raw_entries.extend(part.strip() for part in stripped.split(",") if part.strip())

    if not raw_entries:
        raise ValueError(f"Arquivo HTTP sem URL valida: {path}")

    items: List[Dict[str, Any]] = []
    multi_entries = len(raw_entries) > 1

    for index, raw_entry in enumerate(raw_entries, start=1):
        name = ""
        url = raw_entry

        if "|" in raw_entry:
            maybe_name, maybe_url = raw_entry.split("|", 1)
            if maybe_name.strip() and maybe_url.strip():
                name = maybe_name.strip()
                url = maybe_url.strip()
        elif "=" in raw_entry:
            maybe_name, maybe_url = raw_entry.split("=", 1)
            if maybe_name.strip() and maybe_url.strip().lower().startswith(("http://", "https://")):
                name = maybe_name.strip()
                url = maybe_url.strip()

        items.append({
            "name": name or default_http_target_name(source_name, url, index, multi_entries),
            "url": url,
            "source_name": source_name,
            "source_file": source_file,
        })

    return items


def load_http_targets_from_dir(directory: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for path in iter_config_files(directory, [".url", ".txt", ".json"]):
        suffix = path.suffix.lower()
        content = read_text_file(path)
        if not content:
            raise ValueError(f"Arquivo HTTP vazio: {path}")

        if suffix == ".json":
            try:
                data = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Arquivo HTTP invalido ({path}): {exc}") from exc

            if not isinstance(data, dict):
                raise ValueError(f"Arquivo HTTP {path} precisa conter um objeto JSON.")

            item = dict(data)
            item.setdefault("source_name", default_item_name(directory, path))
            item.setdefault("source_file", relative_config_path(directory, path))
            item.setdefault("name", default_item_name(directory, path))
            items.append(item)
            continue

        items.extend(parse_http_text_entries(directory, path, content))

    return items


def load_oracle_probes_from_dir(directory: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for path in iter_config_files(directory, [".sql"]):
        sql = read_text_file(path)
        if not sql:
            raise ValueError(f"Arquivo SQL vazio: {path}")

        items.append({
            "name": default_item_name(directory, path),
            "sql": sql,
            "source_name": default_item_name(directory, path),
            "source_file": relative_config_path(directory, path),
        })

    return items


def merge_named_items(base_items: List[Dict[str, Any]], override_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    override_names = {
        str(item.get("name")).strip()
        for item in override_items
        if str(item.get("name", "")).strip()
    }
    merged = [
        item
        for item in base_items
        if str(item.get("name", "")).strip() not in override_names
    ]
    merged.extend(override_items)
    return merged


def load_named_json_objects(directory: Path) -> Dict[str, Dict[str, Any]]:
    items: Dict[str, Dict[str, Any]] = {}

    for path in iter_config_files(directory, [".json"]):
        content = read_text_file(path)
        if not content:
            raise ValueError(f"Arquivo JSON vazio: {path}")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Arquivo JSON invalido ({path}): {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Arquivo JSON {path} precisa conter um objeto.")

        items[default_item_name(directory, path)] = data

    return items


def lookup_schema_item(mapping: Any, key: Any) -> Any:
    if not isinstance(mapping, dict):
        return None

    candidates = [str(key), str(key).lower(), str(key).upper()]
    for candidate in candidates:
        if candidate in mapping:
            return mapping[candidate]

    lowered_mapping = {str(item_key).lower(): item_value for item_key, item_value in mapping.items()}
    return lowered_mapping.get(str(key).lower())


def schema_text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


# ============================================================
# MODELOS
# ============================================================

@dataclass
class HttpTarget:
    name: str
    url: str
    source_name: str = ""
    source_file: str = ""
    method: str = "GET"
    expected_statuses: Tuple[int, ...] = (200,)
    expected_text: str = ""
    timeout_seconds: int = 20
    verify_ssl: bool = True
    headers: Optional[Dict[str, str]] = None


@dataclass
class OracleProbe:
    name: str
    sql: str
    source_name: str = ""
    source_file: str = ""


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_NAME = env_str("APP_NAME", "coletor_saas")
OUTPUT_DIR = resolve_output_dir(env_str("OUTPUT_DIR", str(BASE_DIR / "saida")))
HTTP_TARGETS_DIR = resolve_config_dir(env_str("HTTP_TARGETS_DIR", ""), "http_targets")
FUNCTIONAL_PROBES_DIR = resolve_config_dir(env_str("FUNCTIONAL_PROBES_DIR", ""), "oracle_probes")
DATA_SCHEMA_DIR = resolve_config_dir(env_str("DATA_SCHEMA_DIR", ""), "data_schema")
DATASET_SCHEMA_DIR = DATA_SCHEMA_DIR / "datasets"
PROBE_SCHEMA_DIR = DATA_SCHEMA_DIR / "probes"
INTERVAL_SECONDS = env_int("INTERVAL_SECONDS", 30)
LOG_LEVEL = env_str("LOG_LEVEL", "INFO").upper()
ENABLE_HTTP = env_bool("ENABLE_HTTP", True)
ENABLE_ORACLE = env_bool("ENABLE_ORACLE", True)
ENABLE_FUNCTIONAL_PROBES = env_bool("ENABLE_FUNCTIONAL_PROBES", True)
ORACLE_LONG_RUNNING_SECONDS = env_int("ORACLE_LONG_RUNNING_SECONDS", 60)
HTTP_RETRIES = env_int("HTTP_RETRIES", 1)
HTTP_BACKOFF_SECONDS = env_int("HTTP_BACKOFF_SECONDS", 1)

HTTP_TARGETS_ENV_RAW = env_json_list("HTTP_TARGETS_JSON")
FUNCTIONAL_PROBES_ENV_RAW = env_json_list("FUNCTIONAL_PROBES_JSON")
HTTP_TARGETS_FILE_RAW = load_http_targets_from_dir(HTTP_TARGETS_DIR)
FUNCTIONAL_PROBES_FILE_RAW = load_oracle_probes_from_dir(FUNCTIONAL_PROBES_DIR)
HTTP_TARGETS_RAW = merge_named_items(HTTP_TARGETS_ENV_RAW, HTTP_TARGETS_FILE_RAW)
FUNCTIONAL_PROBES_RAW = merge_named_items(FUNCTIONAL_PROBES_ENV_RAW, FUNCTIONAL_PROBES_FILE_RAW)
DATASET_SCHEMAS = load_named_json_objects(DATASET_SCHEMA_DIR)
PROBE_SCHEMAS = load_named_json_objects(PROBE_SCHEMA_DIR)

ORACLE_USER = env_str("ORACLE_USER", "")
ORACLE_PASSWORD = env_str("ORACLE_PASSWORD", "")
ORACLE_DSN = normalize_oracle_dsn(env_str("ORACLE_DSN", ""))
ORACLE_FETCH_LOBS = env_bool("ORACLE_FETCH_LOBS", False)
ORACLE_CLIENT_LIB_DIR = find_oracle_client_lib_dir()
ORACLE_CLIENT_MODE = "thin"
ORACLE_CLIENT_INIT_ERROR = ""

HTTP_CSV = OUTPUT_DIR / "fact_http_health_checks.csv"
ORACLE_SUMMARY_CSV = OUTPUT_DIR / "fact_oracle_summary.csv"
ORACLE_PROBES_CSV = OUTPUT_DIR / "fact_oracle_probe_results.csv"
ORACLE_SUMMARY_METRICS_CSV = OUTPUT_DIR / "fact_oracle_summary_metrics.csv"
ORACLE_PROBE_VALUES_CSV = OUTPUT_DIR / "fact_oracle_probe_values.csv"
COLLECTOR_RUNS_CSV = OUTPUT_DIR / "fact_collection_runs.csv"
ERROR_LOG = OUTPUT_DIR / "errors.log"
APP_LOG = OUTPUT_DIR / "collector.log"

HTTP_HEADER = [
    "collection_id",
    "collected_at_local",
    "collected_at_utc",
    "http_target_name",
    "http_target_group_name",
    "http_target_file_path",
    "request_url",
    "request_method",
    "host_name",
    "remote_ip_address",
    "remote_port",
    "dns_duration_ms",
    "tcp_connect_duration_ms",
    "tls_handshake_duration_ms",
    "http_duration_ms",
    "http_status_code",
    "expected_http_status_codes",
    "expected_response_text",
    "is_expected_text_match",
    "is_success",
    "error_message",
]

ORACLE_SUMMARY_HEADER = [
    "collection_id",
    "collected_at_local",
    "collected_at_utc",
    "oracle_instance_name",
    "oracle_host_name",
    "oracle_database_name",
    "session_total_count",
    "session_active_count",
    "session_inactive_count",
    "wait_sqlnet_message_from_client_count",
    "wait_resmgr_cpu_quantum_count",
    "lock_count",
    "blocked_session_count",
    "long_running_active_session_count",
    "active_jdbc_session_count",
    "top_machine_name",
    "top_program_name",
    "top_username",
    "is_success",
    "error_message",
]

ORACLE_PROBES_HEADER = [
    "collection_id",
    "collected_at_local",
    "collected_at_utc",
    "oracle_probe_name",
    "oracle_probe_group_name",
    "oracle_probe_file_path",
    "oracle_probe_display_name",
    "oracle_probe_description",
    "probe_duration_ms",
    "probe_result_json",
    "is_success",
    "error_message",
]

ORACLE_SUMMARY_METRICS_HEADER = [
    "collection_id",
    "collected_at_local",
    "collected_at_utc",
    "oracle_instance_name",
    "oracle_host_name",
    "oracle_database_name",
    "metric_name",
    "metric_display_name",
    "metric_group_name",
    "metric_description",
    "metric_value",
    "is_success",
    "error_message",
]

ORACLE_PROBE_VALUES_HEADER = [
    "collection_id",
    "collected_at_local",
    "collected_at_utc",
    "oracle_probe_name",
    "oracle_probe_group_name",
    "oracle_probe_file_path",
    "oracle_probe_display_name",
    "oracle_probe_description",
    "result_column_name",
    "result_column_display_name",
    "result_column_description",
    "result_column_value",
    "result_value_display_name",
    "is_success",
    "error_message",
]

COLLECTOR_RUNS_HEADER = [
    "collection_id",
    "collected_at_local",
    "collected_at_utc",
    "http_target_count",
    "http_success_count",
    "http_error_count",
    "oracle_summary_success_flag",
    "oracle_probe_count",
    "oracle_probe_success_count",
    "oracle_probe_error_count",
    "collection_success_flag",
    "collection_health_label",
    "collection_duration_ms",
]


def build_http_targets() -> List[HttpTarget]:
    targets: List[HttpTarget] = []
    for item in HTTP_TARGETS_RAW:
        if not item.get("name") or not item.get("url"):
            raise ValueError("Cada alvo HTTP precisa ter, no minimo, name e url.")

        expected = item.get("expected_statuses", [200])
        if not isinstance(expected, list) or not expected:
            raise ValueError("expected_statuses precisa ser uma lista de inteiros.")

        targets.append(
            HttpTarget(
                name=str(item["name"]),
                url=str(item["url"]),
                source_name=str(item.get("source_name", "")),
                source_file=str(item.get("source_file", "")),
                method=str(item.get("method", "GET")).upper(),
                expected_statuses=tuple(int(x) for x in expected),
                expected_text=str(item.get("expected_text", "")),
                timeout_seconds=int(item.get("timeout_seconds", 20)),
                verify_ssl=bool(item.get("verify_ssl", True)),
                headers=item.get("headers") if isinstance(item.get("headers"), dict) else None,
            )
        )
    return targets


def build_oracle_probes() -> List[OracleProbe]:
    probes: List[OracleProbe] = []
    for item in FUNCTIONAL_PROBES_RAW:
        if not item.get("name") or not item.get("sql"):
            raise ValueError("Cada probe Oracle precisa ter, no minimo, name e sql.")
        probes.append(
            OracleProbe(
                name=str(item["name"]),
                sql=str(item["sql"]).strip().rstrip(";"),
                source_name=str(item.get("source_name", "")),
                source_file=str(item.get("source_file", "")),
            )
        )
    return probes


HTTP_TARGETS = build_http_targets()
ORACLE_PROBES = build_oracle_probes()


# ============================================================
# LOGGING E CSV
# ============================================================

def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_config_dirs() -> None:
    HTTP_TARGETS_DIR.mkdir(parents=True, exist_ok=True)
    FUNCTIONAL_PROBES_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    PROBE_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)


ensure_output_dir()
ensure_config_dirs()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(APP_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(APP_NAME)


def log_exception(context: str, exc: Exception) -> None:
    message = f"{context}: {exc}"
    logger.exception(message)
    with open(ERROR_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"[{now_local_iso()}] {message}\n")
        fh.write(traceback.format_exc())
        fh.write("\n")


def explain_oracle_exception(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()

    if "getaddrinfo failed" in lowered:
        return (
            "Falha ao resolver o host do Oracle. Revise ORACLE_DSN no formato "
            "host:1521/service_name. Erro original: "
            f"{message}"
        )

    if "dpy-3015" in lowered:
        return (
            "Senha Oracle exige thick mode (DPY-3015). Instale/configure o "
            "Oracle Instant Client ou redefina a senha do usuario. Erro original: "
            f"{message}"
        )

    return message


def initialize_oracle_client() -> None:
    global ORACLE_CLIENT_MODE
    global ORACLE_CLIENT_INIT_ERROR

    if not ENABLE_ORACLE or not oracledb.is_thin_mode():
        ORACLE_CLIENT_MODE = "thick" if not oracledb.is_thin_mode() else "thin"
        return

    if ORACLE_CLIENT_LIB_DIR is None:
        return

    try:
        oracledb.init_oracle_client(lib_dir=str(ORACLE_CLIENT_LIB_DIR))
        ORACLE_CLIENT_MODE = "thick"
    except Exception as exc:
        ORACLE_CLIENT_INIT_ERROR = str(exc)
        ORACLE_CLIENT_MODE = "thin"


def init_csv_file(path: Path, header: Sequence[str]) -> None:
    expected_header = ";".join(header)

    if path.exists():
        with open(path, "r", encoding="utf-8") as fh:
            current_header = fh.readline().strip("\r\n")
        if current_header == expected_header:
            return

        backup_name = f"{path.stem}_legacy_{datetime.now().strftime('%Y%m%d%H%M%S')}{path.suffix}"
        backup_path = path.with_name(backup_name)
        path.replace(backup_path)
        logger.warning("Arquivo %s tinha cabecalho antigo e foi movido para %s", path.name, backup_path.name)

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(list(header))


def append_csv_rows(path: Path, rows: Sequence[Sequence[Any]]) -> None:
    if not rows:
        return
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerows(rows)


def new_collection_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


def record_from_row(header: Sequence[str], row: Sequence[Any]) -> Dict[str, Any]:
    return {key: row[idx] if idx < len(row) else "" for idx, key in enumerate(header)}


def get_dataset_schema(schema_name: str) -> Dict[str, Any]:
    schema = lookup_schema_item(DATASET_SCHEMAS, schema_name)
    return schema if isinstance(schema, dict) else {}


def get_probe_schema(probe_name: str) -> Dict[str, Any]:
    schema = lookup_schema_item(PROBE_SCHEMAS, probe_name)
    return schema if isinstance(schema, dict) else {}


def decode_success_label(value: Any) -> str:
    return "Sucesso" if int(value or 0) == 1 else "Falha"


init_csv_file(HTTP_CSV, HTTP_HEADER)
init_csv_file(ORACLE_SUMMARY_CSV, ORACLE_SUMMARY_HEADER)
init_csv_file(ORACLE_PROBES_CSV, ORACLE_PROBES_HEADER)
init_csv_file(ORACLE_SUMMARY_METRICS_CSV, ORACLE_SUMMARY_METRICS_HEADER)
init_csv_file(ORACLE_PROBE_VALUES_CSV, ORACLE_PROBE_VALUES_HEADER)
init_csv_file(COLLECTOR_RUNS_CSV, COLLECTOR_RUNS_HEADER)


# ============================================================
# HTTP
# ============================================================

def build_requests_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=HTTP_RETRIES,
        connect=HTTP_RETRIES,
        read=HTTP_RETRIES,
        backoff_factor=HTTP_BACKOFF_SECONDS,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


HTTP_SESSION = build_requests_session()


def socket_probe(url: str, timeout_seconds: int, verify_ssl: bool) -> Dict[str, Any]:
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    scheme = parsed.scheme.lower()
    port = parsed.port or (443 if scheme == "https" else 80)

    result: Dict[str, Any] = {
        "host": host,
        "port": port,
        "remote_ip": "",
        "dns_ms": "",
        "tcp_ms": "",
        "tls_ms": "",
        "erro": "",
    }

    if not host:
        result["erro"] = "URL sem host válido"
        return result

    raw_sock = None
    wrapped_sock = None

    try:
        dns_start = time.perf_counter()
        addrinfos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        dns_end = time.perf_counter()
        result["dns_ms"] = round((dns_end - dns_start) * 1000, 2)

        family, socktype, proto, _, sockaddr = addrinfos[0]
        result["remote_ip"] = str(sockaddr[0])

        raw_sock = socket.socket(family, socktype, proto)
        raw_sock.settimeout(timeout_seconds)

        tcp_start = time.perf_counter()
        raw_sock.connect(sockaddr)
        tcp_end = time.perf_counter()
        result["tcp_ms"] = round((tcp_end - tcp_start) * 1000, 2)

        if scheme == "https":
            tls_start = time.perf_counter()
            context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
            wrapped_sock = context.wrap_socket(raw_sock, server_hostname=host)
            tls_end = time.perf_counter()
            result["tls_ms"] = round((tls_end - tls_start) * 1000, 2)

    except Exception as exc:
        result["erro"] = str(exc)
    finally:
        try:
            if wrapped_sock is not None:
                wrapped_sock.close()
        except Exception:
            pass
        try:
            if raw_sock is not None:
                raw_sock.close()
        except Exception:
            pass

    return result


def check_http_target(target: HttpTarget, collection_id: str) -> List[Any]:
    ts_local = now_local_iso()
    ts_utc = utc_now_iso()
    parsed = urlsplit(target.url)
    host = parsed.hostname or ""

    network_result = socket_probe(target.url, target.timeout_seconds, target.verify_ssl)
    http_ms: Any = ""
    status_http: Any = ""
    body_ok = ""
    ok = 0
    error = network_result.get("erro", "")

    try:
        request_headers = target.headers or {}
        start = time.perf_counter()
        response = HTTP_SESSION.request(
            method=target.method,
            url=target.url,
            timeout=target.timeout_seconds,
            verify=target.verify_ssl,
            headers=request_headers,
        )
        end = time.perf_counter()

        http_ms = round((end - start) * 1000, 2)
        status_http = response.status_code
        body_ok = 1

        if target.expected_text:
            body_ok = 1 if target.expected_text in response.text else 0

        status_ok = status_http in target.expected_statuses
        ok = 1 if status_ok and body_ok == 1 else 0

        if not status_ok:
            error = f"Status fora do esperado: {status_http}"
        elif body_ok != 1:
            error = "Texto esperado não encontrado na resposta"
        else:
            error = ""

    except Exception as exc:
        error = str(exc)

    return [
        collection_id,
        ts_local,
        ts_utc,
        target.name,
        target.source_name,
        target.source_file,
        target.url,
        target.method,
        host,
        network_result.get("remote_ip", ""),
        network_result.get("port", ""),
        network_result.get("dns_ms", ""),
        network_result.get("tcp_ms", ""),
        network_result.get("tls_ms", ""),
        http_ms,
        status_http,
        ",".join(str(x) for x in target.expected_statuses),
        target.expected_text,
        body_ok,
        ok,
        error,
    ]


def collect_http(collection_id: str) -> List[List[Any]]:
    if not ENABLE_HTTP:
        return []
    rows: List[List[Any]] = []
    for target in HTTP_TARGETS:
        rows.append(check_http_target(target, collection_id))
    return rows


# ============================================================
# ORACLE
# ============================================================

SQL_ORACLE_SUMMARY = """
WITH
sess AS (
    SELECT inst_id, sid, serial#, status, event, machine, program, username, last_call_et, blocking_session
    FROM gv$session
    WHERE type = 'USER'
),
tot AS (
    SELECT COUNT(*) total FROM sess
),
act AS (
    SELECT COUNT(*) active_qtd FROM sess WHERE status = 'ACTIVE'
),
inact AS (
    SELECT COUNT(*) inactive_qtd FROM sess WHERE status = 'INACTIVE'
),
sqlnet AS (
    SELECT COUNT(*) qtd FROM sess WHERE event = 'SQL*Net message from client'
),
resmgr AS (
    SELECT COUNT(*) qtd FROM sess WHERE event = 'resmgr:cpu quantum'
),
locks AS (
    SELECT COUNT(*) qtd FROM gv$lock WHERE block > 0
),
blocked AS (
    SELECT COUNT(*) qtd FROM sess WHERE blocking_session IS NOT NULL
),
long_running AS (
    SELECT COUNT(*) qtd
    FROM sess
    WHERE status = 'ACTIVE'
      AND NVL(last_call_et, 0) >= :long_running_seconds
),
jdbc_active AS (
    SELECT COUNT(*) qtd
    FROM gv$session
    WHERE type = 'USER'
      AND status = 'ACTIVE'
      AND program LIKE '%JDBC%'
),
top_machine AS (
    SELECT machine
    FROM (
        SELECT NVL(machine, '(null)') machine, COUNT(*) qtd
        FROM sess
        GROUP BY machine
        ORDER BY qtd DESC, machine
    )
    WHERE ROWNUM = 1
),
top_program AS (
    SELECT program
    FROM (
        SELECT NVL(program, '(null)') program, COUNT(*) qtd
        FROM sess
        GROUP BY program
        ORDER BY qtd DESC, program
    )
    WHERE ROWNUM = 1
),
top_username AS (
    SELECT username
    FROM (
        SELECT NVL(username, '(null)') username, COUNT(*) qtd
        FROM sess
        GROUP BY username
        ORDER BY qtd DESC, username
    )
    WHERE ROWNUM = 1
)
SELECT
    i.instance_name,
    i.host_name,
    d.name,
    t.total,
    a.active_qtd,
    ia.inactive_qtd,
    sn.qtd,
    rm.qtd,
    l.qtd,
    b.qtd,
    lr.qtd,
    ja.qtd,
    tm.machine,
    tp.program,
    tu.username
FROM v$instance i
CROSS JOIN v$database d
CROSS JOIN tot t
CROSS JOIN act a
CROSS JOIN inact ia
CROSS JOIN sqlnet sn
CROSS JOIN resmgr rm
CROSS JOIN locks l
CROSS JOIN blocked b
CROSS JOIN long_running lr
CROSS JOIN jdbc_active ja
CROSS JOIN top_machine tm
CROSS JOIN top_program tp
CROSS JOIN top_username tu
"""


def connect_oracle() -> oracledb.Connection:
    if not ORACLE_USER or not ORACLE_PASSWORD or not ORACLE_DSN:
        raise ValueError("ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN precisam estar preenchidos no .env")

    if ORACLE_FETCH_LOBS:
        oracledb.defaults.fetch_lobs = True

    initialize_oracle_client()

    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
    )


def collect_oracle_summary(collection_id: str) -> List[Any]:
    ts_local = now_local_iso()
    ts_utc = utc_now_iso()
    empty_row: List[Any] = [
        collection_id,
        ts_local,
        ts_utc,
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        0,
        "",
    ]

    if not ENABLE_ORACLE:
        return empty_row

    conn = None
    cur = None
    try:
        conn = connect_oracle()
        cur = conn.cursor()
        cur.execute(SQL_ORACLE_SUMMARY, long_running_seconds=ORACLE_LONG_RUNNING_SECONDS)
        row = cur.fetchone()
        if row is None:
            empty_row[-1] = "Consulta Oracle retornou vazio"
            return empty_row

        return [
            collection_id,
            ts_local,
            ts_utc,
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],
            row[10],
            row[11],
            row[12],
            row[13],
            row[14],
            1,
            "",
        ]
    except Exception as exc:
        empty_row[-1] = explain_oracle_exception(exc)
        return empty_row
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


def row_to_json(cur: oracledb.Cursor, row: Optional[Tuple[Any, ...]]) -> str:
    if row is None:
        return ""
    columns = [d[0] for d in cur.description] if cur.description else []
    data: Dict[str, Any] = {}
    for idx, column in enumerate(columns):
        value = row[idx]
        if isinstance(value, datetime):
            data[column] = value.isoformat(sep=" ")
        else:
            data[column] = value
    return json.dumps(data, ensure_ascii=False)


def collect_oracle_probes(collection_id: str) -> List[List[Any]]:
    if not ENABLE_ORACLE or not ENABLE_FUNCTIONAL_PROBES or not ORACLE_PROBES:
        return []

    rows: List[List[Any]] = []
    conn = None
    cur = None
    try:
        conn = connect_oracle()
        cur = conn.cursor()

        for probe in ORACLE_PROBES:
            ts_local = now_local_iso()
            ts_utc = utc_now_iso()
            probe_schema = get_probe_schema(probe.name)
            probe_display_name = schema_text(probe_schema.get("probe_display_name"), probe.name)
            probe_description = schema_text(probe_schema.get("probe_description"))
            elapsed_ms: Any = ""
            row_json = ""
            ok = 0
            error = ""

            try:
                start = time.perf_counter()
                cur.execute(probe.sql)
                row = cur.fetchone()
                end = time.perf_counter()
                elapsed_ms = round((end - start) * 1000, 2)
                row_json = row_to_json(cur, row)
                ok = 1
            except Exception as exc:
                error = explain_oracle_exception(exc)

            rows.append([
                collection_id,
                ts_local,
                ts_utc,
                probe.name,
                probe.source_name,
                probe.source_file,
                probe_display_name,
                probe_description,
                elapsed_ms,
                row_json,
                ok,
                error,
            ])
    except Exception as exc:
        ts_local = now_local_iso()
        ts_utc = utc_now_iso()
        rows.append([
            collection_id,
            ts_local,
            ts_utc,
            "__connection__",
            "",
            "",
            "Falha de conexao Oracle",
            "Nao foi possivel abrir a conexao Oracle para executar as probes.",
            "",
            "",
            0,
            explain_oracle_exception(exc),
        ])
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    return rows


def build_oracle_summary_metric_rows(summary_row: Sequence[Any]) -> List[List[Any]]:
    record = record_from_row(ORACLE_SUMMARY_HEADER, summary_row)
    dataset_schema = get_dataset_schema("fact_oracle_summary_metrics")
    metric_values = dataset_schema.get("metric_values", {})
    metric_names = [
        "session_total_count",
        "session_active_count",
        "session_inactive_count",
        "wait_sqlnet_message_from_client_count",
        "wait_resmgr_cpu_quantum_count",
        "lock_count",
        "blocked_session_count",
        "long_running_active_session_count",
        "active_jdbc_session_count",
    ]

    rows: List[List[Any]] = []
    for metric_name in metric_names:
        metric_schema = lookup_schema_item(metric_values, metric_name)
        metric_schema = metric_schema if isinstance(metric_schema, dict) else {}
        rows.append([
            record["collection_id"],
            record["collected_at_local"],
            record["collected_at_utc"],
            record["oracle_instance_name"],
            record["oracle_host_name"],
            record["oracle_database_name"],
            metric_name,
            schema_text(metric_schema.get("display_name"), metric_name),
            schema_text(metric_schema.get("group_name")),
            schema_text(metric_schema.get("description")),
            record.get(metric_name, ""),
            record["is_success"],
            record["error_message"],
        ])
    return rows


def build_oracle_probe_value_rows(probe_rows: Sequence[Sequence[Any]]) -> List[List[Any]]:
    rows: List[List[Any]] = []

    for probe_row in probe_rows:
        record = record_from_row(ORACLE_PROBES_HEADER, probe_row)
        row_json = str(record.get("probe_result_json", "") or "").strip()
        probe_schema = get_probe_schema(record.get("oracle_probe_name", ""))
        probe_display_name = schema_text(record.get("oracle_probe_display_name"), record.get("oracle_probe_name", ""))
        probe_description = schema_text(record.get("oracle_probe_description"))
        column_schemas = probe_schema.get("columns", {}) if isinstance(probe_schema, dict) else {}

        if row_json:
            try:
                parsed = json.loads(row_json)
            except json.JSONDecodeError:
                parsed = {"__raw_json__": row_json}

            if isinstance(parsed, dict) and parsed:
                for column_name, column_value in parsed.items():
                    column_schema = lookup_schema_item(column_schemas, column_name)
                    column_schema = column_schema if isinstance(column_schema, dict) else {}
                    value_map = column_schema.get("value_map", {}) if isinstance(column_schema, dict) else {}
                    value_display_name = schema_text(lookup_schema_item(value_map, column_value), schema_text(column_value))
                    rows.append([
                        record["collection_id"],
                        record["collected_at_local"],
                        record["collected_at_utc"],
                        record["oracle_probe_name"],
                        record["oracle_probe_group_name"],
                        record["oracle_probe_file_path"],
                        probe_display_name,
                        probe_description,
                        column_name,
                        schema_text(column_schema.get("display_name"), column_name),
                        schema_text(column_schema.get("description")),
                        column_value,
                        value_display_name,
                        record["is_success"],
                        record["error_message"],
                    ])
                continue

        rows.append([
            record["collection_id"],
            record["collected_at_local"],
            record["collected_at_utc"],
            record["oracle_probe_name"],
            record["oracle_probe_group_name"],
            record["oracle_probe_file_path"],
            probe_display_name,
            probe_description,
            "",
            "",
            "",
            "",
            "",
            record["is_success"],
            record["error_message"],
        ])

    return rows


def build_run_row(
    collection_id: str,
    ts_local: str,
    ts_utc: str,
    http_rows: Sequence[Sequence[Any]],
    oracle_summary_row: Sequence[Any],
    oracle_probe_rows: Sequence[Sequence[Any]],
    duration_ms: float,
) -> List[Any]:
    http_success_count = sum(1 for row in http_rows if record_from_row(HTTP_HEADER, row).get("is_success") == 1)
    http_error_count = len(http_rows) - http_success_count

    summary_record = record_from_row(ORACLE_SUMMARY_HEADER, oracle_summary_row) if oracle_summary_row else {}
    oracle_summary_success_flag = int(summary_record.get("is_success", 0) or 0)

    oracle_probe_success_count = sum(
        1 for row in oracle_probe_rows if record_from_row(ORACLE_PROBES_HEADER, row).get("is_success") == 1
    )
    oracle_probe_error_count = len(oracle_probe_rows) - oracle_probe_success_count

    collection_success_flag = 1
    if http_rows and http_error_count > 0:
        collection_success_flag = 0
    if oracle_summary_row and oracle_summary_success_flag != 1:
        collection_success_flag = 0
    if oracle_probe_rows and oracle_probe_error_count > 0:
        collection_success_flag = 0

    return [
        collection_id,
        ts_local,
        ts_utc,
        len(http_rows),
        http_success_count,
        http_error_count,
        oracle_summary_success_flag,
        len(oracle_probe_rows),
        oracle_probe_success_count,
        oracle_probe_error_count,
        collection_success_flag,
        decode_success_label(collection_success_flag),
        round(duration_ms, 2),
    ]


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def handle_stop_signal(signum: int, frame: Any) -> None:
    del frame
    global STOP_REQUESTED
    STOP_REQUESTED = True
    logger.warning("Sinal recebido (%s). Encerrando o coletor com segurança...", signum)


signal.signal(signal.SIGINT, handle_stop_signal)
signal.signal(signal.SIGTERM, handle_stop_signal)


def validate_startup() -> None:
    initialize_oracle_client()

    if ENABLE_HTTP and not HTTP_TARGETS:
        logger.warning(
            "ENABLE_HTTP=true, mas não há alvos HTTP nem em %s nem em HTTP_TARGETS_JSON.",
            HTTP_TARGETS_DIR,
        )

    if ENABLE_ORACLE and (not ORACLE_USER or not ORACLE_PASSWORD or not ORACLE_DSN):
        logger.warning("ENABLE_ORACLE=true, mas as variáveis ORACLE_USER/ORACLE_PASSWORD/ORACLE_DSN não estão completas.")

    if ENABLE_ORACLE and ENABLE_FUNCTIONAL_PROBES and not ORACLE_PROBES:
        logger.warning(
            "ENABLE_FUNCTIONAL_PROBES=true, mas não há arquivos .sql em %s nem FUNCTIONAL_PROBES_JSON configurado.",
            FUNCTIONAL_PROBES_DIR,
        )

    if ENABLE_ORACLE and ORACLE_CLIENT_MODE == "thick" and ORACLE_CLIENT_LIB_DIR is not None:
        logger.info("Oracle client inicializado em thick mode: %s", ORACLE_CLIENT_LIB_DIR)
    elif ENABLE_ORACLE and ORACLE_CLIENT_LIB_DIR is not None and ORACLE_CLIENT_INIT_ERROR:
        logger.warning("Oracle client encontrado, mas o thick mode falhou: %s", ORACLE_CLIENT_INIT_ERROR)

    placeholder_probes = [
        probe.name
        for probe in ORACLE_PROBES
        if "sua_view_" in probe.sql.lower() or "sua_tabela_" in probe.sql.lower()
    ]
    if placeholder_probes:
        logger.warning(
            "As probes ainda parecem placeholders e devem ser trocadas por SQL real: %s",
            ", ".join(placeholder_probes),
        )

    logger.info("Saída em: %s", OUTPUT_DIR.resolve())
    logger.info(
        "Data schema: %s dataset(s) em %s | %s probe schema(s) em %s",
        len(DATASET_SCHEMAS),
        DATASET_SCHEMA_DIR,
        len(PROBE_SCHEMAS),
        PROBE_SCHEMA_DIR,
    )
    logger.info(
        "HTTP por arquivos: %s item(ns) em %s | HTTP por .env: %s",
        len(HTTP_TARGETS_FILE_RAW),
        HTTP_TARGETS_DIR,
        len(HTTP_TARGETS_ENV_RAW),
    )
    logger.info(
        "SQL por arquivos: %s item(ns) em %s | SQL por .env: %s",
        len(FUNCTIONAL_PROBES_FILE_RAW),
        FUNCTIONAL_PROBES_DIR,
        len(FUNCTIONAL_PROBES_ENV_RAW),
    )
    logger.info("Intervalo entre coletas: %ss", INTERVAL_SECONDS)
    logger.info("HTTP habilitado: %s | alvos: %s", ENABLE_HTTP, len(HTTP_TARGETS))
    logger.info("Oracle habilitado: %s | probes funcionais: %s", ENABLE_ORACLE, len(ORACLE_PROBES))


def main() -> None:
    validate_startup()
    logger.info("Coletor iniciado.")

    while not STOP_REQUESTED:
        cycle_ts_local = now_local_iso()
        cycle_ts_utc = utc_now_iso()
        collection_id = new_collection_id()
        cycle_start = time.perf_counter()
        try:
            http_rows = collect_http(collection_id)
            append_csv_rows(HTTP_CSV, http_rows)

            oracle_summary_row = collect_oracle_summary(collection_id)
            append_csv_rows(ORACLE_SUMMARY_CSV, [oracle_summary_row])
            append_csv_rows(ORACLE_SUMMARY_METRICS_CSV, build_oracle_summary_metric_rows(oracle_summary_row))

            oracle_probe_rows = collect_oracle_probes(collection_id)
            append_csv_rows(ORACLE_PROBES_CSV, oracle_probe_rows)
            append_csv_rows(ORACLE_PROBE_VALUES_CSV, build_oracle_probe_value_rows(oracle_probe_rows))

            duration_ms = (time.perf_counter() - cycle_start) * 1000
            append_csv_rows(
                COLLECTOR_RUNS_CSV,
                [build_run_row(collection_id, cycle_ts_local, cycle_ts_utc, http_rows, oracle_summary_row, oracle_probe_rows, duration_ms)],
            )
        except Exception as exc:
            log_exception("Erro geral no ciclo", exc)

        elapsed = time.perf_counter() - cycle_start
        sleep_for = max(1, INTERVAL_SECONDS - int(elapsed))

        if not STOP_REQUESTED:
            time.sleep(sleep_for)

    logger.info("Coletor finalizado.")


if __name__ == "__main__":
    main()
