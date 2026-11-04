#!/usr/bin/env bash
# end-4's matugen/templates/kde/kde-material-you-colors-wrapper.sh (dots-hyprland 2f2a376, GPL-3.0).
# BWM changes: runs through colors-python.sh instead of $ILLOGICAL_IMPULSE_VIRTUAL_ENV, uses
# kde-shims/ when Plasma's own tools are missing, Darkly as widget style when installed (end-4's
# setup does it once with kwriteconfig6), and runs it detached with its log in BWM's state. Without
# KWin (Hyprland) it stops after applying, at its KWin reload, as it does in end-4.

XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLORS_PYTHON="$SCRIPT_DIR/colors-python.sh"

bash "$COLORS_PYTHON" --check-qt >/dev/null || exit 1

color=$(tr -d '\n' < "$XDG_STATE_HOME/quickshell/user/generated/color.txt")

current_mode=$(gsettings get org.gnome.desktop.interface color-scheme 2>/dev/null | tr -d "'")
if [[ "$current_mode" == "prefer-dark" ]]; then
    mode_flag="-d"
else
    mode_flag="-l"
fi

# Parse --scheme-variant flag
scheme_variant_str=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scheme-variant)
            scheme_variant_str="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Map string variant to integer
case "$scheme_variant_str" in
    scheme-content) sv_num=0 ;;
    scheme-expressive) sv_num=1 ;;
    scheme-fidelity) sv_num=2 ;;
    scheme-monochrome) sv_num=3 ;;
    scheme-neutral) sv_num=4 ;;
    scheme-tonal-spot) sv_num=5 ;;
    scheme-vibrant) sv_num=6 ;;
    scheme-rainbow) sv_num=7 ;;
    scheme-fruit-salad) sv_num=8 ;;
    "") sv_num=5 ;;
    *)
        echo "Unknown scheme variant: $scheme_variant_str" >&2
        exit 1
        ;;
esac

# end-4's config.conf (installed to ~/.config like its other dotfiles); a user's own one is kept
kmyc_config="${XDG_CONFIG_HOME:-$HOME/.config}/kde-material-you-colors"
[[ -e "$kmyc_config" || -L "$kmyc_config" ]] || ln -s "$(cd -P "$SCRIPT_DIR" && cd ../../../.. && pwd)/kde-material-you-colors" "$kmyc_config"

command -v plasma-apply-colorscheme >/dev/null || export PATH="$SCRIPT_DIR/kde-shims:$PATH"
if command -v kwriteconfig6 >/dev/null; then
    qt_plugins="$(qtpaths6 --query QT_INSTALL_PLUGINS 2>/dev/null || echo /usr/lib64/qt6/plugins)"
    if compgen -G "$qt_plugins/styles/darkly*.so" >/dev/null; then
        kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle Darkly
    fi
fi

log="$XDG_STATE_HOME/bwm/default-colors/kde-material-you-colors.log"
mkdir -p "${log%/*}"
setsid bash "$COLORS_PYTHON" --qt "$mode_flag" --color "$color" -sv "$sv_num" \
    </dev/null >"$log" 2>&1 &
