# Grid Trading Bot Dashboard Launcher
# PowerShell launcher with system tray support

param(
  [string]$Port = "8080",
  [string]$Hostname = "localhost",
  [int]$Timeout = 30,
  [switch]$NoTray = $false
)

# Colors for output
$Green = @{ ForegroundColor = 'Green' }
$Yellow = @{ ForegroundColor = 'Yellow' }
$Red = @{ ForegroundColor = 'Red' }

function Write-Status {
  param([string]$Message, [string]$Type = "Info")

  switch ($Type) {
    "Success" { Write-Host "✓ $Message" @Green }
    "Warning" { Write-Host "⚠ $Message" @Yellow }
    "Error" { Write-Host "✗ $Message" @Red }
    default { Write-Host "ℹ $Message" }
  }
}

function Test-ApiRunning {
  param([string]$Url)

  try {
    $response = Invoke-WebRequest -Uri "$Url/api/bot/status" -TimeoutSec 2 -ErrorAction Stop
    return $response.StatusCode -eq 200
  }
  catch {
    return $false
  }
}

function Wait-ForApi {
  param(
    [string]$Url,
    [int]$Timeout
  )

  $startTime = Get-Date
  Write-Status "Waiting for bot API server at $Url (timeout: ${Timeout}s)..."

  while (((Get-Date) - $startTime).TotalSeconds -lt $Timeout) {
    if (Test-ApiRunning -Url $Url) {
      Write-Status "Bot API server is running!" "Success"
      return $true
    }
    Start-Sleep -Seconds 1
    Write-Host "." -NoNewline
  }

  Write-Host ""
  return $false
}

function Open-Dashboard {
  param([string]$Url)

  Write-Status "Opening dashboard at $Url" "Success"

  try {
    Start-Process $Url
  }
  catch {
    Write-Status "Could not open browser automatically. Please visit: $Url" "Warning"
  }
}

# Main execution
$DashboardUrl = "http://${Hostname}:${Port}"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗"
Write-Host "║       Grid Trading Bot Dashboard Launcher (PowerShell)         ║"
Write-Host "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

# Check if API is running
if (Wait-ForApi -Url $DashboardUrl -Timeout $Timeout) {
  Open-Dashboard -Url $DashboardUrl
  Write-Host ""
  Write-Status "Dashboard launcher complete!" "Success"
  Write-Host ""
  Write-Host "Tip: You can access the dashboard from your phone on the same network:"
  Write-Host "     http://<your-computer-ip>:${Port}"
  Write-Host ""
}
else {
  Write-Status "Bot API server not responding" "Error"
  Write-Host ""
  Write-Host "Troubleshooting steps:"
  Write-Host "1. Make sure bot is running:"
  Write-Host "   python main.py --config config/config.json"
  Write-Host ""
  Write-Host "2. Try accessing manually: $DashboardUrl"
  Write-Host ""
  Write-Host "3. Check bot console for errors"
  Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
