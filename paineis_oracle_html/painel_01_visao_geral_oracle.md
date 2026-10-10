# Painel 1 — Visão geral Oracle

## Finalidade
Painel para visão rápida da operação Oracle por coleta.

## Fontes
- `fact_oracle_summary.csv`
- `fact_oracle_summary_metrics.csv`
- `fact_collection_runs.csv`

## Indicadores principais
- Total de sessões
- Sessões ativas
- Sessões inativas
- Sessões bloqueadas
- Sessões ativas JDBC
- Sessões ativas de longa duração
- Coleta com sucesso ou falha
- Tempo da coleta

## Cortes recomendados
- Data e hora da coleta
- Instância Oracle
- Host Oracle
- Banco Oracle

## Visuais recomendados
- Cartões de indicadores
- Linha do tempo por coleta
- Barra por tipo de métrica
- Tabela com últimas coletas

## Regras em linguagem natural
- Mostrar como alerta quando houver sessão bloqueada maior que zero.
- Mostrar como alerta quando houver sessão ativa de longa duração maior que zero.
- Mostrar como alerta quando a coleta falhar.
- Exibir o nome mais frequente de máquina, programa e usuário para facilitar identificação rápida de concentração operacional.