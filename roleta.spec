# -*- mode: python ; coding: utf-8 -*-
# Empacota a Roleta de Filmes num .app do macOS.
# Build:  pyinstaller roleta.spec --noconfirm

from PyInstaller.utils.hooks import collect_all

# pywebview e pyobjc precisam ter seus submódulos coletados explicitamente.
datas, binaries, hiddenimports = [], [], []
for pkg in ("webview", "objc", "Foundation", "WebKit", "AppKit", "Quartz"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Recursos da aplicação (somente leitura dentro do .app).
datas += [
    ("web", "web"),
    ("filmes_iniciais.rtf", "."),
]
# .env empacotado como fallback (o app também lê um .env da pasta de dados do usuário).
import os
if os.path.exists(".env"):
    datas += [(".env", ".")]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
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
    name="Roleta de Filmes",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name="Roleta de Filmes",
)

app = BUNDLE(
    coll,
    name="Roleta de Filmes.app",
    icon="build_assets/icon.icns",
    bundle_identifier="com.ana.roletadefilmes",
    info_plist={
        "CFBundleName": "Roleta de Filmes",
        "CFBundleDisplayName": "Roleta de Filmes",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.entertainment",
    },
)
