[app]
title = JARVIS
package.name = jarvis
package.domain = org.gordeev
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,kivymd,requests,speechrecognition,urllib3,certifi,chardet,idna
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.permissions = INTERNET, RECORD_AUDIO, FOREGROUND_SERVICE, POST_NOTIFICATIONS
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True