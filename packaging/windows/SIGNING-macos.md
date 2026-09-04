# Firma dell'installer Windows da macOS

Controparte macOS di [`SIGNING.md`](SIGNING.md) (che descrive il flusso da Windows con
`sign-release.ps1`). Usa questa pagina se firmi da un Mac con
[`sign-release-macos.sh`](sign-release-macos.sh) invece che da una macchina Windows.

## Perché serve uno script diverso

`sign-release.ps1` chiama `signtool.exe`, un binario Windows-only (si appoggia alle API
CryptoAPI/Authenticode del sistema) — non esiste una build macOS, quindi lo script non gira su
Mac nemmeno avendo PowerShell installato (PowerShell non è il problema). `sign-release-macos.sh`
ottiene lo stesso risultato con **[`osslsigncode`](https://github.com/mtrojnar/osslsigncode)**
(firma Authenticode basata su OpenSSL, multipiattaforma) che parla con la chiave cloud
SimplySign tramite un **motore PKCS#11**, senza bisogno di Windows.

A differenza di `sign-release.ps1` (che presuppone il draft della release già pronto),
`sign-release-macos.sh` **attende automaticamente** che la CI produca il draft con l'installer
non firmato (polling via `gh release view`), poi firma — così puoi lanciarlo subito dopo aver
pushato il tag e allontanarti, senza dover ricontrollare a mano quando la build su GitHub Actions
è finita.

## Setup one-time

1. **Installa SimplySign Desktop** per macOS (Certum offre client per Windows, macOS — Intel e
   Apple Silicon — e Linux). Avvialo e fai il primo login con le credenziali dell'account Certum
   + OTP dall'app mobile SimplySign, come su Windows (vedi `SIGNING.md`). Il modulo PKCS#11 viene
   installato in `/usr/local/lib/libSimplySignPKCS.dylib`.

2. **Installa i tool di firma via Homebrew**:

   ```bash
   brew install osslsigncode libp11 opensc gh
   ```

   - `osslsigncode` — firma Authenticode
   - `libp11` — fornisce l'engine PKCS#11 per OpenSSL (`engines-3/pkcs11.dylib`)
   - `opensc` — fornisce `pkcs11-tool`, usato una tantum sotto per individuare la chiave e
     esportare il certificato
   - `gh` — GitHub CLI (`gh auth login` se non già fatto)

3. **Individua l'URI PKCS#11 della chiave privata**, con SimplySign Desktop loggato:

   ```bash
   pkcs11-tool --module /usr/local/lib/libSimplySignPKCS.dylib -O
   ```

   Elenca gli oggetti sul token (certificato + chiave privata). Annota la label/ID dell'oggetto
   "Private Key" — ti servirà per costruire l'URI da passare come `PKCS11_KEY_URI`, tipicamente
   nella forma `pkcs11:object=<label>;type=private` (regola l'URI in base a cosa mostra realmente
   `pkcs11-tool` sul tuo token: label e ID possono variare).

4. **Esporta il certificato (+ catena) in PEM**, per il flag `-certs` di `osslsigncode`:

   ```bash
   pkcs11-tool --module /usr/local/lib/libSimplySignPKCS.dylib -r -y cert -o /tmp/cert.der
   openssl x509 -inform der -in /tmp/cert.der -out ~/.simplysign/cartellino-cert.pem
   ```

   Se il certificato del CA emittente (Certum) non è incluso e `osslsigncode verify` si lamenta
   della catena, scarica la catena intermedia dal
   [repository certificati Certum](https://www.certum.eu/en/repository/) e concatenala nello
   stesso file PEM.

   > **Verificato end-to-end su più release reali** (v3.2.0 e v3.3.0, da macOS): il certificato
   > esportato con `pkcs11-tool -r -y cert` contiene solo il certificato foglia, non la catena —
   > la firma riesce comunque, ma `osslsigncode verify` si lamenta di
   > `unable to get local issuer certificate` finché non si concatena nello stesso file PEM
   > l'intermedio "Certum Code Signing 2021 CA", scaricabile dall'URL `CA Issuers` indicato
   > nell'estensione Authority Information Access del certificato foglia
   > (`openssl x509 -in cert.pem -noout -text | grep -A3 "Authority Information Access"` —
   > tipicamente `http://repository.certum.pl/ccsca2021.cer`). Se `osslsigncode sign` fallisce con
   > un errore sui flag PKCS#11, controlla `osslsigncode --help` per i nomi esatti supportati dalla
   > versione installata (versioni più recenti usano `-pkcs11cert`/`-provider` invece di
   > `-certs`/`-pkcs11engine` per OpenSSL 3.x).

## Prerequisiti per ogni sessione di firma

- `osslsigncode`, `libp11`, `gh` installati (punto 2 sopra)
- SimplySign Desktop avviato e loggato (stesso avvertimento di `SIGNING.md`: la sessione OTP
  scade — se lo script fallisce sul modulo PKCS#11, riapri l'app e rifai il login)
- Variabili d'ambiente impostate (vedi sotto)

## Variabili d'ambiente

| Variabile | Obbligatoria | Default | Significato |
|---|:---:|---|---|
| `PKCS11_KEY_URI` | sì | — | URI PKCS#11 della chiave privata (punto 3 sopra) |
| `CERT_PEM_PATH` | sì | — | Percorso del certificato+catena esportato in PEM (punto 4 sopra) |
| `PKCS11_MODULE` | no | `/usr/local/lib/libSimplySignPKCS.dylib` | Percorso del modulo SimplySign |
| `PKCS11_ENGINE` | no | rilevato via `brew --prefix libp11` | Percorso dell'engine PKCS#11 di OpenSSL |
| `TSA_URL` | no | `http://time.certum.pl/` | Server di timestamp RFC3161 |
| `POLL_INTERVAL_SECONDS` | no | `30` | Intervallo di polling in attesa del draft |
| `POLL_TIMEOUT_MINUTES` | no | `60` | Timeout massimo di attesa del draft |

Come per `CERT_THUMBPRINT` in `SIGNING.md`: nessuno di questi valori è segreto (l'URI PKCS#11 e i
percorsi non contengono la chiave privata, che resta nell'HSM cloud di Certum), ma vanno comunque
tenuti fuori dai file versionati — impostali nel tuo shell profile (`~/.zshrc`) o esportali prima
di lanciare lo script.

## Procedura

Dopo aver pushato il tag della release:

```bash
export PKCS11_KEY_URI='pkcs11:object=<label-tua-chiave>;type=private'
export CERT_PEM_PATH=~/.simplysign/cartellino-cert.pem
./packaging/windows/sign-release-macos.sh --tag v3.0.0
```

Lo script:

1. verifica i prerequisiti;
2. **attende** (polling) che la CI completi la build e pubblichi il draft della release con
   l'installer `.exe` tra gli asset — puoi lanciarlo subito dopo il push del tag e allontanarti;
3. scarica l'asset, lo firma con `osslsigncode` + PKCS#11, verifica la firma;
4. aggiorna `SHA256SUMS` se presente tra gli asset;
5. ricarica gli asset firmati sulla draft (che resta in draft).

Quando sei soddisfatto, ripeti con `--publish` per pubblicare:

```bash
./packaging/windows/sign-release-macos.sh --tag v3.0.0 --publish
```

Se ometti `--tag`, lo script usa l'ultimo tag Git locale (`git describe --tags --abbrev=0`) —
verifica comunque che corrisponda al tag giusto prima di procedere.
