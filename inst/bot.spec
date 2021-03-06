# -*- mode: python -*-
import os
import sys

# In case of problems set `debug` to `True`
debug = False

upx = not debug
exe_options = [('v', None, 'OPTION')] if debug else []

proj_name = 'bot'
exe_name = 'bot'
block_cipher = None

modules = [
    '../bot/__main__.py',
]

hidden_imports = [
    'bot.service',  # PyInstaller cannot detect a module imported from within a function.
]

a = Analysis(
    modules,
    pathex=[],
    binaries=None,
    datas=None,
    hiddenimports=hidden_imports,
    hookspath=['./inst/hooks'],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    exe_options,
    exclude_binaries=True,
    name=exe_name,
    debug=debug,
    strip=False,
    upx=upx,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=upx,
    name=proj_name
)
