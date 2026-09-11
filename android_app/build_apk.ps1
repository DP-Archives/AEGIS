# build_apk.ps1 - Automated AEGIS APK Build
$ErrorActionPreference = "Stop"

$root = "D:\Devang\Github\Mark-LII-main - Mobile"
$appDir = "$root\android_app"

Write-Host "=== AEGIS APK Builder ===" -ForegroundColor Cyan

# Create app dir if missing
New-Item -ItemType Directory -Force -Path $appDir | Out-Null

# Copy core AEGIS modules
Write-Host "Copying AEGIS modules..." -ForegroundColor Yellow
@("actions","core","memory","config") | ForEach-Object {
    $src = Join-Path $root $_
    $dst = Join-Path $appDir $_
    if (Test-Path $src) {
        Copy-Item $src $dst -Recurse -Force
        Write-Host "Copied $_" -ForegroundColor Green
    }
}

# Ensure logo
if (!(Test-Path "$appDir\assets\logo.png")) {
    New-Item -ItemType Directory -Force -Path "$appDir\assets" | Out-Null
    Copy-Item "$root\logo.png" "$appDir\assets\logo.png" -Force
}

Write-Host "Installing Buildozer..." -ForegroundColor Yellow
pip install -q buildozer cython

Write-Host "Starting build. This will take a long time on first run..." -ForegroundColor Cyan
Set-Location $appDir
buildozer android debug

Write-Host "Build complete! APK at $appDir\bin\AEGIS-*.apk" -ForegroundColor Green
