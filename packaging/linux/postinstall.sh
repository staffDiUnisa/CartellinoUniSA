#!/bin/sh
# Eseguito da `fpm --after-install` dopo l'installazione del payload in
# /opt/cartellino-unisa: crea un symlink in /usr/local/bin così
# `cartellino-unisa` è lanciabile da terminale senza conoscere il percorso
# di installazione.
set -e

mkdir -p /usr/local/bin
ln -sf /opt/cartellino-unisa/cartellino-unisa /usr/local/bin/cartellino-unisa

exit 0
