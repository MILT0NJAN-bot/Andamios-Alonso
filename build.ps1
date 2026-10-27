$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name AndamiosAlonso --collect-all customtkinter --add-data 'app/schema.sql;app' --add-data 'assets;assets' main.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el ejecutable.' }
Write-Host 'Ejecutable generado: dist\AndamiosAlonso.exe'
if (Test-Path -LiteralPath '.\dist\AndamiosAlonsoActualizado.exe') {
    try {
        Copy-Item -LiteralPath '.\dist\AndamiosAlonso.exe' -Destination '.\dist\AndamiosAlonsoActualizado.exe' -Force -ErrorAction Stop
        Write-Host ''
    } catch {
        Write-Warning 'No se pudo actualizar el nombre anterior porque está en uso. La versión nueva es dist\AndamiosAlonso.exe.'
    }
}
