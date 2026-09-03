#!/usr/bin/env bash
#
# Attende che la CI abbia prodotto il draft di una release (con l'installer
# .exe di Windows non firmato tra gli asset), poi lo firma in locale da
# macOS con il certificato Certum SimplySign Open Source Code Signing,
# tramite osslsigncode + motore PKCS#11 (equivalente macOS di
# sign-release.ps1, che su Windows usa signtool.exe — non disponibile su
# macOS). Vedi packaging/windows/SIGNING-macos.md per il setup one-time e i
# prerequisiti.
#
# Uso:
#   ./packaging/windows/sign-release-macos.sh [--tag vX.Y.Z] [--publish]
#
# Se --tag e' omesso, usa l'ultimo tag Git locale (git describe --tags
# --abbrev=0). Senza --publish la release resta in draft per un controllo
# manuale finale.
#
# Variabili d'ambiente richieste (vedi SIGNING-macos.md per come ottenerle):
#   PKCS11_KEY_URI     URI PKCS#11 della chiave privata sul token SimplySign
#                       (es. "pkcs11:object=mio-oggetto;type=private")
#   CERT_PEM_PATH       percorso del certificato (+ catena) esportato in PEM
#
# Variabili d'ambiente opzionali (hanno un default ragionevole):
#   PKCS11_MODULE       default: /usr/local/lib/libSimplySignPKCS.dylib
#   PKCS11_ENGINE        default: rilevato via `brew --prefix libp11`
#   TSA_URL              default: http://time.certum.pl/
#   POLL_INTERVAL_SECONDS  default: 30
#   POLL_TIMEOUT_MINUTES   default: 60

set -euo pipefail

TAG=""
PUBLISH=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --publish)
            PUBLISH=1
            shift
            ;;
        *)
            echo "Argomento sconosciuto: $1" >&2
            exit 1
            ;;
    esac
done

step() { printf '\033[36m==> %s\033[0m\n' "$1"; }
info() { printf '%s\n' "$1"; }
ok()   { printf '\033[32m%s\033[0m\n' "$1"; }
warn() { printf '\033[33m%s\033[0m\n' "$1"; }
fail() { printf '\033[31mERRORE: %s\033[0m\n' "$1" >&2; exit 1; }

# --- 1. Prerequisiti -----------------------------------------------------

step "Verifica prerequisiti"

command -v osslsigncode >/dev/null 2>&1 || fail "osslsigncode non trovato. Installa con: brew install osslsigncode"
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) non trovato. Installa con: brew install gh"

if ! gh auth status >/dev/null 2>&1; then
    fail "GitHub CLI non autenticato. Esegui 'gh auth login' prima di continuare."
fi

PKCS11_MODULE="${PKCS11_MODULE:-/usr/local/lib/libSimplySignPKCS.dylib}"
[[ -f "$PKCS11_MODULE" ]] || fail "Modulo PKCS#11 SimplySign non trovato in $PKCS11_MODULE. Verifica che SimplySign Desktop sia installato e loggato (vedi SIGNING-macos.md), oppure imposta PKCS11_MODULE se il percorso e' diverso."

if [[ -z "${PKCS11_ENGINE:-}" ]]; then
    if command -v brew >/dev/null 2>&1 && brew --prefix libp11 >/dev/null 2>&1; then
        PKCS11_ENGINE="$(brew --prefix libp11)/lib/engines-3/pkcs11.dylib"
    fi
fi
[[ -n "${PKCS11_ENGINE:-}" ]] || fail "PKCS11_ENGINE non impostato e non rilevabile automaticamente. Installa con: brew install libp11, oppure imposta PKCS11_ENGINE esplicitamente."
[[ -f "$PKCS11_ENGINE" ]] || fail "PKCS11_ENGINE punta a un file inesistente: $PKCS11_ENGINE"

[[ -n "${CERT_PEM_PATH:-}" ]] || fail "CERT_PEM_PATH non impostato (percorso del certificato+catena esportato in PEM). Vedi SIGNING-macos.md."
[[ -f "$CERT_PEM_PATH" ]] || fail "CERT_PEM_PATH punta a un file inesistente: $CERT_PEM_PATH"

[[ -n "${PKCS11_KEY_URI:-}" ]] || fail "PKCS11_KEY_URI non impostato (URI PKCS#11 della chiave privata). Vedi SIGNING-macos.md."

TSA_URL="${TSA_URL:-http://time.certum.pl/}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-30}"
POLL_TIMEOUT_MINUTES="${POLL_TIMEOUT_MINUTES:-60}"

ok "Prerequisiti OK (modulo: $PKCS11_MODULE, engine: $PKCS11_ENGINE)"

# --- 2. Determina il tag ---------------------------------------------------

if [[ -z "$TAG" ]]; then
    step "Nessun tag specificato, rilevo l'ultimo tag locale"
    TAG="$(git describe --tags --abbrev=0)" || fail "Impossibile determinare automaticamente il tag. Specifica --tag esplicitamente."
    ok "Tag rilevato: $TAG"
fi

# --- 3. Attende il draft della release con l'asset .exe ---------------------

step "Attendo che la CI produca il draft della release $TAG con l'installer .exe (poll ogni ${POLL_INTERVAL_SECONDS}s, timeout ${POLL_TIMEOUT_MINUTES}min)"

deadline=$(( $(date +%s) + POLL_TIMEOUT_MINUTES * 60 ))
asset_name=""
while true; do
    if assets_json="$(gh release view "$TAG" --json assets,isDraft 2>/dev/null)"; then
        asset_name="$(echo "$assets_json" | python3 -c '
import json, sys
data = json.load(sys.stdin)
for a in data.get("assets", []):
    if a["name"].startswith("cartellino-unisa-setup-") and a["name"].endswith(".exe"):
        print(a["name"])
        break
')"
        if [[ -n "$asset_name" ]]; then
            ok "Draft trovato con asset: $asset_name"
            break
        fi
        info "Release $TAG trovata ma l'asset .exe non e' ancora presente, riprovo..."
    else
        info "Release $TAG non ancora disponibile, riprovo..."
    fi

    if (( $(date +%s) >= deadline )); then
        fail "Timeout: dopo ${POLL_TIMEOUT_MINUTES} minuti la release $TAG non ha ancora l'asset .exe. Controlla lo stato della CI su GitHub Actions."
    fi
    sleep "$POLL_INTERVAL_SECONDS"
done

# --- 4. Scarica l'asset non firmato ------------------------------------------

step "Scarico $asset_name"

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/cartellino-sign-${TAG}.XXXXXX")"
trap 'rm -rf "$work_dir"' EXIT

gh release download "$TAG" --dir "$work_dir" --pattern "$asset_name" \
    || fail "Download dell'asset .exe fallito."

exe_path="$work_dir/$asset_name"
[[ -f "$exe_path" ]] || fail "Asset scaricato ma non trovato in $exe_path."

ok "Asset scaricato: $exe_path"

# --- 5. Firma con osslsigncode + PKCS#11 -------------------------------------

step "Firmo $asset_name con osslsigncode"

signed_path="$work_dir/signed-$asset_name"

osslsigncode sign \
    -pkcs11engine "$PKCS11_ENGINE" \
    -pkcs11module "$PKCS11_MODULE" \
    -certs "$CERT_PEM_PATH" \
    -key "$PKCS11_KEY_URI" \
    -h sha256 \
    -n "Cartellino UniSA" \
    -i "https://github.com/staffDiUnisa/CartellinoUniSA" \
    -t "$TSA_URL" \
    -in "$exe_path" \
    -out "$signed_path" \
    || fail "osslsigncode sign ha restituito un errore. Se il tuo osslsigncode e' una versione recente, i flag potrebbero essere cambiati (-pkcs11cert invece di -certs, -provider invece di -pkcs11engine per OpenSSL 3.x) — vedi 'osslsigncode --help' e SIGNING-macos.md."

[[ -f "$signed_path" ]] || fail "osslsigncode non ha prodotto il file firmato atteso."

# --- 6. Verifica la firma -----------------------------------------------------

step "Verifico la firma"

osslsigncode verify -in "$signed_path" || fail "osslsigncode verify ha fallito: la firma non risulta valida."

ok "Firma verificata con successo."

mv "$signed_path" "$exe_path"

# --- 7. Aggiorna SHA256SUMS se presente tra gli asset -------------------------

step "Controllo SHA256SUMS tra gli asset della release"

sums_path="$work_dir/SHA256SUMS"
gh release download "$TAG" --dir "$work_dir" --pattern "SHA256SUMS" 2>/dev/null || true

if [[ -f "$sums_path" ]]; then
    new_hash="$(shasum -a 256 "$exe_path" | awk '{print $1}')"
    tmp_sums="$(mktemp)"
    while IFS= read -r line; do
        if [[ "$line" == *"$asset_name"* ]]; then
            printf '%s  %s\n' "$new_hash" "$asset_name" >> "$tmp_sums"
        else
            printf '%s\n' "$line" >> "$tmp_sums"
        fi
    done < "$sums_path"
    mv "$tmp_sums" "$sums_path"
    ok "SHA256SUMS aggiornato con il nuovo hash del file firmato."
else
    warn "Nessun file SHA256SUMS trovato tra gli asset, salto questo step."
fi

# --- 8. Ricarica gli asset firmati sulla draft ---------------------------------

step "Carico gli asset firmati sulla draft release $TAG"

gh release upload "$TAG" "$exe_path" --clobber || fail "Upload dell'exe firmato fallito."

if [[ -f "$sums_path" ]]; then
    gh release upload "$TAG" "$sums_path" --clobber || fail "Upload di SHA256SUMS aggiornato fallito."
fi

ok "Asset firmati caricati sulla draft release $TAG."

# --- 9. Pubblica se richiesto ---------------------------------------------------

if [[ "$PUBLISH" -eq 1 ]]; then
    step "Pubblico la release $TAG (rimuovo lo stato draft)"
    gh release edit "$TAG" --draft=false || fail "Pubblicazione della release fallita."
    ok "Release $TAG pubblicata."
else
    echo ""
    warn "La release $TAG resta in DRAFT. Verifica manualmente gli asset firmati, poi rilancia con --publish per pubblicare."
fi
