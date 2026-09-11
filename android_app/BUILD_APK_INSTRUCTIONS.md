# Build AEGIS APK - Step by Step

## Prerequisites
* Windows 10/11 with PowerShell
* Python 3.11+ installed
* At least 10 GB free disk
* Internet connection

## One-time setup

1. Open PowerShell as Administrator
2. Install Buildozer and dependencies
```powershell
pip install buildozer cython
```

3. Let Buildozer download Android SDK/NDK. First run will take long:
```powershell
cd "D:\Devang\Github\Mark-LII-main - Mobile\android_app"
buildozer android debug
```

Buildozer will:
* Download SDK/NDK ~4GB
* Compile python-for-android toolchain
* Build APK

The APK will appear at:
`D:\Devang\Github\Mark-LII-main - Mobile\android_app\bin\AEGIS-1.0-debug.apk`

## Project structure ready

```
android_app/
  main.py              # Kivy loading screen + entry
  buildozer.spec       # Build config
  assets/logo.png      # Your logo
  actions/             # From root AEGIS project - copy here
  core/                # From root AEGIS project - copy here
  memory/              # From root AEGIS project - copy here
  config/              # From root AEGIS project - copy here
```

To include full AEGIS code:
```powershell
Copy-Item "D:\Devang\Github\Mark-LII-main - Mobile\actions" "D:\Devang\Github\Mark-LII-main - Mobile\android_app\actions" -Recurse -Force
Copy-Item "D:\Devang\Github\Mark-LII-main - Mobile\core" "D:\Devang\Github\Mark-LII-main - Mobile\android_app\core" -Recurse -Force
Copy-Item "D:\Devang\Github\Mark-LII-main - Mobile\memory" "D:\Devang\Github\Mark-LII-main - Mobile\android_app\memory" -Recurse -Force
Copy-Item "D:\Devang\Github\Mark-LII-main - Mobile\config" "D:\Devang\Github\Mark-LII-main - Mobile\android_app\config" -Recurse -Force
```

Then update buildozer.spec `source.include_patterns` to include those folders.

## Install APK on phone
1. Enable Developer Options + USB debugging on Android
2. Connect phone via USB
3. Run:
```powershell
buildozer android deploy run
```
Or copy APK manually to phone and install.

## Troubleshooting
* `SDK not found` - Run `buildozer android debug` once, it will download
* `Out of memory` - Close Chrome, increase virtual memory
* `Permission denied` - Run PowerShell as Administrator

If you want, I can generate a ready-to-run PowerShell script `build_apk.ps1` that does all copying and building automatically.
