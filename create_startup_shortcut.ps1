$WshShell = New-Object -ComObject WScript.Shell
$StartupPath = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupPath "GridBot Fleet.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "D:\gridbotchuck\start_all_bots.bat"
$Shortcut.WorkingDirectory = "D:\gridbotchuck"
$Shortcut.Description = "Start all trading bots"
$Shortcut.Save()
Write-Host "Startup shortcut created at: $ShortcutPath"
