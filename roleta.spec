# -*- mode: python ; coding: utf-8 -*-
# Empacota a Roleta de Filmes.
#   macOS:   pyinstaller roleta.spec --noconfirm   -> dist/Roleta de Filmes.app
#   Windows: pyinstaller roleta.spec --noconfirm   -> dist/Roleta de Filmes.exe (onefile)

import os
import sys

from PyInstaller.utils.hooks import collect_all

IS_WIN = sys.platform == "win32"

# Coleta de submódulos. No Windows o pywebview usa WebView2 (pythonnet/clr);
# no macOS usa pyobjc (objc/Foundation/WebKit/AppKit/Quartz).
datas, binaries, hiddenimports = [], [], []
pkgs = ("webview",) if IS_WIN else (
    "webview", "objc", "Foundation", "WebKit", "AppKit", "Quartz",
)
for pkg in pkgs:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

if IS_WIN:
    # Backend do pywebview no Windows.
    hiddenimports += ["clr", "clr_loader", "webview.platforms.edgechromium"]

# Recursos da aplicação (somente leitura dentro do pacote).
datas += [
    ("web", "web"),
    ("filmes_iniciais.rtf", "."),
]
# .env empacotado só se existir (em CI normalmente não existe — o app também lê
# um .env da pasta de dados do usuário).
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

if IS_WIN:
    # Onefile: um único .exe.
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="Roleta de Filmes",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        icon="build_assets/icon.ico",
    )
else:
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
