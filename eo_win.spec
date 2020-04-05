# -*- mode: python -*-


import os
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import is_module_satisfies
from PyInstaller.archive.pyz_crypto import PyiBlockCipher


block_cipher = None



a = Analysis(['src\\eo_web.py'],
             pathex=['Z:\\src'],
             binaries=[],
             datas=[
                ('src/templates/*.html','emptyorchestra/templates'),
                ('src/templates/*.js','emptyorchestra/templates'),
                ('src/static/images/*','emptyorchestra/static/images'),
                ('src/static/tracks/*.mp3','emptyorchestra/static/tracks'),
                ('src/static/css/*.css', 'emptyorchestra/static/css'),
                ('src/static/js/*.js', 'emptyorchestra/static/js'),
                ('src/static/*.mp3', 'emptyorchestra/static'),
                ('src/eo_conf.yml', 'emptyorchestra'),
                ('src/*.py', '.'),
                ('/wine/drive_c/Python36/Lib/site-packages/webview/lib/WebBrowserInterop.x64.dll','webview/lib'),
                ('mic1.png', '.')
                #('/wine/drive_c/Python36/Lib/site-packages/pip/_vendor/certifi','pip/_vendor/certifi'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.dat', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.dll', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.pak', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/locales/*', 'cefpython3/locales'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/swiftshader/*', 'cefpython3/swiftshader'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.bin', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.dll', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.dat', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.bin', 'cefpython3'),
                #('src/templates/*','templates'),
                #('src/static/images/*','static/images'),
                #('src/static/tracks/*','static/tracks'),
                #('src/static/css/*', 'static/css'),
                #('src/static/*.mp3', 'static'),
                #('src/eo_conf.yml', '.'),
                #('src/id3reader.py', '.'),
                #('src/youtube.py', '.')
             ],
             hiddenimports=[],
             hookspath=['./hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=True,
             win_private_assemblies=True,
             cipher=block_cipher,
             noarchive=False)

#if not os.environ.get("PYINSTALLER_CEFPYTHON3_HOOK_SUCCEEDED", None):
#    raise SystemExit("Error: Pyinstaller hook-cefpython3.py script was "
#                     "not executed or it failed")

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='emptyorch_win',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=True, 
          icon="mic1.ico"
)
