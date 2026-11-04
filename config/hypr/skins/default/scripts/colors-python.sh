#!/usr/bin/env bash
# Python dependencies for end-4's unmodified color classifiers/generator.
#   --install      colors runtime        --check      prints «colors-runtime 1»
#   --install-qt   + kde-material-you-colors (Qt apps, optional)
#   --check-qt     prints «qt-colors 1»   --qt <args>  runs kde-material-you-colors
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME="${XDG_DATA_HOME:-$HOME/.local/share}/bwm/default-colors-venv"
check_python() {
    "$1" -c 'import importlib.util, importlib.metadata; assert all(importlib.util.find_spec(m) for m in ("cv2", "numpy", "PIL", "materialyoucolor")); assert importlib.metadata.version("materialyoucolor") == "2.0.10"' >/dev/null 2>&1
}
check_qt() {
    "$1" -c 'import importlib.metadata; assert importlib.metadata.version("kde-material-you-colors") == "1.10.1"' >/dev/null 2>&1
}
case "${1:-}" in
    --install|--install-qt)
        if ! check_python python3 && ! check_python "$RUNTIME/bin/python"; then
            python3 -m venv "$RUNTIME"
            "$RUNTIME/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
        fi
        if [[ "$1" == "--install-qt" ]] && ! check_qt python3 && ! check_qt "$RUNTIME/bin/python"; then
            [[ -x "$RUNTIME/bin/python" ]] || python3 -m venv --system-site-packages "$RUNTIME"
            "$RUNTIME/bin/python" -m pip install -r "$SCRIPT_DIR/requirements-qt.txt"
        fi
        exit 0 ;;
    --check-qt|--qt)
        if check_qt "$RUNTIME/bin/python"; then
            PYTHON="$RUNTIME/bin/python"
        elif check_qt python3; then
            PYTHON=python3
        else
            echo "Falta kde-material-you-colors (apps Qt de default (end-4)). Ejecuta: bash $SCRIPT_DIR/colors-python.sh --install-qt" >&2
            exit 1
        fi
        if [[ "$1" == "--check-qt" ]]; then
            echo 'qt-colors 1'
        else
            shift
            exec "$PYTHON" -c 'import sys; sys.argv[0] = "kde-material-you-colors"; from kde_material_you_colors.main import main; sys.exit(main())' "$@"
        fi
        exit 0 ;;
esac
if check_python python3; then
    PYTHON=python3
elif check_python "$RUNTIME/bin/python"; then
    PYTHON="$RUNTIME/bin/python"
else
    echo "Faltan los módulos de colores de default (end-4). Ejecuta: bash $SCRIPT_DIR/colors-python.sh --install" >&2
    exit 1
fi
if [[ "${1:-}" == "--check" ]]; then
    echo 'colors-runtime 1'
else
    exec "$PYTHON" "$@"
fi
