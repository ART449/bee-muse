$ErrorActionPreference='Stop'
$installRoot=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\Bee-Muse'))
$actualRoot=[IO.Path]::GetFullPath($PSScriptRoot)
if($actualRoot -ne $installRoot -or -not(Test-Path -LiteralPath (Join-Path $installRoot 'bee-muse-install.marker'))){throw 'La retirada sólo puede ejecutarse desde la instalación identificada de Bee-Muse.'}
Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($installRoot+'\',[StringComparison]::OrdinalIgnoreCase) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$menu=Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\Bee-Muse.lnk'
if(Test-Path -LiteralPath $menu){Remove-Item -LiteralPath $menu -Force}
$entry='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\IArtLabsBeeMuse'
if(Test-Path -LiteralPath $entry){Remove-Item -LiteralPath $entry -Recurse}
Remove-Item -LiteralPath $installRoot -Recurse -Force
Write-Output 'Bee-Muse retirado. Se conservaron biblioteca, historial y datos de Roaming.'
