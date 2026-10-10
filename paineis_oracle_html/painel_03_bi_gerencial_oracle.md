# Painel 3 — BI gerencial de operação Oracle

## Finalidade
Painel para acompanhamento gerencial da operação Oracle, com leitura simples e drill-through para análise operacional.

## Fontes
- `fact_oracle_summary.csv`
- `fact_oracle_summary_metrics.csv`
- `fact_collection_runs.csv`
- `fact_oracle_sessions.csv`

## Perguntas de negócio que o painel responde
- O ambiente Oracle está estável nas últimas coletas?
- Houve aumento de sessões ativas, bloqueadas ou de longa duração?
- Existe concentração de uso por máquina, programa ou usuário?
- A operação está com indício de fila, bloqueio ou uso excessivo de JDBC?
- Em qual coleta ocorreu o desvio e quais sessões explicam esse cenário?

## Indicadores principais em linguagem natural
- Total de sessões na coleta
- Total de sessões ativas
- Total de sessões inativas
- Total de sessões bloqueadas
- Total de sessões bloqueando outras
- Total de sessões JDBC
- Total de sessões ativas de longa duração
- Coleta concluída com sucesso
- Tempo total da coleta

## Visuais recomendados
- Cartões com os principais indicadores
- Linha do tempo por coleta
- Barras por usuário Oracle
- Barras por máquina de origem
- Barras por programa de origem
- Tabela resumo das últimas coletas
- Botão ou ação de detalhamento para abrir a visão das sessões

## Regras em linguagem natural
- Mostrar alerta quando houver qualquer sessão bloqueada.
- Mostrar alerta quando houver sessão bloqueando outra sessão.
- Mostrar alerta quando houver crescimento de sessões ativas em relação às coletas anteriores.
- Mostrar alerta quando houver sessão ativa de longa duração.
- Mostrar alerta quando a coleta falhar.
- Destacar os principais usuários, máquinas e programas quando houver concentração operacional.

## Navegação recomendada
- Visão executiva
- Tendência por coleta
- Principais origens de uso
- Drill-through para sessão detalhada
