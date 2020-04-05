# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src/eo_web.py'],
             pathex=['/emptyorchestra'],
             binaries=[
                #('/usr/lib/x86_64-linux-gnu/*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libjavascriptcoregtk*', '.'),
                #('/usr/lib/x86_64-linux-gnu/libwebkit2gtk*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libicuuc*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libicui18n*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libwebp*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libicudata*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libpng*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libssh*', '.'),
                #('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/W*', 'webkit2gtk-4.0'),
                #('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/M*', 'webkit2gtk-4.0'),
                #('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/injected-bundle/libwebkit2gtkinjectedbundle.so', 'webkit2gtk-4.0/injected-bundle'),
                ('/usr/lib/x86_64-linux-gnu/gstreamer-1.0/*', 'gstreamer-1.0'),
                #('/usr/local/lib/python3.5/dist-packages/pip/_vendor/certifi/cacert.pem', 'pip/_vendor/certifi')
            ],
             datas=[
                ('src/templates/*.html','emptyorchestra/templates'),
                ('src/templates/*.js','emptyorchestra/templates'),
                ('src/static/images/*','emptyorchestra/static/images'),
                ('src/static/tracks/*.mp3','emptyorchestra/static/tracks'),
                ('src/static/css/*.css', 'emptyorchestra/static/css'),
                ('src/static/js/*.js', 'emptyorchestra/static/js'),
                ('src/static/*.mp3', 'emtpyorchestra/static'),
                ('src/eo_conf.yml', 'emptyorchestran'),
                ('src/*.py', '.'),
                ('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/injected-bundle/libwebkit2gtkinjectedbundle.so', 'webkit2gtk-4.0/injected-bundle'),
                ('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKit*', 'webkit2gtk-4.0'),
                ('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKit*', '.'),
                ('/usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/injected-bundle/libwebkit2gtkinjectedbundle.so', '.'),
                #('/usr/lib/x86_64-linux-gnu/gstreamer-1.0/*', 'gstreamer-1.0'),
                #('/usr/lib/x86_64-linux-gnu/gstreamer-1.0/*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libjavascriptcoregtk*', '.'),
                ('/usr/lib/x86_64-linux-gnu/libwebkit2gtk*', '.'),
                ('mic1.*', '.')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='emptyorch_amd64_linux',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True, 
          icon="emptyorchestra_amd64_linxu.png"
)
