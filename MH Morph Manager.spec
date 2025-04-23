# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\shina\\OneDrive\\Documents\\GitHub\\MH-Morph-Manager\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\shina\\OneDrive\\Documents\\GitHub\\MH-Morph-Manager\\app.ico', '.'), ('C:\\Users\\shina\\OneDrive\\Documents\\GitHub\\MH-Morph-Manager\\Morphs.txt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MH Morph Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\shina\\OneDrive\\Documents\\GitHub\\MH-Morph-Manager\\app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MH Morph Manager',
)
