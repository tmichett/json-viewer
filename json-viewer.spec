# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for JSON Viewer desktop app."""

import platform

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

pyqt_datas, pyqt_binaries, pyqt_hiddenimports = collect_all("PyQt6")
pygments_hiddenimports = collect_submodules("pygments")
yaml_hiddenimports = collect_submodules("yaml")

hiddenimports = (
    pyqt_hiddenimports
    + pygments_hiddenimports
    + yaml_hiddenimports
    + ["defusedxml", "defusedxml.ElementTree", "json_viewer", "PyQt6.QtSvg"]
)

a = Analysis(
    ["src/json_viewer/__main__.py"],
    pathex=["src"],
    binaries=pyqt_binaries,
    datas=pyqt_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="json-viewer",
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="json-viewer",
)

if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name="JSON Viewer.app",
        icon=None,
        bundle_identifier="com.jsonviewer.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleDisplayName": "JSON Viewer",
        },
    )
