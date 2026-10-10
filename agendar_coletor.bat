@echo off
setlocal

cd /d "%~dp0"

set "TASK_NAME=ColetorSaaS_ErroPrd"
set "TASK_SCRIPT=%~dp0iniciar_coletor.bat"

echo.
echo [INFO] Criando ou atualizando a tarefa agendada...
echo [INFO] Nome da tarefa: %TASK_NAME%

if not exist "%TASK_SCRIPT%" (
    echo [ERRO] Arquivo iniciar_coletor.bat nao encontrado.
    pause
    endlocal & exit /b 1
)

schtasks /create /tn "%TASK_NAME%" /sc ONLOGON /tr "\"%TASK_SCRIPT%\"" /f >nul

if not "%errorlevel%"=="0" (
    echo [ERRO] Nao foi possivel criar a tarefa agendada.
    echo [DICA] Execute este arquivo como o usuario que deve rodar o coletor.
    pause
    endlocal & exit /b 1
)

echo [OK] Tarefa agendada criada com sucesso.
echo [INFO] O coletor sera iniciado no logon do usuario atual.
echo [INFO] Para remover manualmente: schtasks /delete /tn "%TASK_NAME%" /f

endlocal & exit /b 0
