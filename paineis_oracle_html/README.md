# Pacote consolidado dos painéis Oracle e BI

Este pacote consolida a estrutura dos painéis para considerar o novo arquivo `fact_oracle_sessions.csv` e incluir uma camada de BI mais executiva.

## Painel 1 — Visão geral Oracle
Base principal:
- `fact_oracle_summary.csv`
- `fact_oracle_summary_metrics.csv`
- `fact_collection_runs.csv`

Objetivo:
- mostrar saúde geral da coleta
- mostrar volume de sessões
- mostrar sessões ativas, inativas, bloqueadas e JDBC
- mostrar tendência por coleta

## Painel 2 — Análise operacional de sessões
Base principal:
- `fact_oracle_sessions.csv`
- opcionalmente `fact_oracle_probe_results.csv`
- opcionalmente `fact_oracle_probe_values.csv`

Objetivo:
- identificar sessões relevantes e problemáticas em nível de linha
- localizar origem por usuário, máquina, programa, módulo e ação
- destacar bloqueios, atividade, JDBC e tempo desde a última chamada

## Painel 3 — BI gerencial de operação Oracle
Base principal:
- `fact_oracle_summary.csv`
- `fact_oracle_summary_metrics.csv`
- `fact_collection_runs.csv`
- `fact_oracle_sessions.csv`

Objetivo:
- entregar visão executiva com linguagem natural
- mostrar risco operacional por coleta
- apontar onde houve concentração de sessões, atividade, bloqueio e uso JDBC
- permitir sair do indicador executivo para a sessão detalhada

## Observação
Como os arquivos originais dos painéis não vieram anexados nesta conversa, a consolidação abaixo foi feita de forma compatível com o coletor ajustado e com o novo CSV de sessões.
