# Coletor SaaS

Guia simples para rodar o coletor e aproveitar os dados em BI.

Ao clonar o projeto, copie `.env.example` para `.env` e ajuste a configuração local. O arquivo `.env` e a pasta `saida/`, com dados gerados pelo monitoramento, são ignorados pelo Git.

## 1. O que voce precisa editar

### Arquivo `.env`

Preencha somente:

- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_DSN`

Deixe assim:

```env
OUTPUT_DIR=./saida
HTTP_TARGETS_DIR=./http_targets
FUNCTIONAL_PROBES_DIR=./oracle_probes
DATA_SCHEMA_DIR=./data_schema
```

### Arquivo `http_targets/lista_sites.url`

Coloque os links que quer monitorar no mesmo arquivo, separados por virgula.

Exemplo:

```text
http://2324prd.cloudmv.com.br, https://meusistema/login, https://meusistema/api/status
```

Se quiser dar nome manual a um link, pode usar:

```text
login|https://meusistema/login, api_status|https://meusistema/api/status
```

### Pasta `oracle_probes/`

Mantenha um arquivo `.sql` por probe.

Exemplo:

Arquivo `oracle_probes/heartbeat_sql.sql`

```sql
select systimestamp as data_banco from dual
```

Arquivo `oracle_probes/fila_pendente.sql`

```sql
select count(*) as qtd
from sua_view_fila
where status = 'PENDENTE'
```

### Pasta `data_schema/`

Toda a logica de interpretacao do dado fica aqui.

Use:

- `data_schema/datasets/` para datasets fixos
- `data_schema/probes/` para as saidas das queries

Exemplo:

- `oracle_probes/atendimentos.sql`
- `data_schema/probes/atendimentos.json`

Importante:

- `saida/` e descartavel
- nenhuma logica deve ficar em `saida/`

## 2. Como instalar

```powershell
pip install -r requirements.txt
```

## 3. Como rodar

```powershell
python .\coletor_saas.py
```

Ou use os atalhos:

```bat
.\iniciar_coletor.bat
.\parar_coletor.bat
.\agendar_coletor.bat
```

O agendamento criado por `agendar_coletor.bat` inicia o coletor no logon do usuario atual.

## 4. Onde ficam os resultados

Tudo sai em `saida/`.

Arquivos principais:

- `fact_http_health_checks.csv`
- `fact_oracle_summary.csv`
- `fact_oracle_probe_results.csv`
- `fact_collection_runs.csv`
- `collector.log`
- `errors.log`

Arquivos extras para BI:

- `fact_oracle_summary_metrics.csv`
- `fact_oracle_probe_values.csv`

Esses arquivos ja saem enriquecidos pelo `data_schema` quando houver schema configurado.

## 5. O que usar no BI

### Para disponibilidade HTTP

Use `fact_http_health_checks.csv`.

Colunas uteis:

- `collection_id`
- `http_target_name`
- `http_target_file_path`
- `request_url`
- `dns_duration_ms`
- `tcp_connect_duration_ms`
- `http_duration_ms`
- `http_status_code`
- `is_success`
- `error_message`

### Para saude geral de cada coleta

Use `fact_collection_runs.csv`.

Colunas uteis:

- `collection_id`
- `http_success_count`
- `http_error_count`
- `oracle_summary_success_flag`
- `oracle_probe_success_count`
- `oracle_probe_error_count`
- `collection_success_flag`
- `collection_health_label`
- `collection_duration_ms`

### Para resumo Oracle

Se quiser tabela pronta, use `fact_oracle_summary.csv`.

Se quiser graficos por metrica, use `fact_oracle_summary_metrics.csv`.

Colunas amigaveis importantes:

- `metric_display_name`
- `metric_group_name`
- `metric_description`

### Para probes SQL

Se quiser o retorno bruto de cada probe, use `fact_oracle_probe_results.csv`.

Se quiser uma tabela mais facil para BI, use `fact_oracle_probe_values.csv`.

Quando existir schema em `data_schema/probes/`, a saida ja traz:

- nome amigavel da probe
- descricao da probe
- nome amigavel da coluna da query
- descricao da coluna
- decode amigavel do valor, quando configurado

Colunas amigaveis importantes:

- `oracle_probe_display_name`
- `oracle_probe_description`
- `result_column_display_name`
- `result_column_description`
- `result_value_display_name`

## 6. Como os dados se ligam

Use `collection_id` para juntar:

- `fact_http_health_checks.csv`
- `fact_oracle_summary.csv`
- `fact_oracle_probe_results.csv`
- `fact_oracle_summary_metrics.csv`
- `fact_oracle_probe_values.csv`
- `fact_collection_runs.csv`

## 7. Regras praticas

- um unico arquivo para links HTTP
- um arquivo `.sql` por probe
- links separados por virgula
- probes devem retornar 1 linha
- arquivos e pastas que comecam com `_` sao ignorados pelo coletor

## 8. Fluxo mais simples possivel

1. Preencha Oracle no `.env`
2. Edite `http_targets/lista_sites.url`
3. Coloque os `.sql` em `oracle_probes/`
4. Crie ou ajuste os schemas em `data_schema/`
5. Rode `python .\coletor_saas.py`
6. Monte o painel usando `collection_id`
