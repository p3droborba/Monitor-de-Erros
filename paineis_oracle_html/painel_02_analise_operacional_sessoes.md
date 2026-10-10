# Painel 2 — Análise operacional de sessões

## Finalidade
Painel analítico para investigar sessões Oracle em nível de linha.

## Fonte principal
- `fact_oracle_sessions.csv`

## Colunas mais importantes para o usuário
- Data e hora local da coleta
- Instância Oracle
- Host Oracle
- Banco Oracle
- Id da instância
- Id da sessão
- Número serial da sessão
- Usuário Oracle
- Situação da sessão
- Evento de espera
- Classe de espera
- Máquina de origem
- Programa de origem
- Módulo
- Ação
- Usuário do sistema operacional
- Id do SQL
- Sessão bloqueadora
- Segundos desde a última chamada
- Data e hora de logon
- Sessão ativa
- Sessão bloqueada
- Sessão bloqueando outra
- Sessão JDBC

## Visuais recomendados
- Tabela analítica detalhada
- Segmentadores por usuário, status, máquina, programa, módulo e JDBC
- Ranking de máquinas
- Ranking de programas
- Ranking de usuários
- Quantidade de sessões bloqueadas por coleta
- Quantidade de sessões ativas por coleta

## Regras em linguagem natural
- Tratar como sessão ativa quando o campo "Sessão ativa" for igual a 1.
- Tratar como sessão bloqueada quando o campo "Sessão bloqueada" for igual a 1.
- Tratar como sessão bloqueando outra quando o campo "Sessão bloqueando outra" for igual a 1.
- Tratar como sessão JDBC quando o campo "Sessão JDBC" for igual a 1.
- Dar prioridade visual para sessões ativas, bloqueadas, bloqueando outra ou com tempo alto desde a última chamada.