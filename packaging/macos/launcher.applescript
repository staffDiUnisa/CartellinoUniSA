-- Cartellino UniSA — avvia il terminale scelto dall'utente ed esegue la CLI/TUI.
--
-- Percorso assoluto invece del comando dal PATH: un terminale appena aperto da
-- Finder potrebbe non aver ancora ricaricato un PATH modificato di recente
-- (stesso problema di profili shell che sovrascrivono PATH, già documentato in
-- README.md per l'uso da riga di comando).
set cliPath to "/usr/local/cartellino-unisa/cartellino-unisa"

-- File di stato condiviso con cartellino/tui/macos_terminal.py (stessa cartella
-- di config.toml, file separato): una riga col bundle id del terminale scelto.
-- Vive fuori da config.toml perché questo script gira prima di qualunque cosa
-- Python, quindi prima dell'onboarding.
set choiceDir to (POSIX path of (path to application support from user domain)) & "cartellino-unisa/"
set choiceFile to choiceDir & "macos_terminal.txt"

on readSavedBundleId(choiceFile)
	try
		set fileRef to open for access (POSIX file choiceFile)
		set content to (read fileRef)
		close access fileRef
		set AppleScript's text item delimiters to {return, linefeed, " ", tab}
		set content to (text items of content) as text
		set AppleScript's text item delimiters to ""
		return content
	on error
		try
			close access (POSIX file choiceFile)
		end try
		return ""
	end try
end readSavedBundleId

on writeSavedBundleId(choiceDir, choiceFile, bundleId)
	do shell script "mkdir -p " & quoted form of choiceDir
	try
		set fileRef to open for access (POSIX file choiceFile) with write permission
		set eof of fileRef to 0
		write bundleId to fileRef
		close access fileRef
	on error
		try
			close access (POSIX file choiceFile)
		end try
	end try
end writeSavedBundleId

on appIsInstalled(appPath)
	return (do shell script "test -e " & quoted form of appPath & " && echo 1 || echo 0") is "1"
end appIsInstalled

on indexOfItem(theItem, theList)
	repeat with i from 1 to count of theList
		if item i of theList is theItem then return i
	end repeat
	return 0
end indexOfItem

-- Terminal.app: `do script` restituisce un riferimento diretto alla tab aperta,
-- quindi il polling su `busy` è preciso (chiude esattamente quella finestra,
-- non "una finestra Terminal.app qualunque" se l'utente sposta il focus altrove
-- nel frattempo). `bounds` impostato a un rettangolo volutamente più grande
-- dello schermo reale è un trucco per "massimizzare" senza dover chiedere un
-- secondo permesso Automazione solo per interrogare Finder/System Events sulla
-- risoluzione: il window server clippa comunque alle dimensioni reali.
on launchInTerminalApp(cliPath)
	tell application id "com.apple.Terminal"
		activate
		if not (exists window 1) then
			set t to do script cliPath
		else
			set t to do script cliPath in window 1
		end if
		set bounds of front window to {0, 0, 4000, 4000}
		repeat while busy of t
			delay 1
		end repeat
		close (front window)
	end tell
end launchInTerminalApp

-- Ghostty e iTerm2: la loro terminologia AppleScript (comandi come "new window
-- with configuration" o "create window with default profile command") NON è
-- parte della Standard Suite — `osacompile` deve poterla risolvere AL MOMENTO
-- DELLA COMPILAZIONE per qualunque `tell application id "..." to <comando
-- specifico dell'app>` scritto direttamente in questo file. Il runner CI
-- (`macos-latest` su GitHub Actions) NON ha né Ghostty né iTerm2 installati —
-- solo Terminal.app (app di sistema, sempre presente) può essere indirizzata
-- direttamente come sopra. Per questo i blocchi Ghostty/iTerm2 costruiscono il
-- proprio codice come STRINGA ed eseguono con `run script`: la risoluzione
-- della terminologia avviene così solo a runtime, sulla macchina dell'utente
-- finale (che avrà scelto quell'app solo se installata). Verificato: un file
-- che referenzia Ghostty/iTerm2 solo dentro `run script` compila con
-- `osacompile` anche senza quelle app installate.

-- Ghostty (AppleScript in preview da v1.3, soggetto a modifiche in v1.4): la sua
-- API non espone alcuna proprietà "busy"/di stato del processo in esecuzione,
-- quindi l'unico modo per chiudere la finestra a fine esecuzione è appendere la
-- chiusura alla riga di comando stessa. Limite noto e accettato: "close window
-- (front window)" chiude "la finestra Ghostty frontmost", non necessariamente
-- quella aperta qui, se un'altra finestra Ghostty diventa frontmost nel
-- frattempo — non risolvibile con l'API attuale (nessun riferimento diretto
-- alla finestra sopravvive al processo shell che esegue il comando). Sintassi
-- verificata a mano (`sdef`/`osascript`) su Ghostty 1.3 realmente installato:
-- il dizionario NON ha un comando "do script" atomico né un verbo
-- "toggle_fullscreen" come tale — si usa "new window with configuration"
-- (record "surface configuration", proprietà "initial input" = testo inviato
-- al terminale come se digitato) e il comando generico "perform action"
-- (accetta qualunque azione/keybind Ghostty come stringa, qui
-- "toggle_fullscreen", applicata a un "terminal", non a una "window" —
-- ottenuto da "focused terminal of (selected tab of <window>)").
on launchInGhostty(cliPath)
	set selfCloseCmd to cliPath & "; osascript -e 'tell application id \"com.mitchellh.ghostty\" to close window (front window)'" & return
	set ghosttyScript to "on run {inputText}
	tell application id \"com.mitchellh.ghostty\"
		activate
		set newWin to new window with configuration {initial input:inputText}
		set theTerminal to focused terminal of (selected tab of newWin)
		perform action \"toggle_fullscreen\" on theTerminal
	end tell
end run"
	run script ghosttyScript with parameters {selfCloseCmd}
end launchInGhostty

-- iTerm2 — testato a mano su iTerm2 reale (non solo da documentazione).
-- Scoperte empiriche rilevanti, diverse da quanto la documentazione ufficiale
-- lascerebbe pensare:
-- - "create window with default profile command" **non restituisce un
--   riferimento valido alla finestra creata** (torna sempre "missing value" su
--   questa versione — bug riproducibile, nonostante il dizionario dichiari
--   "result type window"), e anche la proprietà "current window"
--   dell'applicazione è ugualmente inaffidabile. Per questo, come per Ghostty,
--   non è possibile fare polling preciso su una sessione specifica: si usa lo
--   stesso meccanismo di self-close appeso al comando, con lo stesso limite
--   noto (potrebbe chiudere "una" finestra iTerm2, non necessariamente quella
--   appena creata, se un'altra diventa "window 1" nel frattempo).
-- - La proprietà per "massimizzata" non è "fullscreen" ma "zoomed" (il classico
--   zoom del pulsante verde macOS — verificato funzionante). Un breve `delay`
--   prima di indirizzare "window 1" è necessario perché la finestra potrebbe
--   non essere ancora indicizzabile subito dopo la creazione.
on launchInITerm2(cliPath)
	set selfCloseCmd to cliPath & "; osascript -e 'tell application id \"com.googlecode.iterm2\" to close window 1'"
	set itermScript to "on run {theCommand}
	tell application id \"com.googlecode.iterm2\"
		activate
		create window with default profile command theCommand
		delay 0.7
		try
			set zoomed of window 1 to true
		end try
	end tell
end run"
	run script itermScript with parameters {selfCloseCmd}
end launchInITerm2

set savedBundleId to my readSavedBundleId(choiceFile)

if savedBundleId is "" then
	set candidateLabels to {"Terminale"}
	set candidateIds to {"com.apple.Terminal"}
	if my appIsInstalled("/Applications/Ghostty.app") then
		set end of candidateLabels to "Ghostty"
		set end of candidateIds to "com.mitchellh.ghostty"
	end if
	if my appIsInstalled("/Applications/iTerm.app") then
		set end of candidateLabels to "iTerm2"
		set end of candidateIds to "com.googlecode.iterm2"
	end if

	if (count of candidateLabels) is 1 then
		-- Solo Terminale installato: nessuna scelta da fare, si salva e si parte.
		set savedBundleId to "com.apple.Terminal"
		my writeSavedBundleId(choiceDir, choiceFile, savedBundleId)
	else
		set chosenLabel to choose from list candidateLabels ¬
			with title "Cartellino UniSA" ¬
			with prompt "Scegli il terminale da usare per Cartellino UniSA (potrai cambiarlo in seguito da Impostazioni):" ¬
			default items {item 1 of candidateLabels} ¬
			without multiple selections allowed
		if chosenLabel is false then
			-- Annullato: usa Terminale solo per questa volta, senza salvare —
			-- verrà richiesto di nuovo al prossimo avvio.
			set savedBundleId to "com.apple.Terminal"
		else
			set savedBundleId to item (my indexOfItem(chosenLabel as text, candidateLabels)) of candidateIds
			my writeSavedBundleId(choiceDir, choiceFile, savedBundleId)
		end if
	end if
end if

if savedBundleId is "com.mitchellh.ghostty" then
	my launchInGhostty(cliPath)
else if savedBundleId is "com.googlecode.iterm2" then
	my launchInITerm2(cliPath)
else
	-- Default anche per bundle id sconosciuto/corrotto nel file di stato.
	my launchInTerminalApp(cliPath)
end if
