# Omarchy image picker in Retro

`ImagePicker.qml`, `ImagePickerModel.js`, `list.sh` and `manifest.json` come from
Omarchy's `shell/plugins/image-picker` (quattro, MIT, Copyright (c) David Heinemeier
Hansson; see `licenses/omarchy-MIT.txt` at the repository root). The existing BWM
adaptations keep the skin carousel, local script paths, inline `PreviewHold` and
thumbnail retry. The wallpaper integration preserves this carousel's appearance,
keyboard/mouse navigation, cancellation and preview lifetime.

The wallpaper protocol and `hypr/scripts/omarchy-shims/omarchy-menu-images` are
ported from Omarchy quattro `cbd0029fddcfcae0b73cf1c01a1c6031eae98f99`
(`shell/shell.qml` and `bin/omarchy-menu-images`). `OmarchyPlugins.qml` exposes
`omarchy.image-selector` (`open`, `preload`, `cancel`, `ping`); the `omarchy-shell`
shim maps upstream's `image-selector` name to it. BWM also adds a read-only
`inspect` method. Rows travel as UTF-8/base64; selection and completion use
Omarchy's temporary-file protocol. The loader does not inject `shell` or
`manifest`: the original image picker has neither property.

Adaptations to the script: thumbnails use BWM's existing ImageMagick/FFmpeg
instead of libvips/ffmpegthumbnailer, with the same 1536x864 JPEG preview size,
cache signatures, locks and atomic publication. The background conversion pool
uses the existing utilities without introducing nice/ionice dependencies.
An empty or unreadable collection returns without opening an invisible overlay.

`hypr/skins/retro/scripts/wallpaper-picker.py` resolves the active theme with
`bwm_omarchy.theme_directory` (bundled and community themes). It offers, in order:

1. The current static theme's `backgrounds` directory.
2. `~/.config/omarchy/backgrounds/<theme>` (the original format for personal extras).
3. `~/Pictures/Wallpapers` (BWM's shared collection).

Dynamic mode offers its personal extras and the shared directory. All collections
keep Omarchy's one-directory-level scan and supported image/video formats. The
current original media path is preselected, including videos with a poster.
`wallpaper-picker.sh` still owns Alt+W and the menu entry; only its Retro branch
uses this backend. Applying calls `omarchy-theme-bg-set`, which delegates to
`set-wallpaper.sh` to preserve the skin's profile, static/dynamic palette and
video engine. A skin switch while the picker is open cancels its application.

`omarchy-theme-bg-switcher` returns the selected path, as upstream does;
`wallpaper-picker.py --print-dirs` and `--print-rows` inspect the collection.
Regression checks: `python3 -m unittest discover -s tests -p test_retro_wallpapers.py`.
