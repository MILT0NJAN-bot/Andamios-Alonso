$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name AndamiosAlonsoActualizado --icon 'assets/logo_alonso.png' --collect-all customtkinter --add-data 'app/schema.sql;app' --add-data 'assets;assets' preview_cash.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar la versión de comparación.' }
Write-Host 'Versión de prueba: dist\AndamiosAlonsoActualizado.exe. El ejecutable habitual no se modifica.'
