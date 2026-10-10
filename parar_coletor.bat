@echo off
setlocal

cd /d "%~dp0"

echo.
echo [INFO] Procurando o coletor em execucao...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$project = (Resolve-Path '%~dp0').Path.TrimEnd('\');" ^
  "$projectName = Split-Path $project -Leaf;" ^
  "$processes = Get-CimInstance Win32_Process | Where-Object {" ^
  "  $_.Name -match '^(python|pythonw)(\.exe)?$' -and" ^
  "  $_.CommandLine -match 'coletor_saas\.py' -and" ^
  "  ($_.CommandLine -match [regex]::Escape($projectName) -or $_.CommandLine -match '\\\.\\coletor_saas\.py' -or $_.CommandLine -match 'coletor_saas.py')" ^
  "};" ^
  "if (-not $processes) { exit 3 }" ^
  "foreach ($process in $processes) {" ^
  "  Stop-Process -Id $process.ProcessId -Force;" ^
  "  Write-Host ('[OK] Processo encerrado: PID=' + $process.ProcessId)" ^
  "}"

set "exit_code=%errorlevel%"

if "%exit_code%"=="3" (
    echo [INFO] Nenhum processo do coletor foi encontrado.
    endlocal & exit /b 0
)

if not "%exit_code%"=="0" (
    echo [ERRO] Nao foi possivel encerrar o coletor.
    pause
    endlocal & exit /b %exit_code%
)

echo [INFO] Coletor encerrado.

endlocal & exit /b 0
