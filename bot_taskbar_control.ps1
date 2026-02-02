# Grid Trading Bot - Taskbar Control Launcher (PowerShell)
# This script launches the bot taskbar control application with nice formatting

$Title = "Grid Trading Bot - Taskbar Control"
$Green = @{ ForegroundColor = 'Green' }
$Red = @{ ForegroundColor = 'Red' }
$Yellow = @{ ForegroundColor = 'Yellow' }

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" @Green
Write-Host "║     Grid Trading Bot - Taskbar Control                     ║" @Green
Write-Host "╚════════════════════════════════════════════════════════════╝" @Green
Write-Host ""

# Check if Python is installed
try {
  $pythonVersion = python --version 2>&1
  Write-Host "✓ Python found: $pythonVersion" @Green
}
catch {
  Write-Host "❌ Python is not installed or not in PATH" @Red
  Write-Host ""
  Write-Host "Please install Python or add it to your PATH"
  Read-Host "Press Enter to exit"
  exit 1
}

# Check if required modules are installed
Write-Host "Checking for required packages..." @Yellow

$missingPackages = @()
foreach ($package in @("pystray", "PIL", "requests")) {
  try {
    python -c "import $package" 2>$null
  }
  catch {
    $missingPackages += $package
  }
}

if ($missingPackages.Count -gt 0) {
  Write-Host "⚠️  Installing missing packages: $($missingPackages -join ', ')" @Yellow
  Write-Host ""

  pip install pystray pillow requests

  if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install packages" @Red
    Read-Host "Press Enter to exit"
    exit 1
  }
}

Write-Host "✓ All packages ready" @Green
Write-Host ""
Write-Host "Starting taskbar control application..." @Green
Write-Host ""

# Run the bot control application
python bot_taskbar_control.py

if ($LASTEXITCODE -ne 0) {
  Write-Host ""
  Write-Host "❌ Error running bot control application" @Red
  Read-Host "Press Enter to exit"
  exit 1
}

Read-Host "Press Enter to exit"
