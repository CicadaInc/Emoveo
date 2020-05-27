# -*- mode: python ; coding: utf-8 -*-
import os

include = ['media', 'ui']
include_files = ['database.db']


def make_datas(path='.'):
    datas = []
    for p, ds, fs in os.walk(path):
        p = os.path.normcase(os.path.normpath(p))
        inc = False
        for i in include:
            i = os.path.normcase(os.path.normpath(i))
            if os.path.commonprefix([p, i]) == i:
                inc = True
                break
        if inc:
            for f in fs:
                ffp = os.path.join(p, f)
                datas.append((ffp, p))
    for f in include_files:
        if os.path.isfile(f):
            datas.append((f, os.path.normpath(os.path.dirname(f))))
    return datas


print(make_datas())
block_cipher = None


a = Analysis(['run_desktop.py'],
             pathex=['D:\\Game\\Develop\\Emoveo'],
             binaries=[],
             datas=make_datas(),
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
          [],
          exclude_binaries=True,
          name='Emoveo',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Emoveo')
