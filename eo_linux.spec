# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src/eo_web.py'],
             pathex=['/emptyorchestra'],
             binaries=[],
             datas=[
                ('src/templates/*.html','emptyorchestra/templates'),
                ('src/templates/*.js','emptyorchestra/templates'),
                ('src/static/images/*','emptyorchestra/static/images'),
                ('src/static/tracks/*.mp3','emptyorchestra/static/tracks'),
                ('src/static/css/*.css', 'emptyorchestra/static/css'),
                ('src/static/js/*.js', 'emptyorchestra/static/js'),
                ('src/static/*.mp3', 'emtpyorchestra/static'),
                ('src/eo_conf.yml', '.'),
                ('src/*.py', '.'),
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
          console=True )
