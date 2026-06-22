#!/bin/bash
# Gera o app "Roleta de Filmes.app" e um instalador .dmg.
# Uso:  ./build_app.sh
set -e

cd "$(dirname "$0")"
APP_NAME="Roleta de Filmes"

echo "==> Ativando ambiente virtual"
source .venv/bin/activate

echo "==> Instalando PyInstaller (se necessário)"
pip install -q --upgrade pyinstaller pillow

echo "==> Limpando builds anteriores"
rm -rf build dist "${APP_NAME}.dmg"

echo "==> Empacotando o .app"
pyinstaller roleta.spec --noconfirm

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
  echo "ERRO: $APP_PATH não foi criado."; exit 1
fi

echo "==> Montando estrutura do DMG"
STAGING="dist/dmg"
rm -rf "$STAGING"; mkdir -p "$STAGING"
cp -R "$APP_PATH" "$STAGING/"
ln -s /Applications "$STAGING/Applications"   # atalho para arrastar

echo "==> Criando o .dmg"
hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$STAGING" \
  -ov -format UDZO \
  "${APP_NAME}.dmg"

rm -rf "$STAGING"
echo ""
echo "✅ Pronto!"
echo "   App:  $APP_PATH"
echo "   DMG:  $(pwd)/${APP_NAME}.dmg"
