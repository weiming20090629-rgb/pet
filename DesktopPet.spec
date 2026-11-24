# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ("assets", "assets"),
    ("src/*.py", "src"),
]
binaries = []

hiddenimports = [
    "src",
    "src.path_utils",
    "src.pet_actions",
    "src.pet_animation",
    "src.pet_menu",
    "src.pet_monitors",
    "src.pet_mouse_handler",
    "src.pet_shop",
    "src.pet_stock",
    "src.pet_voice",
    "src.pet_window",
    "src.punishment",
    "src.styles",
    "src.workers",
    'src.stockfish_engine',
    'src.chess_dialog',
    'chess',
    'chess.engine'
]

for pkg in ("yfinance", "gtts", "miniaudio"):
    pkg_datas, pkg_bins, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_bins
    hiddenimports += pkg_hidden

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('src/*.py', 'src'),
    ],
    hiddenimports=[
        'chess',
        'chess.engine',
    ],
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
    name="DesktopPet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 先開 console 方便看錯誤訊息，成功後再改回 False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DesktopPet",
)