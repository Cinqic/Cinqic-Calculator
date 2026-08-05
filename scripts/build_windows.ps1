#Requires -Version 5.1
<#
    Builds Cinqic Calculator for Windows: creates a venv, runs tests,
    packages with PyInstaller, builds the Inno Setup installer and a
    portable ZIP, and generates SHA256SUMS.txt. Exits non-zero on failure.
#>

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$VenvPath = Join-Path $RepoRoot ".build-venv"
$DistPath = Join-Path $RepoRoot "dist"
$BuildPath = Join-Path $RepoRoot "build"
$OutputPath = Join-Path $RepoRoot "installer\Output"

function Fail($message) {
    Write-Error $message
    exit 1
}

Write-Host "== 1. Create/refresh virtual environment ==" -ForegroundColor Cyan
if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { Fail "Failed to create virtual environment" }
}
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

Write-Host "== 2. Install pinned build dependencies ==" -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip -q
& $PythonExe -m pip install -e $RepoRoot -q
if ($LASTEXITCODE -ne 0) { Fail "Failed to install package" }
& $PythonExe -m pip install -r (Join-Path $RepoRoot "requirements-build.txt") -q
if ($LASTEXITCODE -ne 0) { Fail "Failed to install build dependencies" }

Write-Host "== 3. Run tests ==" -ForegroundColor Cyan
& $PythonExe -m pytest (Join-Path $RepoRoot "tests") -q
if ($LASTEXITCODE -ne 0) { Fail "Tests failed - aborting build" }

Write-Host "== 4. Remove previous build output ==" -ForegroundColor Cyan
foreach ($path in @($DistPath, $BuildPath, $OutputPath)) {
    if (Test-Path $path) { Remove-Item -Recurse -Force $path }
}

Write-Host "== 5. Build application with PyInstaller ==" -ForegroundColor Cyan
& $PythonExe -m PyInstaller `
    --name "CinqicCalculator" `
    --windowed `
    --onedir `
    --noconfirm `
    --icon (Join-Path $RepoRoot "assets\icons\cinqic-calculator.ico") `
    --paths (Join-Path $RepoRoot "src") `
    (Join-Path $RepoRoot "src\cinqic_calculator\__main__.py")
if ($LASTEXITCODE -ne 0) { Fail "PyInstaller build failed" }

$AppDir = Join-Path $DistPath "CinqicCalculator"
if (-not (Test-Path (Join-Path $AppDir "CinqicCalculator.exe"))) {
    Fail "Expected PyInstaller output not found: CinqicCalculator.exe"
}

Write-Host "== 6. Build Inno Setup installer ==" -ForegroundColor Cyan
$IsccCandidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    $Iscc = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
}
if (-not $Iscc) {
    Fail "Inno Setup (ISCC.exe) not found. Install Inno Setup 6 to build the installer."
}

New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
& $Iscc (Join-Path $RepoRoot "installer\cinqic-calculator.iss")
if ($LASTEXITCODE -ne 0) { Fail "Inno Setup build failed" }

$InstallerExe = Join-Path $OutputPath "Cinqic-Calculator-Windows-x64-Setup.exe"
if (-not (Test-Path $InstallerExe)) { Fail "Installer output not found: $InstallerExe" }

Write-Host "== 7. Build portable ZIP ==" -ForegroundColor Cyan
$PortableZip = Join-Path $OutputPath "Cinqic-Calculator-Windows-x64-Portable.zip"
if (Test-Path $PortableZip) { Remove-Item -Force $PortableZip }
Compress-Archive -Path (Join-Path $AppDir "*") -DestinationPath $PortableZip

Write-Host "== 8. Generate SHA-256 checksums ==" -ForegroundColor Cyan
$ChecksumFile = Join-Path $OutputPath "SHA256SUMS.txt"
& $PythonExe (Join-Path $RepoRoot "scripts\calculate_checksum.py") $ChecksumFile $InstallerExe $PortableZip
if ($LASTEXITCODE -ne 0) { Fail "Checksum generation failed" }

Write-Host "== 9. Verify expected artifacts exist ==" -ForegroundColor Cyan
& $PythonExe (Join-Path $RepoRoot "scripts\verify_release.py") $OutputPath
if ($LASTEXITCODE -ne 0) { Fail "Release verification failed" }

Write-Host "Build complete. Artifacts in $OutputPath" -ForegroundColor Green
exit 0
