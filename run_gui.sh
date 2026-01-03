cd "$(dirname "$0")"
MY_PROJECT_DIR="$(pwd)"
HYPERION_DIR="$MY_PROJECT_DIR/hyperion"

source "$MY_PROJECT_DIR/.venv/bin/activate"

export PYTHONPATH="$HYPERION_DIR:$MY_PROJECT_DIR:$PYTHONPATH"

echo "[*] Starting Hyperion GUI..."
python -m client.GUI
