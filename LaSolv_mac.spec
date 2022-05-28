# -*- mode: python -*-

import sys
sys.setrecursionlimit(5000)

block_cipher = None


a = Analysis(['./src/gui_wx.py', './src/Enums.py', './src/eqnSolver.py'],
             pathex=['/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages', './src'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', 'tkinter', '_tkinter', 'Tkinter'],
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
          name='LaSolv',
          debug=False,
          bootloader_ignore_signals=False,
          strip=True,
          upx=True,
          runtime_tmpdir=None,
          console=False, icon='LaSolv_icon.icns')
