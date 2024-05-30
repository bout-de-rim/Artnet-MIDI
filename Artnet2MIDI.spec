# artnet2midi.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['artnet2midi.py'],
             pathex=['.'],
             binaries=[],
             datas=[('artnet2midi.png', '.')],
             hiddenimports=['mido.backends.rtmidi'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='artnet2midi',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='artnet2midi.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='artnet2midi')
