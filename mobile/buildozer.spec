[app]
# (str) Title of your application
title = ChatApp

# (str) Package name
package.name = chatapp

# (str) Package domain (needed for android)
package.domain = org.example

# (str) Source code where the main.py is located
source.dir = .

# (list) Source files to include (let empty to include all .py files)
#source.include_exts = py,png,jpg,kv,ini

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy,requests,websocket-client,pillow,plyer

# (str) Supported orientation (one of: landscape, portrait)
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (str) Android API target
android.api = 33

# (int) Android NDK version to use
#android.ndk = 25b

# (str) Presplash image (optional)
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon file
# icon.filename = %(source.dir)s/data/icon.png

[buildozer]
# (str) Path to buildozer.spec
log_level = 2
