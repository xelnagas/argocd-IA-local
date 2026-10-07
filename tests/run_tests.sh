#!/usr/bin/env bash
# Script d'exécution rapide de la suite de tests fonctionnels J.A.R.V.I.S.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN=$(command -v python3 || command -v python)

if [ -z "$PYTHON_BIN" ]; then
    echo "[-] Erreur : Python n'a pas été trouvé dans le PATH."
    exit 1
fi

echo "[*] Lancement de la suite de tests fonctionnels avec $PYTHON_BIN..."
$PYTHON_BIN "$SCRIPT_DIR/run_functional_suite.py" "$@"
