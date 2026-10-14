# -*- mode: python ; coding: utf-8 -*-
# Empacota a Roleta de Filmes.
# Rode a partir da raiz do projeto:
#   macOS:   pyinstaller packaging/roleta.spec --noconfirm   -> dist/Roleta de Filmes.app
#   Windows: pyinstaller packaging/roleta.spec --noconfirm   -> dist/Roleta de Filmes.exe (onefile)

import os
import sys

from PyInstaller.utils.hooks import collect_all

IS_WIN = sys.platform == "win32"
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # SPECPATH é definido pelo PyInstaller
PKG = os.path.join(ROOT, "roleta_de_filmes")
ASSETS = os.path.join(SPECPATH, "assets")

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
    (os.path.join(PKG, "web"), "roleta_de_filmes/web"),
    (os.path.join(PKG, "data"), "roleta_de_filmes/data"),
]
# A chave do TMDB NUNCA é embutida no pacote: o app lê o .env da pasta de dados
# do usuário (veja o README).

a = Analysis(
    [os.path.join(ROOT, "run.py")],
    pathex=[ROOT],
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
        icon=os.path.join(ASSETS, "icon.ico"),
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
        icon=os.path.join(ASSETS, "icon.icns"),
        bundle_identifier="com.roletadefilmes.app",
        info_plist={
            "CFBundleName": "Roleta de Filmes",
            "CFBundleDisplayName": "Roleta de Filmes",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.entertainment",
        },
    )
