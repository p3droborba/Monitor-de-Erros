# Prompt rígido para Codex CLI — execução no workspace e saída em um único arquivo

Use este arquivo como prompt único para o Codex CLI.

## Objetivo

Fazer o Codex agir como desenvolvedor executor dentro de um workspace já aberto, implementando a solução diretamente no repositório, validando a execução local e só então retornando um resumo final.

## Prompt completo

```text
Você está atuando como o desenvolvedor principal dentro de um workspace já aberto, com acesso aos arquivos do repositório e capacidade de criar, editar e validar código localmente.

Sua função é executar o trabalho diretamente no workspace. Não descreva apenas o que faria. Implemente, valide e finalize.

Objetivo:
Implementar, no próprio workspace, uma solução Python 3.11+ para monitoramento de disponibilidade, performance e sinais operacionais de um SaaS/ERP com coleta HTTP e Oracle, seguindo rigorosamente o SDD abaixo.

Postura obrigatória:
- aja como executor técnico principal;
- trate este pedido como trabalho real de engenharia;
- tome iniciativa;
- faça primeiro, explique depois;
- prefira correção prática e código funcional;
- não responda com planejamento genérico;
- não interrompa para pedir confirmação em decisões pequenas;
- não devolva só arquitetura, passos, ideias ou scaffold;
- não deixe a implementação pela metade.

Restrições obrigatórias:
1. Trabalhe sobre o workspace atual.
2. Se o workspace estiver vazio, crie a estrutura completa.
3. Use o SDD como contrato principal.
4. Não use pseudocódigo.
5. Não deixe TODO, pass, NotImplementedError ou placeholders em partes centrais.
6. Não omita arquivos importantes.
7. Não simplifique requisitos centrais.
8. Não coloque credenciais hardcoded.
9. Não invente integrações fora do escopo.
10. Se houver lacuna pequena, faça a inferência mínima, registre em “Assunções adotadas” e siga.
11. Se um comando de validação falhar, corrija o problema quando estiver no escopo e rode novamente.
12. Só encerre depois de entregar a primeira versão completa e validada no que for possível no ambiente.

O que eu não quero:
- plano genérico;
- documentação excessiva;
- resposta abstrata;
- scaffold vazio;
- implementação parcial;
- “posso continuar depois”;
- “os demais arquivos seguem o mesmo padrão”;
- pedido de confirmação para detalhes menores.

O que eu quero:
- implementação real no repositório;
- arquivos reais e consistentes entre si;
- projeto utilizável;
- configuração externa;
- persistência funcional;
- tratamento de erro;
- execução contínua;
- documentação operacional suficiente;
- validação local do que foi implementado.

Fluxo de trabalho obrigatório:
1. Inspecione a árvore atual do workspace.
2. Identifique o que já existe e o que precisa ser criado ou alterado.
3. Defina a estrutura final coerente com o SDD.
4. Crie ou ajuste os arquivos necessários.
5. Garanta consistência de imports, caminhos, nomes de módulos e configuração.
6. Prepare arquivos de configuração de exemplo.
7. Prepare testes mínimos úteis.
8. Rode validações locais.
9. Corrija erros óbvios encontrados.
10. Só então entregue o resumo final.

Validações obrigatórias que você deve tentar executar:
- inspeção da árvore de arquivos;
- verificação de sintaxe Python;
- verificação de imports e empacotamento;
- teste básico de inicialização da aplicação;
- execução de testes automatizados, se disponíveis;
- confirmação de que Oracle pode ficar desabilitado via configuração;
- confirmação de que diretórios necessários são criados automaticamente;
- confirmação de que CSV e SQLite estão conectados ao fluxo principal.

Comandos de verificação esperados:
- listar a árvore do projeto;
- rodar verificação de sintaxe/bytecode dos arquivos Python;
- rodar testes automatizados;
- executar a aplicação em modo de ciclo único para smoke test.

Se algum comando exato não for viável no ambiente, adapte para um equivalente prático, mas preserve a intenção da validação.

Critério de qualidade:
- Python 3.11+;
- type hints;
- código modular;
- funções pequenas;
- separação por camadas;
- logging estruturado;
- tratamento de exceções;
- YAML + variáveis de ambiente;
- CSV + SQLite;
- queries Oracle isoladas;
- regras separadas da coleta;
- scheduler interno simples;
- desligamento controlado;
- testes mínimos úteis;
- README claro;
- operação previsível em Windows e Linux.

Entregáveis obrigatórios no repositório:
- app/main.py
- app/config.py
- app/scheduler.py
- app/models/*
- app/collectors/*
- app/storage/*
- app/rules/*
- app/alerts/*
- app/reporting/*
- app/utils/*
- config/settings.yaml
- config/.env.example
- requirements.txt
- README.md
- tests/*

Requisitos mínimos que devem estar realmente implementados:
- monitoramento HTTP/HTTPS de múltiplos endpoints;
- medição de latência;
- timeout e falha de conexão;
- captura de status code;
- validação opcional de conteúdo esperado;
- coleta Oracle leve e resumida;
- sessões total, ativas e inativas;
- waits configuráveis;
- locks bloqueantes;
- concentração por machine, program e username;
- engine de regras com severidade normal, atenção e crítico;
- alertas em arquivo;
- persistência em CSV;
- persistência em SQLite;
- relatório resumido por período;
- execução contínua por agendamento interno;
- configuração externa sem editar código.

Exigência adicional de executabilidade:
Implemente uma forma simples e previsível de smoke test local. De preferência:
- suporte a execução principal normal;
- suporte a execução em ciclo único para validação rápida, por exemplo com um parâmetro como `--once` ou equivalente;
- suporte a geração de relatório por comando ou rotina clara.

Se optar por nomes de parâmetros diferentes, documente claramente no README e use esses comandos nas validações finais.

Exigência adicional de robustez:
- falha de uma coleta não derruba o processo inteiro;
- Oracle desabilitado não quebra a aplicação;
- ausência de credenciais Oracle deve ser tratada com mensagem clara quando Oracle estiver habilitado;
- diretórios de saída devem ser criados automaticamente;
- escrita em CSV e SQLite deve ser tolerante a erros com logging adequado;
- scheduler deve respeitar interrupção controlada.

Bibliotecas e implementação:
- use Python 3.11+;
- pode usar `requests`, `oracledb`, `pydantic`, `pyyaml`, `sqlite3`, `pandas`, `tenacity` e padrão da biblioteca nativa;
- mantenha dependências enxutas;
- não adicione complexidade desnecessária;
- se uma dependência opcional não estiver disponível no ambiente, deixe o código preparado e documente a limitação.

Formato obrigatório da resposta final:
1. Assunções adotadas.
2. O que foi encontrado no workspace antes das alterações.
3. Arquivos criados.
4. Arquivos alterados.
5. Validações executadas.
6. Resultado das validações.
7. Pendências ou limitações explícitas.
8. Resumo final do que ficou pronto.

Regra final de comportamento:
Execute a implementação no repositório primeiro. Responda somente depois de concluir a primeira versão funcional e validar o que for possível no ambiente.

Agora implemente com base no SDD abaixo.

# SDD — Solução Profissional de Monitoramento de Disponibilidade, Performance e Sessões para SaaS/ERP MV

## 1. Visão geral

### 1.1 Objetivo

Desenvolver uma solução em Python para monitoramento contínuo de um ambiente SaaS/ERP, com foco em:

- disponibilidade percebida pelo usuário;
- latência de acesso;
- saúde de endpoints críticos;
- sinais de degradação de aplicação;
- métricas resumidas do Oracle;
- sessões ativas/inativas;
- waits relevantes;
- contenção de CPU;
- locks;
- geração de evidências históricas para análise técnica.

A solução deve ajudar a responder, com base em dados, se a lentidão ou indisponibilidade percebida está mais relacionada a:

- aplicação;
- rede;
- balanceamento/proxy;
- banco Oracle;
- concorrência;
- saturação de recurso;
- ou comportamento de sessão/conexão.

### 1.2 Contexto do problema

O ambiente apresenta relatos recorrentes de lentidão e/ou indisponibilidade operacional, porém os relatórios do fornecedor mostram principalmente disponibilidade de infraestrutura. Há necessidade de uma camada própria de observação, independente, que registre evidências técnicas correlacionáveis com o horário dos incidentes relatados pela operação.

### 1.3 Resultado esperado

A solução deve coletar, armazenar e organizar dados suficientes para:

- identificar padrões por horário;
- detectar picos e degradações;
- correlacionar reclamações operacionais com métricas técnicas;
- fornecer insumo para investigação de gargalos;
- apoiar discussão com TI interna e fornecedor.

## 2. Escopo

### 2.1 Escopo funcional

A solução deverá:

- monitorar URLs configuráveis do sistema;
- medir tempo de resposta HTTP/HTTPS;
- registrar falhas de conexão, timeout e códigos de resposta;
- opcionalmente validar conteúdo esperado da resposta;
- consultar métricas resumidas do Oracle;
- registrar contagem de sessões por status;
- registrar waits relevantes;
- registrar locks;
- registrar concentração por máquina, programa e usuário;
- gerar logs estruturados;
- persistir dados em arquivos CSV e opcionalmente SQLite;
- gerar alertas simples por limiar;
- gerar relatórios resumidos por período;
- operar em modo contínuo.

### 2.2 Fora do escopo inicial

Não faz parte da primeira versão:

- interface web complexa;
- dashboard em tempo real sofisticado;
- integração com Prometheus/Grafana;
- automação de correção;
- coleta profunda de AWR/ASH;
- alteração em banco Oracle;
- coleta invasiva em servidor do fornecedor;
- captura de tráfego via packet inspection.

## 3. Requisitos funcionais

### RF-01 — Monitoramento HTTP/HTTPS

A solução deve consultar, em intervalo configurável, uma ou mais URLs do sistema.

Deve registrar:
- timestamp;
- URL;
- status code;
- latência total;
- sucesso/falha;
- mensagem de erro;
- tempo de conexão;
- tempo até primeiro byte, se possível.

### RF-02 — Verificação de conteúdo

A solução deve permitir validar se a resposta contém conteúdo esperado, como:
- palavra-chave;
- título de página;
- texto de login;
- marcador de aplicação saudável.

Caso o endpoint responda 200, mas o conteúdo esperado não apareça, deve registrar “resposta inválida”.

### RF-03 — Monitoramento Oracle

A solução deve consultar, em intervalo configurável, métricas resumidas do Oracle.

Deve coletar no mínimo:
- total de sessões;
- sessões ACTIVE;
- sessões INACTIVE;
- contagem de `SQL*Net message from client`;
- contagem de `resmgr:cpu quantum`;
- contagem de locks bloqueantes;
- sessões JDBC ativas;
- concentração por machine;
- concentração por program;
- concentração por username.

### RF-04 — Captura de waits críticos

A solução deve permitir lista configurável de eventos Oracle a observar, por exemplo:
- `resmgr:cpu quantum`;
- `SQL*Net message from client`;
- `enq: TX - row lock contention`;
- `db file sequential read`;
- `log file sync`;
- `library cache lock`.

### RF-05 — Classificação de anomalias

A solução deve classificar eventos monitorados em estados como:
- normal;
- atenção;
- crítico.

Exemplos:
- latência acima de X ms = atenção;
- timeout = crítico;
- aumento abrupto de sessões ativas = atenção;
- lock bloqueante > 0 = crítico.

### RF-06 — Alertas

A solução deve gerar alertas quando limiares forem atingidos.

Canais mínimos:
- log local;
- arquivo CSV/JSON de alertas.

Canais opcionais:
- e-mail;
- webhook;
- Teams/Slack.

### RF-07 — Persistência

A solução deve persistir os dados coletados em:
- CSV por tipo de coleta;
- SQLite para consultas históricas.

### RF-08 — Relatório resumido

A solução deve gerar resumo por período com:
- disponibilidade observada;
- média, p95 e p99 de latência;
- quantidade de falhas;
- horários críticos;
- eventos Oracle mais frequentes;
- top máquinas/programas/usuários;
- correlação simples entre latência e atividade Oracle.

### RF-09 — Modo contínuo

A solução deve operar continuamente até interrupção manual ou parada controlada.

### RF-10 — Configuração externa

A solução deve ler parâmetros por arquivo de configuração, sem necessidade de editar código.

## 4. Requisitos não funcionais

### RNF-01 — Linguagem

Implementação obrigatória em Python 3.11+.

### RNF-02 — Portabilidade

Deve rodar em:
- Windows;
- Linux.

### RNF-03 — Baixo impacto

A coleta não deve sobrecarregar o ambiente monitorado.
Consultas Oracle devem ser leves, resumidas e de baixa frequência configurável.

### RNF-04 — Observabilidade

A própria aplicação deve ter logs estruturados e claros.

### RNF-05 — Resiliência

Falha em uma coleta não deve derrubar o monitor.
O processo deve continuar executando e registrar o erro.

### RNF-06 — Segurança

Credenciais não devem ficar hardcoded.
Devem ser carregadas por:
- variáveis de ambiente;
- arquivo `.env`;
- arquivo de configuração protegido.

### RNF-07 — Auditabilidade

Toda coleta deve ter timestamp padronizado e rastreável.

### RNF-08 — Manutenibilidade

Código modular, testável e organizado por camadas.

## 5. Arquitetura proposta

### 5.1 Visão geral

A solução deve ser estruturada em módulos:
- `collector_http`
- `collector_oracle`
- `rules_engine`
- `storage`
- `alerts`
- `reporting`
- `scheduler`
- `config`
- `logging`

### 5.2 Arquitetura lógica

Entrada:
- URLs configuradas
- parâmetros Oracle
- thresholds
- eventos de espera monitorados

Processamento:
- coleta HTTP
- coleta Oracle
- normalização
- classificação por regra
- gravação
- alerta

Saída:
- CSV
- SQLite
- logs
- alertas
- relatório

## 6. Estrutura de diretórios esperada

```text
monitor_saas/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── scheduler.py
│   ├── models/
│   │   ├── http_metric.py
│   │   ├── db_metric.py
│   │   └── alert_event.py
│   ├── collectors/
│   │   ├── http_collector.py
│   │   └── oracle_collector.py
│   ├── storage/
│   │   ├── csv_store.py
│   │   └── sqlite_store.py
│   ├── rules/
│   │   └── anomaly_rules.py
│   ├── alerts/
│   │   ├── alert_service.py
│   │   └── webhook_notifier.py
│   ├── reporting/
│   │   └── summary_report.py
│   └── utils/
│       ├── logger.py
│       ├── time_utils.py
│       └── retry.py
├── config/
│   ├── settings.yaml
│   └── .env.example
├── data/
│   ├── csv/
│   ├── sqlite/
│   └── reports/
├── logs/
├── tests/
├── requirements.txt
└── README.md
```

## 7. Modelo de configuração

### 7.1 Arquivo `settings.yaml`

```yaml
app:
  interval_seconds: 15
  timezone: "America/Sao_Paulo"

http:
  timeout_seconds: 20
  verify_tls: true
  endpoints:
    - name: "login"
      url: "https://seu-sistema/login"
      expected_text: "Entrar"
    - name: "home"
      url: "https://seu-sistema/home"
      expected_text: "Dashboard"

oracle:
  enabled: true
  dsn: "${ORACLE_DSN}"
  user: "${ORACLE_USER}"
  password: "${ORACLE_PASSWORD}"
  wait_events:
    - "SQL*Net message from client"
    - "resmgr:cpu quantum"
    - "enq: TX - row lock contention"
    - "db file sequential read"

thresholds:
  http_latency_warning_ms: 2000
  http_latency_critical_ms: 5000
  oracle_active_sessions_warning: 50
  oracle_resmgr_cpu_quantum_warning: 5
  oracle_blocking_locks_critical: 1

storage:
  csv_enabled: true
  sqlite_enabled: true
  sqlite_path: "data/sqlite/monitor.db"

alerts:
  file_enabled: true
  webhook_enabled: false
  webhook_url: ""

report:
  enabled: true
  summary_interval_minutes: 60
```

## 8. Modelo de dados

### 8.1 HTTP metric
Campos mínimos:
- timestamp
- endpoint_name
- url
- http_status
- latency_ms
- success
- content_valid
- error_message

### 8.2 Oracle metric
Campos mínimos:
- timestamp
- instance_name
- host_name
- db_name
- sessions_total
- sessions_active
- sessions_inactive
- wait_sqlnet_client
- wait_resmgr_cpu_quantum
- blocking_locks
- active_jdbc_qtd
- top_machine
- top_program
- top_username
- error_message

### 8.3 Alert event
Campos mínimos:
- timestamp
- severity
- source
- rule_name
- message
- metric_value
- threshold
- context_json

## 9. Regras de negócio

### RN-01
Se endpoint não responder no timeout, registrar falha crítica.

### RN-02
Se endpoint responder com código fora de 200–399, registrar falha.

### RN-03
Se endpoint responder, mas conteúdo esperado não for encontrado, registrar resposta inválida.

### RN-04
Se latência exceder limiar de atenção, gerar alerta de atenção.

### RN-05
Se latência exceder limiar crítico, gerar alerta crítico.

### RN-06
Se `blocking_locks > 0`, gerar alerta crítico.

### RN-07
Se `resmgr:cpu quantum` ultrapassar limiar configurado, gerar alerta de contenção de CPU.

### RN-08
Se sessões ativas crescerem abruptamente em relação à média recente, registrar anomalia.

### RN-09
Se houver falha HTTP simultânea com Oracle aparentemente saudável, classificar hipótese inicial como “camada de aplicação/rede/proxy”.

### RN-10
Se houver alta latência HTTP com aumento de sessões ativas e `resmgr:cpu quantum`, classificar hipótese inicial como “contenção/concorrência”.

## 10. Consultas Oracle mínimas

A implementação deve usar consultas leves.

### 10.1 Sessões por status
Consultar `gv$session` filtrando `type = 'USER'`.

### 10.2 Wait events monitorados
Agrupar por `event`.

### 10.3 Locks bloqueantes
Consultar `gv$lock` ou combinação equivalente.

### 10.4 Top machine/program/username
Agrupar sessões por:
- machine
- program
- username

### 10.5 Metadados da instância
Consultar:
- `v$instance`
- `v$database`

A solução deve encapsular SQL em arquivos ou funções dedicadas.

## 11. Fluxo de execução

### 11.1 Fluxo principal
1. carregar configuração;
2. inicializar logging;
3. inicializar persistência;
4. iniciar loop de coleta;
5. executar coleta HTTP;
6. executar coleta Oracle;
7. aplicar regras;
8. persistir resultados;
9. registrar alertas;
10. aguardar próximo ciclo.

### 11.2 Fluxo de erro
Se qualquer etapa falhar:
- registrar erro;
- marcar coleta com falha;
- continuar execução no próximo ciclo.

## 12. Relatórios esperados

### 12.1 Resumo horário
- total de coletas;
- falhas;
- disponibilidade observada;
- média de latência;
- p95;
- p99;
- top waits Oracle;
- top máquinas/programas.

### 12.2 Resumo diário
- janelas de maior lentidão;
- quantidade de falhas por endpoint;
- momentos com maior concorrência Oracle;
- presença de locks;
- hipóteses automáticas.

### 12.3 Relatório investigativo
Formato texto ou markdown com:
- período analisado;
- principais achados;
- sinais de aplicação;
- sinais de banco;
- correlação com horários críticos;
- recomendação inicial.

## 13. Requisitos de implementação

### 13.1 Bibliotecas sugeridas
- `requests`
- `oracledb`
- `pydantic`
- `pyyaml`
- `sqlite3` nativo
- `pandas` para relatório, se necessário
- `tenacity` opcional para retry

### 13.2 Boas práticas obrigatórias
- tipagem com type hints;
- logging estruturado;
- tratamento de exceções;
- separação por módulos;
- sem credenciais no código;
- funções pequenas;
- testes unitários mínimos.

### 13.3 Padrões de código
- PEP8;
- dataclasses ou pydantic models;
- injeção de configuração;
- queries SQL separadas de regra de negócio.

## 14. Requisitos de operação

### 14.1 Onde executar
Host/servidor local da instituição com:
- acesso HTTP/HTTPS ao sistema;
- acesso Oracle de leitura, se disponível.

### 14.2 Modo de execução
Deve suportar:
- execução em foreground;
- execução contínua como serviço;
- agendamento via Task Scheduler no Windows;
- agendamento via systemd/cron no Linux.

### 14.3 Retenção
Deve permitir retenção configurável:
- CSV diário;
- rotação de logs;
- compactação opcional de histórico.

## 15. Critérios de aceite

A solução será considerada aceita se:
1. monitorar pelo menos 2 endpoints HTTP;
2. gravar métricas com timestamp a cada ciclo;
3. consultar Oracle com sucesso quando habilitado;
4. registrar sessões ativas/inativas;
5. registrar `resmgr:cpu quantum`;
6. registrar locks;
7. persistir em CSV e SQLite;
8. gerar alertas por threshold;
9. sobreviver a falhas sem encerrar o processo;
10. gerar relatório-resumo por período.

## 16. Evoluções futuras

Itens futuros desejáveis:
- dashboard web com FastAPI;
- gráficos de tendência;
- correlação automática com reclamações manuais;
- exportação para Power BI;
- detecção de anomalia com baseline histórico;
- monitoramento de DNS/TCP/TLS;
- teste de login autenticado;
- captura de headers para indício de proxy/load balancer;
- integração com Teams/e-mail.
```

## Observação importante

Este prompt foi endurecido para maximizar a chance de execução real pelo agente, com inspeção do workspace, edição de arquivos, validação local e resposta final objetiva. Ainda assim, o comportamento final do agente e o que ele consegue executar dependem do ambiente, permissões e ferramentas disponíveis.
