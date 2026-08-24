# PyInstaller spec for "Zaria Crop ET and Irrigation DSS"
# Build with:  pyinstaller zaria_dss.spec
#
# Produces a standalone desktop app (no Python installation required to run it) with
# the app's logo as the window/taskbar icon. Build ONCE ON EACH TARGET OS you want to
# ship for -- PyInstaller does not cross-compile (build on Windows for a .exe, on
# macOS for a .app, on Linux for a Linux binary).

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Bundle everything the app reads from disk at runtime: the maize training CSV,
# the author photo, and the generated icon files.
datas = [
    ("data", "data"),
    ("assets", "assets"),
]

if sys.platform == "darwin":
    icon_file = "assets/icons/app_icon.icns"
elif sys.platform.startswith("win"):
    icon_file = "assets/icons/app_icon.ico"
else:
    icon_file = None  # Linux: PyInstaller doesn't embed a binary icon; we set it at
                       # runtime via _set_app_icon() in gui.py, and desktop launchers
                       # (see zaria-dss.desktop) point directly at the PNG instead.

a = Analysis(
    ["gui.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=["docx", "PIL", "PIL._tkinter_finder"],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ZariaCropETIrrigationDSS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=(sys.platform == "darwin"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="ZariaCropETIrrigationDSS.app",
        icon=icon_file,
        bundle_identifier="ng.zaria.cropetirrigationdss",
        info_plist={
            "CFBundleName": "Zaria Crop ET and Irrigation DSS",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
