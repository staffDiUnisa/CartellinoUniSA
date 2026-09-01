#!/bin/bash
# Test locale della fase macOS del job "build" in .github/workflows/release.yml
# (firma, notarizzazione, .app launcher, .pkg) — pensato per intercettare i
# problemi di firma/notarizzazione PRIMA di taggare una release (quella che in
# genere dà più grattacapi), senza dover passare da un tag -rcN + push.
#
# Differenze rispetto alla CI (deliberate, solo per l'uso locale):
# - Niente import di secrets/Certificates.p12 / secrets/Installer_Certificates.p12:
#   i certificati "Developer ID Application"/"Developer ID Installer" sono già
#   nel login keychain di chi lancia lo script (verificato con
#   `security find-identity`), quindi si firma direttamente con quelli.
# - Notarizzazione via `--keychain-profile "$NOTARY_PROFILE"` (creato una tantum con
#   `xcrun notarytool store-credentials`), non `--apple-id/--password/--team-id`
#   letti da variabili in chiaro: niente credenziali su disco né in questo script.
# - Output in build/local-macos-test/ (gitignored, come build/ e dist/), non
#   pubblicato da nessuna parte.
#
# Uso: packaging/local_test_macos_release.sh
# Richiede: macOS, i tool Apple (codesign/xcrun/pkgbuild/osacompile/security),
# jq, e un profilo notarytool già configurato (vedi NOTARY_PROFILE sotto).

set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Questo script gira solo su macOS." >&2
    exit 1
fi

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

NOTARY_PROFILE="${NOTARY_PROFILE:-cartellino-notary}"
SIGN_APP_IDENTITY="Developer ID Application"
SIGN_INSTALLER_IDENTITY="Developer ID Installer"
VERSION="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"
OUT_DIR="build/local-macos-test"

echo "==> Versione: $VERSION"
echo "==> Profilo notarytool: $NOTARY_PROFILE"

if ! xcrun notarytool history --keychain-profile "$NOTARY_PROFILE" >/dev/null 2>&1; then
    echo "Profilo notarytool '$NOTARY_PROFILE' non trovato o non valido. Crealo con:" >&2
    echo "  xcrun notarytool store-credentials \"$NOTARY_PROFILE\" --apple-id <email> --team-id <TEAMID> --password <password-per-app>" >&2
    exit 1
fi

for identity in "$SIGN_APP_IDENTITY" "$SIGN_INSTALLER_IDENTITY"; do
    if ! security find-identity -v | grep -q "\"$identity:"; then
        echo "Identità '$identity' non trovata nel keychain. Verifica con: security find-identity -v" >&2
        exit 1
    fi
done

notarize_and_check() {
    # $1 = percorso file/zip da inviare, $2 = etichetta per i log
    local target="$1" label="$2" result_json
    result_json="$(mktemp)"
    xcrun notarytool submit "$target" \
        --keychain-profile "$NOTARY_PROFILE" \
        --wait \
        --output-format json | tee "$result_json"
    local submission_id status
    submission_id=$(jq -r '.id' "$result_json")
    status=$(jq -r '.status' "$result_json")
    echo "Notarizzazione '$label': status=$status id=$submission_id"
    if [[ "$status" != "Accepted" ]]; then
        echo "--- Log dettagliato Apple (xcrun notarytool log) ---"
        xcrun notarytool log "$submission_id" --keychain-profile "$NOTARY_PROFILE" || true
        echo "::error:: Notarizzazione '$label' non accettata da Apple (status: $status)" >&2
        rm -f "$result_json"
        exit 1
    fi
    rm -f "$result_json"
}

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

echo "==> uv sync --group build"
uv sync --group build

echo "==> Genero le icone da resources/logo.png"
uv run python packaging/generate_icons.py
ICONSET=packaging/build/icon.iconset
rm -rf "$ICONSET"
mkdir -p "$ICONSET"
sips -z 16 16     resources/logo.png --out "$ICONSET/icon_16x16.png" >/dev/null
sips -z 32 32     resources/logo.png --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 32 32     resources/logo.png --out "$ICONSET/icon_32x32.png" >/dev/null
sips -z 64 64     resources/logo.png --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 128 128   resources/logo.png --out "$ICONSET/icon_128x128.png" >/dev/null
sips -z 256 256   resources/logo.png --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256   resources/logo.png --out "$ICONSET/icon_256x256.png" >/dev/null
sips -z 512 512   resources/logo.png --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512   resources/logo.png --out "$ICONSET/icon_512x512.png" >/dev/null
sips -z 1024 1024 resources/logo.png --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o packaging/build/icon.icns

echo "==> pyinstaller packaging/cartellino.spec"
uv run pyinstaller packaging/cartellino.spec --noconfirm

echo "==> Firmo tutti i Mach-O in dist/cartellino-unisa"
find dist/cartellino-unisa -type f -print0 | while IFS= read -r -d '' f; do
    if file "$f" | grep -q "Mach-O"; then
        codesign --force --timestamp --options runtime \
            --entitlements packaging/entitlements.plist \
            --sign "$SIGN_APP_IDENTITY" "$f"
    fi
done
codesign --force --timestamp --options runtime \
    --entitlements packaging/entitlements.plist \
    --sign "$SIGN_APP_IDENTITY" \
    dist/cartellino-unisa/cartellino-unisa
codesign --force --timestamp --options runtime \
    --entitlements packaging/entitlements.plist \
    --sign "$SIGN_APP_IDENTITY" \
    dist/cartellino-unisa/cartellino-unisa-gui
codesign --verify --deep --strict --verbose=2 dist/cartellino-unisa/cartellino-unisa
codesign --verify --deep --strict --verbose=2 dist/cartellino-unisa/cartellino-unisa-gui

echo "==> Costruisco e firmo il launcher TUI .app"
rm -rf "build/Cartellino UniSA (Terminale).app"
osacompile -o "build/Cartellino UniSA (Terminale).app" packaging/macos/launcher.applescript
cp packaging/build/icon.icns "build/Cartellino UniSA (Terminale).app/Contents/Resources/applet.icns"
rm -f "build/Cartellino UniSA (Terminale).app/Contents/Resources/Assets.car"
PLIST="build/Cartellino UniSA (Terminale).app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$PLIST" || true
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier org.antaresnet.cartellino-unisa.launcher.terminale" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string org.antaresnet.cartellino-unisa.launcher.terminale" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleName Cartellino UniSA (Terminale)" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleName string Cartellino UniSA (Terminale)" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName Cartellino UniSA (Terminale)" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string Cartellino UniSA (Terminale)" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$PLIST"
codesign --force --timestamp --options runtime \
    --entitlements packaging/macos/launcher-entitlements.plist \
    --sign "$SIGN_APP_IDENTITY" \
    "build/Cartellino UniSA (Terminale).app"
codesign --verify --deep --strict --verbose=2 "build/Cartellino UniSA (Terminale).app"

echo "==> Costruisco e firmo il launcher GUI .app"
rm -rf "build/Cartellino UniSA.app"
cp -R "dist/Cartellino UniSA.app" "build/Cartellino UniSA.app"
PLIST="build/Cartellino UniSA.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $VERSION" "$PLIST"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$PLIST" \
    || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $VERSION" "$PLIST"
codesign --force --deep --timestamp --options runtime \
    --entitlements packaging/entitlements.plist \
    --sign "$SIGN_APP_IDENTITY" \
    "build/Cartellino UniSA.app"
codesign --verify --deep --strict --verbose=2 "build/Cartellino UniSA.app"

echo "==> Notarizzo e staplo i due launcher .app"
for app in "Cartellino UniSA (Terminale).app" "Cartellino UniSA.app"; do
    zip_name=$(echo "$app" | tr -c '[:alnum:]' '_')
    ditto -c -k --keepParent "build/$app" "$OUT_DIR/${zip_name}.zip"
    notarize_and_check "$OUT_DIR/${zip_name}.zip" "$app"
    xcrun stapler staple "build/$app"
    spctl -a -vvv "build/$app" || echo "::warning:: spctl non ha accettato '$app' (vedi output sopra)"
done

echo "==> Notarizzo l'eseguibile onedir (nessuno staple: formato non supportato)"
ditto -c -k --keepParent dist/cartellino-unisa "$OUT_DIR/notarize.zip"
notarize_and_check "$OUT_DIR/notarize.zip" "cartellino-unisa (onedir)"

echo "==> Costruisco, firmo e notarizzo il .pkg"
chmod +x packaging/macos/postinstall
rm -rf "$OUT_DIR/pkgroot"
mkdir -p "$OUT_DIR/pkgroot/usr/local/cartellino-unisa"
mkdir -p "$OUT_DIR/pkgroot/Applications"
cp -R dist/cartellino-unisa/. "$OUT_DIR/pkgroot/usr/local/cartellino-unisa/"
cp -R "build/Cartellino UniSA (Terminale).app" "$OUT_DIR/pkgroot/Applications/Cartellino UniSA (Terminale).app"
cp -R "build/Cartellino UniSA.app" "$OUT_DIR/pkgroot/Applications/Cartellino UniSA.app"

pkgbuild \
    --root "$OUT_DIR/pkgroot" \
    --install-location / \
    --scripts packaging/macos \
    --identifier org.antaresnet.cartellino-unisa \
    --version "$VERSION" \
    --sign "$SIGN_INSTALLER_IDENTITY" \
    "$OUT_DIR/cartellino-unisa.pkg"

notarize_and_check "$OUT_DIR/cartellino-unisa.pkg" "cartellino-unisa.pkg"
xcrun stapler staple "$OUT_DIR/cartellino-unisa.pkg"
spctl -a -vvv --type install "$OUT_DIR/cartellino-unisa.pkg" || echo "::warning:: spctl non ha accettato il .pkg (vedi output sopra)"

echo ""
echo "==> Fatto. Output in $OUT_DIR/:"
ls -la "$OUT_DIR"
echo ""
echo "Puoi installare il .pkg per una prova reale con:"
echo "  sudo installer -pkg \"$OUT_DIR/cartellino-unisa.pkg\" -target /"
