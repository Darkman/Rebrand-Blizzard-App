# -*- mode: python -*-

block_cipher = None

added_files = [
    ('./rebrand-blizzard-app/MPQEditor.exe', '.'),
    ('./rebrand-blizzard-app/logs/log_config.yaml', 'logs'),
    ('./rebrand-blizzard-app/resources', 'resources')
]

a = Analysis(
    ['.\\rebrand-blizzard-app\\rebrand-blizzard-app.py'],
    pathex=['E:\\High Priority\\Low Volume\\Projects\\Python\\Code\\Rebrand-Blizzard-App\\PyInstaller'],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
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
    exclude_binaries=True,
    name='rebrand-blizzard-app',
    debug=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='rebrand-blizzard-app'
)
