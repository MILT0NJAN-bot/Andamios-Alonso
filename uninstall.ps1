$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
try {
    $expectedDir = [IO.Path]::GetFullPath((Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Programs\AndamiosAlonso'))
    $actualDir = [IO.Path]::GetFullPath($PSScriptRoot)
    if (-not $actualDir.Equals($expectedDir, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Este desinstalador solo funciona desde la carpeta instalada de Andamios Alonso.'
    }
    $installedExe = Join-Path $actualDir 'AndamiosAlonso.exe'
    $running = Get-Process -Name AndamiosAlonso -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -eq $installedExe }
    if ($running) { throw 'Cierra Andamios Alonso antes de desinstalarlo.' }
    $answer = [Windows.Forms.MessageBox]::Show(
        'Se quitara el programa. Se conservaran clientes, documentos, rentas y respaldos. Deseas continuar?',
        'Desinstalar Andamios Alonso', 'YesNo', 'Question')
    if ($answer -ne [Windows.Forms.DialogResult]::Yes) { exit }
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in @('Desktop', 'Programs')) {
        $link = Join-Path ([Environment]::GetFolderPath($folder)) 'Andamios Alonso.lnk'
        if ((Test-Path -LiteralPath $link) -and $shell.CreateShortcut($link).TargetPath -eq $installedExe) {
            Remove-Item -LiteralPath $link -Force
        }
    }
    $uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AndamiosAlonso'
    $registration = Get-ItemProperty -LiteralPath $uninstallKey -ErrorAction SilentlyContinue
    if ($registration -and $registration.InstallLocation -eq $actualDir) {
        Remove-Item -LiteralPath $uninstallKey -Force
    }
    # Solo archivos propios; nunca se elimina la carpeta de datos del negocio.
    foreach ($filename in @('AndamiosAlonso.exe', 'GUIA_OPERACION.md', 'installation.json', 'uninstall.ps1')) {
        $path = Join-Path $actualDir $filename
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
    if (-not (Get-ChildItem -LiteralPath $actualDir -Force)) {
        Remove-Item -LiteralPath $actualDir
    }
    [Windows.Forms.MessageBox]::Show('Programa desinstalado. Tus datos y respaldos se conservaron.', 'Andamios Alonso') | Out-Null
} catch {
    [Windows.Forms.MessageBox]::Show($_.Exception.Message, 'No se pudo desinstalar', 'OK', 'Error') | Out-Null
    exit 1
}
