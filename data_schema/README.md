# Data Schema

Tudo que for regra de entendimento do dado fica aqui.

A pasta `saida/` e descartavel.

## Estrutura

```text
data_schema/
  datasets/
  probes/
```

## datasets

Schemas de datasets fixos do coletor.

Exemplo:

- `fact_oracle_summary_metrics.json`

## probes

Schemas das consultas SQL.

O nome do arquivo deve acompanhar o nome da probe.

Exemplos:

- `oracle_probes/atendimentos.sql`
- `data_schema/probes/atendimentos.json`

- `oracle_probes/heartbeat_sql.sql`
- `data_schema/probes/heartbeat_sql.json`

## O que um schema de probe pode ter

```json
{
  "probe_display_name": "Nome amigavel da probe",
  "probe_description": "Descricao curta para leigos.",
  "columns": {
    "NOME_DA_COLUNA": {
      "display_name": "Nome amigavel da coluna",
      "description": "O que essa coluna significa.",
      "value_map": {
        "0": "Nao",
        "1": "Sim"
      }
    }
  }
}
```

## Regra principal

Nenhuma logica de schema fica em `saida/`.
