# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['skills/company-filter-refresh/refresh.py'],
    pathex=[],
    binaries=[],
    datas=[('skills/company-filter/data', 'seed_data')],
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
    name='Charlie Skill',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Charlie Skill',
)
app = BUNDLE(
    coll,
    name='Charlie Skill.app',
    icon=None,
    bundle_identifier=None,
)
