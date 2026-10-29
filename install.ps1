param([string]$Version = '2026.10.29.1')

$ErrorActionPreference = 'Stop'
$sourceExe = Join-Path $PSScriptRoot 'dist\AndamiosAlonso.exe'
if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
    throw 'Primero genera el programa con build.ps1.'
}
$installDir = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Programs\AndamiosAlonso'
$installedExe = Join-Path $installDir 'AndamiosAlonso.exe'
$desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Andamios Alonso.lnk'
$menuLink = Join-Path ([Environment]::GetFolderPath('Programs')) 'Andamios Alonso.lnk'
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AndamiosAlonso'

$running = Get-Process -Name AndamiosAlonso -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $installedExe }
if ($running) { throw 'Cierra la version instalada de Andamios Alonso y vuelve a ejecutar el instalador.' }
$previous = Get-ItemProperty -LiteralPath $uninstallKey -ErrorAction SilentlyContinue
if ($previous -and $previous.InstallLocation -ne $installDir) {
    throw 'Hay una instalacion en otra ubicacion. Conserva sus datos y revisala antes de continuar.'
}

New-Item -ItemType Directory -Path $installDir -Force | Out-Null
$stagedExe = Join-Path $installDir 'AndamiosAlonso.exe.new'
try {
    Copy-Item -LiteralPath $sourceExe -Destination $stagedExe -Force
    $sourceHash = (Get-FileHash -LiteralPath $sourceExe -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $stagedExe -Algorithm SHA256).Hash -ne $sourceHash) {
        throw 'La copia del programa no coincide con el original.'
    }
    Move-Item -LiteralPath $stagedExe -Destination $installedExe -Force
} finally {
    if (Test-Path -LiteralPath $stagedExe) { Remove-Item -LiteralPath $stagedExe -Force }
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'uninstall.ps1') -Destination $installDir -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'GUIA_OPERACION.md') -Destination $installDir -Force

$shell = New-Object -ComObject WScript.Shell
foreach ($linkPath in @($desktopLink, $menuLink)) {
    $shortcut = $shell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $installedExe
    $shortcut.WorkingDirectory = $installDir
    $shortcut.Description = 'Andamios Alonso - Control de rentas y expedientes de clientes'
    $shortcut.IconLocation = "$installedExe,0"
    $shortcut.Save()
}

$powershellExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$uninstaller = Join-Path $installDir 'uninstall.ps1'
New-Item -Path $uninstallKey -Force | Out-Null
$properties = @{
    DisplayName = 'Andamios Alonso'
    DisplayVersion = $Version
    Publisher = 'Andamios Alonso'
    InstallLocation = $installDir
    DisplayIcon = "$installedExe,0"
    InstallDate = (Get-Date -Format 'yyyyMMdd')
    UninstallString = ('"{0}" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{1}"' -f $powershellExe, $uninstaller)
}
foreach ($name in $properties.Keys) {
    New-ItemProperty -LiteralPath $uninstallKey -Name $name -Value $properties[$name] -PropertyType String -Force | Out-Null
}
foreach ($name in @('NoModify', 'NoRepair')) {
    New-ItemProperty -LiteralPath $uninstallKey -Name $name -Value 1 -PropertyType DWord -Force | Out-Null
}
New-ItemProperty -LiteralPath $uninstallKey -Name EstimatedSize -Value ([int][Math]::Ceiling((Get-Item -LiteralPath $installedExe).Length / 1024)) -PropertyType DWord -Force | Out-Null
[ordered]@{ version = $Version; executable = $installedExe; sha256 = $sourceHash } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $installDir 'installation.json') -Encoding UTF8

Write-Output "Instalado: $installedExe"
Write-Output "Acceso de escritorio: $desktopLink"
Write-Output "Acceso del menu Inicio: $menuLink"
Write-Output 'La base de datos existente se conserva en LocalAppData\AndamiosAlonso.'
