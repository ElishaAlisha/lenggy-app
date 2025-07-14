[app]
title = Lenggy's App
package.name = lenggyapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,json
version = 0.1
requirements = python3,kivy
icon.filename = assets/app_icon.png

[buildozer]
log_level = 1

[app:android]
permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
arch.armeabi-v7a = 1
