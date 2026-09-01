#!/bin/sh
# Eseguito da `fpm --after-install` dopo l'installazione del payload in
# /opt/cartellino-unisa: crea un symlink in /usr/local/bin così
# `cartellino-unisa` è lanciabile da terminale senza conoscere il percorso
# di installazione. Stesso symlink per `cartellino-unisa-gui` (Fase 13
# TODO_gui.md): nessuna icona/voce desktop per il launcher grafico su Linux
# (fuori scope, vedi TODO_gui.md — richiederebbe un file .desktop e
# l'installazione nel tema icone di sistema, infrastruttura non ancora nel
# repo), ma il binario resta lanciabile da riga di comando.
set -e

mkdir -p /usr/local/bin
ln -sf /opt/cartellino-unisa/cartellino-unisa /usr/local/bin/cartellino-unisa
ln -sf /opt/cartellino-unisa/cartellino-unisa-gui /usr/local/bin/cartellino-unisa-gui

exit 0
