# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "config.example.json"), "."),
        (str(ROOT / "system_prompt.txt"), "."),
        (str(ROOT / "plugins_user" / "hello.py"), "plugins_user"),
    ],
    hiddenimports=[
        "pocket_agent",
        "pocket_agent.gui",
        "pocket_agent.agent",
        "pocket_agent.client",
        "pocket_agent.config",
        "pocket_agent.paths",
        "pocket_agent.plugins.loader",
        "pocket_agent.plugins.builtin.echo",
        "pocket_agent.plugins.builtin.time",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PocketAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="PocketAgent",
)
