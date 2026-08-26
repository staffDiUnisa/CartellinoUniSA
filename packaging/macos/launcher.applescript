-- Cartellino UniSA — avvia il Terminale ed esegue la CLI/TUI.
-- Percorso assoluto invece del comando dal PATH: un Terminale appena aperto da
-- Finder potrebbe non aver ancora ricaricato un PATH modificato di recente
-- (stesso problema di profili shell che sovrascrivono PATH, già documentato in
-- README.md per l'uso da riga di comando).
set cliPath to "/usr/local/cartellino-unisa/cartellino-unisa"

tell application "Terminal"
	activate
	if not (exists window 1) then
		do script cliPath
	else
		do script cliPath in window 1
	end if
end tell
