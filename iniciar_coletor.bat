@echo off
setlocal

cd /d "%~dp0"

echo.
echo [INFO] Iniciando o coletor SaaS...
echo [INFO] Pasta do projeto: %cd%

if not exist ".env" (
    echo [ERRO] Arquivo .env nao encontrado.
    echo [DICA] Copie .env.example para .env e preencha as configuracoes.
    pause
    exit /b 1
)

if not exist "saida" (
    mkdir "saida"
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 ".\coletor_saas.py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python ".\coletor_saas.py"
    ) else (
        echo [ERRO] Python nao encontrado no PATH.
        echo [DICA] Instale o Python ou ajuste a variavel PATH.
        pause
        exit /b 1
    )
)

set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
    echo.
    echo [ERRO] O coletor foi encerrado com codigo %exit_code%.
    pause
)

endlocal & exit /b %exit_code%
