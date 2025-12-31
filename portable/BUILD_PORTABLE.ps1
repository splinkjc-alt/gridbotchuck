# GridBot Portable Builder
# Downloads Python embedded and packages everything for easy distribution

$ErrorActionPreference = "Stop"
$PortableDir = $PSScriptRoot
$PythonVersion = "3.11.9"
$PythonZip = "python-$PythonVersion-embed-amd64.zip"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/$PythonZip"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GridBot Portable Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create directories
Write-Host "[1/6] Creating directory structure..." -ForegroundColor Yellow
$dirs = @("python", "scripts", "logs", "config")
foreach ($dir in $dirs) {
  New-Item -ItemType Directory -Path "$PortableDir\$dir" -Force | Out-Null
}

# Download Python embedded
Write-Host "[2/6] Downloading Python $PythonVersion embedded..." -ForegroundColor Yellow
$pythonZipPath = "$PortableDir\$PythonZip"
if (-not (Test-Path $pythonZipPath)) {
  Invoke-WebRequest -Uri $PythonUrl -OutFile $pythonZipPath
}

# Extract Python
Write-Host "[3/6] Extracting Python..." -ForegroundColor Yellow
Expand-Archive -Path $pythonZipPath -DestinationPath "$PortableDir\python" -Force
Remove-Item $pythonZipPath -Force

# Enable pip in embedded Python (modify python311._pth)
Write-Host "[4/6] Configuring Python for pip..." -ForegroundColor Yellow
$pthFile = Get-ChildItem "$PortableDir\python\python*._pth" | Select-Object -First 1
if ($pthFile) {
  $content = Get-Content $pthFile.FullName
  $content = $content -replace "#import site", "import site"
  $content | Set-Content $pthFile.FullName
}

# Download and install pip
Write-Host "[5/6] Installing pip and dependencies..." -ForegroundColor Yellow
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath = "$PortableDir\get-pip.py"
Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath

# Run get-pip.py
& "$PortableDir\python\python.exe" $getPipPath --no-warn-script-location
Remove-Item $getPipPath -Force

# Install required packages
$packages = @("ccxt", "python-dotenv", "pandas", "aiohttp")
foreach ($pkg in $packages) {
  Write-Host "  Installing $pkg..." -ForegroundColor Gray
  & "$PortableDir\python\python.exe" -m pip install $pkg --no-warn-script-location --quiet
}

# Copy bot scripts
Write-Host "[6/6] Copying bot scripts..." -ForegroundColor Yellow
$parentDir = Split-Path $PortableDir -Parent
$scripts = @("run_ema_bot.py", "scan_ema_signals.py", "health_check.py")
foreach ($script in $scripts) {
  $src = "$parentDir\$script"
  if (Test-Path $src) {
    Copy-Item $src "$PortableDir\scripts\" -Force
  }
}

# Copy strategy file
if (Test-Path "$parentDir\strategies\ema_crossover_strategy.py") {
  New-Item -ItemType Directory -Path "$PortableDir\scripts\strategies" -Force | Out-Null
  Copy-Item "$parentDir\strategies\ema_crossover_strategy.py" "$PortableDir\scripts\strategies\" -Force
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit config\.env with your API keys" -ForegroundColor White
Write-Host "2. Double-click START_BOT.bat to run" -ForegroundColor White
Write-Host ""
