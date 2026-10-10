@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM deploy.bat: commit + push com Conventional Commits no Windows.

echo.
echo [INFO] Verificando o status do repositorio Git...

REM 1) Verifica se esta dentro de um repositorio Git
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Este nao e um repositorio Git. Abortando.
    goto :END
)

REM 2) Verifica se existe ao menos 1 commit (HEAD)
git rev-parse --verify HEAD >nul 2>&1
set "HAS_HEAD=1"
if errorlevel 1 set "HAS_HEAD=0"

REM 3) Verifica se ha alteracoes (inclui untracked)
REM    - tracked: git diff --quiet
REM    - staged : git diff --cached --quiet
REM    - untracked: git ls-files --others --exclude-standard
set "HAS_CHANGES=0"

git diff --quiet >nul 2>&1
if errorlevel 1 set "HAS_CHANGES=1"

git diff --cached --quiet >nul 2>&1
if errorlevel 1 set "HAS_CHANGES=1"

for /f "delims=" %%U in ('git ls-files --others --exclude-standard') do (
    set "HAS_CHANGES=1"
    goto :AFTER_UNTRACKED_CHECK
)
:AFTER_UNTRACKED_CHECK

if "%HAS_CHANGES%"=="0" (
    echo [INFO] Nenhuma alteracao para commitar. Arvore de trabalho limpa.
    goto :END
)

echo.
echo [INFO] Arquivos modificados/novos:
git status -sb

echo.
echo Selecione o tipo de commit (Conventional Commits):
echo   1. feat:     Um novo recurso para o usuario
echo   2. fix:      Correcao de um bug
echo   3. docs:     Alteracoes na documentacao
echo   4. style:    Formatacao etc (sem mudanca de codigo)
echo   5. refactor: Refatoracao de codigo
echo   6. test:     Adicionando ou corrigindo testes
echo   7. chore:    Tarefas de build, configs, etc.
echo.

:CHOICE_LOOP
set "COMMIT_TYPE="
set /p "CHOICE=Digite o numero da sua escolha: "

if "%CHOICE%"=="1" set "COMMIT_TYPE=feat"
if "%CHOICE%"=="2" set "COMMIT_TYPE=fix"
if "%CHOICE%"=="3" set "COMMIT_TYPE=docs"
if "%CHOICE%"=="4" set "COMMIT_TYPE=style"
if "%CHOICE%"=="5" set "COMMIT_TYPE=refactor"
if "%CHOICE%"=="6" set "COMMIT_TYPE=test"
if "%CHOICE%"=="7" set "COMMIT_TYPE=chore"

if not defined COMMIT_TYPE (
    echo [AVISO] Selecao invalida. Tente novamente.
    goto :CHOICE_LOOP
)

echo.
set /p "COMMIT_MESSAGE=Digite a mensagem do commit (seja descritivo): "
if not defined COMMIT_MESSAGE (
    echo [ERRO] A mensagem de commit nao pode ser vazia. Abortando.
    goto :END
)

REM Remove aspas para evitar quebrar o -m
set "COMMIT_MESSAGE=!COMMIT_MESSAGE:"=!"

set "FULL_COMMIT_MESSAGE=!COMMIT_TYPE!: !COMMIT_MESSAGE!"

echo.
echo [INFO] Commit a ser criado: "!FULL_COMMIT_MESSAGE!"
pause

echo.
echo [INFO] Adicionando todos os arquivos ao stage (git add -A)...
git add -A
if errorlevel 1 (
    echo [ERRO] Falha no git add. Verifique os erros acima.
    goto :END
)

echo [INFO] Realizando o commit...
git commit -m "!FULL_COMMIT_MESSAGE!"
if errorlevel 1 (
    echo [ERRO] Falha no commit. Verifique os erros acima.
    goto :END
)

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set "CURRENT_BRANCH=%%b"

REM 4) Sincroniza com remoto antes do push (evita rejeicao por divergencia)
git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Upstream nao configurado. Criando com -u origin "!CURRENT_BRANCH!"...
    git push -u origin "!CURRENT_BRANCH!"
    if errorlevel 1 (
        echo [ERRO] Falha ao criar upstream. Verifique os erros acima.
        goto :END
    )
    goto :PUSH_DONE
)

echo [INFO] Atualizando referencias remotas...
git fetch --prune
if errorlevel 1 (
    echo [ERRO] Falha no git fetch. Verifique os erros acima.
    goto :END
)

for /f "delims=" %%a in ('git rev-list --count HEAD..@{u} 2^>nul') do set "BEHIND_COUNT=%%a"
if not defined BEHIND_COUNT set "BEHIND_COUNT=0"

if not "%BEHIND_COUNT%"=="0" (
    echo [INFO] Branch local esta %BEHIND_COUNT% commits atras do remoto. Executando rebase...
    git pull --rebase
    if errorlevel 1 (
        echo [ERRO] Falha no rebase. Resolva conflitos e execute novamente.
        goto :END
    )
)

REM 4) Push robusto: se nao houver upstream, cria com -u
echo [INFO] Realizando push para a branch "!CURRENT_BRANCH!"...
git push

if errorlevel 1 (
    echo [ERRO] Falha no push. Verifique os erros e sua conexao.
    goto :END
)

echo.
echo [SUCESSO] Dados enviados para o repositorio com sucesso!
echo.
:PUSH_DONE

:END
pause
endlocal
