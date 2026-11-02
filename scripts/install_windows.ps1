param([string]$Package=(Join-Path $PSScriptRoot '..\desktop\ready\Bee-Muse-win32-x64'))
$ErrorActionPreference='Stop'
$packageRoot=(Resolve-Path -LiteralPath $Package).Path
$installRoot=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\Bee-Muse'))
if(-not(Test-Path -LiteralPath (Join-Path $packageRoot 'Bee-Muse.exe')) -or -not(Test-Path -LiteralPath (Join-Path $packageRoot 'resources\backend\bee-muse-service.exe'))){throw 'El paquete de Bee-Muse no está completo.'}
if($packageRoot -eq $installRoot){throw 'El paquete de origen ya es la instalación.'}
Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($installRoot+'\',[StringComparison]::OrdinalIgnoreCase) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
Get-ChildItem -LiteralPath $packageRoot -Force | Copy-Item -Destination $installRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'uninstall_windows.ps1') -Destination $installRoot -Force
Set-Content -LiteralPath (Join-Path $installRoot 'bee-muse-install.marker') -Value 'IArtLabs Bee-Muse user installation'
$menu=Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\Bee-Muse.lnk'
$shell=New-Object -ComObject WScript.Shell
$shortcut=$shell.CreateShortcut($menu);$shortcut.TargetPath=Join-Path $installRoot 'Bee-Muse.exe';$shortcut.WorkingDirectory=$installRoot;$shortcut.Save()
$entry='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\IArtLabsBeeMuse'
New-Item -Path $entry -Force | Out-Null
New-ItemProperty -Path $entry -Name DisplayName -Value 'Bee-Muse · IArtLabs' -Force | Out-Null
New-ItemProperty -Path $entry -Name DisplayVersion -Value '0.5.0' -Force | Out-Null
New-ItemProperty -Path $entry -Name Publisher -Value 'IArtLabs' -Force | Out-Null
New-ItemProperty -Path $entry -Name UninstallString -Value ('powershell.exe -NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $installRoot 'uninstall_windows.ps1')+'"') -Force | Out-Null
Write-Output ('Instalado en '+$installRoot+'. El catálogo y el historial se conservan en sus ubicaciones actuales.')
