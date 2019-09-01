# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\eo_web.py'],
             pathex=['Z:\\src'],
             binaries=[],
             datas=[
                ('/wine/drive_c/Python36/Lib/site-packages/webview/lib/WebBrowserInterop.x64.dll','webview/lib'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.dll', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.dat', 'cefpython3'),
                #('/wine/drive_c/Python36/Lib/site-packages/cefpython3/*.bin', 'cefpython3'),
                ('src/templates/*','templates'),
                ('src/static/images/*','static/images'),
                ('src/static/tracks/*','static/tracks'),
                ('src/static/css/*', 'static/css'),
                ('src/static/*.mp3', 'static'),
                ('src/eo_conf.yml', '.'),
                ('src/id3reader.py', '.'),
                ('src/youtube.py', '.')
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
          name='emptyorch',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
