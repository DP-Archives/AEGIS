[app]
title = AEGIS
package.name = aegis
package.domain = org.dparchive
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
source.include_patterns = actions/*,core/*,memory/*,config/*,assets/*
version = 1.0
requirements = python3,kivy==2.3.0,pillow,requests,beautifulsoup4,numpy,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = RECORD_AUDIO,POST_NOTIFICATIONS,FOREGROUND_SERVICE,USE_FULL_SCREEN_INTENT,ACCESS_NOTIFICATION_POLICY
android.api = 34
android.minapi = 26
android.ndk = 25b
android.allow_backup = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.wakelock = True
android.enable_androidx = True
