cd "$(dirname "$0")"
MY_PROJECT_DIR="$(pwd)"
HYPERION_DIR="$MY_PROJECT_DIR/hyperion"

source "$MY_PROJECT_DIR/.venv/bin/activate"

export PYTHONPATH="$HYPERION_DIR:$MY_PROJECT_DIR:$PYTHONPATH"

# Run the admin GUI
echo "[*] Starting Hyperion Admin GUI..."
cd "$MY_PROJECT_DIR"
python -m client.admin_gui

