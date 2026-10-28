# 🪟 Better Window Manager (BWM)

<div align="center">

**A window manager that wraps every other window manager as a _skin_.**
Default (end-4 / illogical-impulse), Retro (Omarchy) and KDE Plasma on top of Hyprland and Quickshell: switch between them without closing anything, and your apps follow.

<p align="center">
  <b>English</b> • <a href="README.es.md">Español</a>
</p>

[![GitLab](https://img.shields.io/badge/GitLab-bwm-orange?logo=gitlab)](https://gitlab.com/saselandia/bwm)
[![GitHub](https://img.shields.io/badge/GitHub-Better--Window--Manager-blue?logo=github)](https://github.com/saselandia/Better-Window-Manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hyprland](https://img.shields.io/badge/Hyprland-Wayland-brightgreen)](https://hyprland.org)
[![Quickshell](https://img.shields.io/badge/Quickshell-Qt%206%20%2F%20QML-purple)](https://quickshell.outfoxxed.me)

</div>

---

## 🧭 What BWM is

**BWM (Better Window Manager) is a window manager that aims to encapsulate every existing window manager and desktop as a _skin_.** Each skin recreates another desktop —its bar, menus, panels, shortcuts and themes— on the same compositor (Hyprland) and shell (Quickshell), and the whole system follows it: GTK, Qt, terminals, Firefox, Vesktop, Spotify, Steam, the lock screen and the login screen. Switch skins live with **`Alt + T`**.

**The goal is compatibility.** Each skin should accept the themes and look-and-feel add-ons of the desktop it imitates: if you are on the KDE Plasma skin and download a Plasma theme, it should apply and work; on Retro, the same for Omarchy themes and plugins. BWM has few interfaces of its own; almost everything is the original desktop's interface.

> ### 🟩 Designed with NVIDIA cards in mind
> BWM is developed and tested on an **NVIDIA GPU** (Wayland, Hyprland and NVIDIA's official driver), and its choices —boot, monitors, screenshots, games— are made for that hardware.
> <sub>It can also be used with AMD and Intel cards (Hyprland supports them), but they are less tested. NVIDIA is a registered trademark of NVIDIA Corporation; BWM is an independent project, not affiliated with or endorsed by NVIDIA.</sub>

### Bundled skins

| Skin | Imitates | Windows | Default theme | Other themes | Compatibility target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Default** | [end-4 / illogical-impulse](https://github.com/end-4/dots-hyprland) (Material You) | Tiling | **Dynamic**: matugen builds the palette from your wallpaper every time it changes | — (light or dark from the wallpaper) | matugen / end-4 templates and wallpapers |
| **Retro** | [Omarchy 4](https://github.com/basecamp/omarchy) (`quattro` branch) | Tiling | **Dynamic**: an Omarchy-format palette from the wallpaper | 23 static Omarchy themes (Tokyo Night, Catppuccin, Nord, Gruvbox…) with `Alt + R`; once one is pinned, the wallpaper no longer changes the colours | Omarchy community themes and plugins (Settings → Themes / Plugins) |
| **KDE Plasma** | KDE Plasma 6 (Breeze Dark) | Stacking (floating) | **Static**: Breeze Dark, unaffected by the wallpaper | — | Plasma colour schemes and global themes from the KDE Store (planned) |

### Few skins, the essentials, the same in all of them

BWM does not want to be complicated. It offers **very few skins** —the current three— that do the essentials and are quick to learn. They all share almost the same basic features (launcher, settings, network, Bluetooth, audio, displays, screenshots, clipboard, notifications, lock screen…), so moving between them means relearning nothing. When a desktop has something very important of its own (Omarchy's dock and menu, Plasma's Kickoff and title bars), that skin brings it. Anyone who wants more complexity can add it; BWM does not ship it.

**Kept when you switch skins:** network and Bluetooth, the cursor, the night-light temperature (Kelvin), default apps, workspaces (the same 1–10 on the same monitors), displays (resolution, refresh rate, position and scale: change it in one, it stays changed in all), autostart apps, services (weather, AI, search…), the interface (logo, overview, OSD, lock screen) and general settings (language, time, battery). **Each skin's own:** its look and fonts (the skin's and its theme's), wallpaper, bar and dock.

### Compatibility with each desktop's themes (estimate)

This is the point of the project, so we measure it. Estimated share of the original desktop's themes or plugins that work today without changes:

| Skin | Original themes | Original plugins / extensions | Basis of the estimate |
| :--- | :---: | :---: | :--- |
| **Retro** (Omarchy) | **~90 %** | **~80 %** | Themes: `colors.toml`, wallpapers and app files (Neovim, VS Code, btop…) are applied; not the theme's `hyprland.lua`, `icons.theme` (Retro uses Papirus with the accent) or the Chromium theme (needs root). Plugins: bar widgets and services work unchanged; not those replacing the bar, lock screen, overlays or panels |
| **Default** (end-4) | **~90 %** | — | Any wallpaper builds its palette (100 %); third-party matugen templates are added to `matugen/config.toml`. end-4 has no plugin catalogue |
| **KDE Plasma** | **~5 %** | **0 %** | Breeze Dark only. From the KDE Store, cursors work (shared by every skin); colour schemes, global themes, Plasma styles, Aurorae and plasmoids not yet |

### Towards a single compositor: Hyprland

One of BWM's most ambitious goals is **porting desktops that do not run on Hyprland to Hyprland**, starting with KDE Plasma (in progress: its panel, Kickoff, applets, KWin's Alt+Tab, OSD and Breeze title bars already run on Hyprland), so everything lives on one compositor. Other desktops and window managers can follow the same path as new skins.

Switching between a tiling skin and a stacking one keeps every window where it was, and apps restarted to pick up the new theme come back in place without popping up on the workspace you are looking at.

More skins: [docs/SKINS.md](docs/SKINS.md) explains what a skin is and how one is added.

## 👋 Welcome window and the `bwm` command

After installing, every login opens a Calamares-style welcome wizard that thanks you, lists the installed skins —**green** when all their requirements are met—, expands each one's requirements with the commands to install what is missing, lets you activate them and links the wiki for adding skins. Turn it off with the "Show at login" switch.

```bash
bwm                 # open the welcome window (works before the install is finished too)
bwm check           # core and per-skin requirements, with the commands for your distro
bwm skins           # installed skins
bwm skin retro      # switch skin (checks its requirements first)
bwm startup off     # don't open the welcome window at login
```

## ✨ Key Features

- 🎨 **Real-Time Dynamic Theming:** Change your wallpaper and the entire desktop (windows, panels, terminal, and applications) instantly adapts its palette using Material You.
- 🖥️ **Interactive Display & Monitor Manager:** Configure resolution, refresh rate (Hz), scale, and rearrange multi-monitor setups visually with mouse **drag-and-drop** and magnetic edge snapping.
- 🖱️ **Cursor & Hyprcursor Theme Manager:** Easily switch cursor themes (Hyprcursor and XCursor) and customize cursor sizes (20px to 48px) with a dedicated GUI, complete with live hover testing zones and bundled Bibata Material Design cursors.
- 📁 **Integrated Nautilus File Manager:** Open your file manager anytime with **`Super + E`** or **`Alt + E`**, featuring dynamic dark mode and synced accent colors.
- 🚀 **Quickshell HUD & Widgets:** Top bar with system metrics, quick settings sidebar, and an interactive **`Alt + Tab`** window switcher with live visual previews.
- 🔍 **App Launcher & Search:** Instant access to your applications and smart system search by tapping the **`Super`** key.
- 🌐 **Themed Firefox, Vesktop & Spotify:** Seamless aesthetic integration across your daily tools with live synchronized color palettes.
- 🪟 **Persistent Floating Rules:** Easily toggle and remember which apps float or tile across reboots with **`Alt + Q`**.
- 🖼️ **Visual Wallpaper Selector:** Browse and select wallpapers interactively with instant preview by pressing **`Alt + W`**.
- ⚡ **One-Command Automated Installer:** Fast setup and effortless deployment via `install.sh`.

---

## 📸 Gallery & Screenshots

> 💡 **Real-Time Dynamic Theming:** Changing wallpaper **automatically adapts all application colors and widgets** to the tonal palette generated by `matugen`.

| 🎨 Themed Apps (Vesktop, Nautilus, Spotify) | 🌐 Firefox with userChrome.css & Kitty Terminal |
| :---: | :---: |
| [![Vesktop, Nautilus & Spotify](assets/screenshots/01-apps-material-you.png)](assets/screenshots/01-apps-material-you.png) | [![Firefox & Kitty](assets/screenshots/02-firefox-terminal.png)](assets/screenshots/02-firefox-terminal.png) |
| **❄️ Clean Desktop with Quickshell Bar & Widgets** | **⚡ High-Contrast Cyberpunk Theme with Neofetch** |
| [![Gentoo Desktop](assets/screenshots/03-desktop-clean.jpg)](assets/screenshots/03-desktop-clean.jpg) | [![Cyberpunk Theme](assets/screenshots/04-cyberpunk-neofetch.png)](assets/screenshots/04-cyberpunk-neofetch.png) |

---

## 🛠️ Requirements

The installer **checks everything before touching anything**: if something is missing it tells you what, what it is for, and gives you the commands for your distribution (Gentoo, Arch/CachyOS, Fedora, openSUSE, Debian/Ubuntu; elsewhere, the guide), then exits. Check any time with:

```bash
./install.sh --check       # or, once installed: bwm check
```

The full list with each distribution's package names is in [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) and comes from `config/hypr/skins/*.json`. In short:

| | Needs |
| :--- | :--- |
| **Core** (every skin) | Hyprland ≥ 0.55 (Lua config), Quickshell (tested with 0.3.1), Qt ≥ 6.10 with 5Compat and SVG, Python ≥ 3.11 with Pillow, jq, swww (or awww), wl-clipboard, cliphist, kitty, grim, slurp, libnotify, GLib, fontconfig, PipeWire/WirePlumber, adw-gtk3. Fonts (Material Symbols, Google Sans Flex, JetBrainsMono Nerd Font) are installed by BWM |
| **Default** | matugen, rofi (Wayland), hyprpolkitagent |
| **Retro** | ImageMagick 7 (`magick`). Polkit, notifications and OSD are drawn by Quickshell |
| **KDE Plasma** | hyprpolkitagent, Breeze icons and BWM's hyprbars plugin **built for your Hyprland version** (the installer builds it if you have the Hyprland headers, `make` and a C++ compiler) |

Optional: desktop portals (hyprland, gtk), NetworkManager, BlueZ, qt6ct, socat, git, Nautilus, Firefox, Flatpak (Vesktop, Spotify, Stremio), btop, fastfetch, Papirus, hyprsunset, SDDM and Plymouth.

---

## 🚀 Download & Installation

### 1. Clone the repository

You can clone from either GitHub or GitLab:

```bash
# From GitHub:
git clone https://github.com/saselandia/Better-Window-Manager.git ~/dotfiles/bwm
cd ~/dotfiles/bwm

# Or from GitLab:
git clone https://gitlab.com/saselandia/bwm.git ~/dotfiles/bwm
cd ~/dotfiles/bwm
```

### 2. Run the installer

```bash
./install.sh            # checks requirements, links ~/.config to the repo and applies the themes
./install.sh --check    # only check the requirements
./install.sh --skins default,retro   # only some skins
./install.sh --copy     # copy instead of linking
```

If a requirement is missing, the installer stops **without changing anything** and prints the commands to install it. Otherwise it backs up your previous `~/.config`, links the configs, installs fonts and cursors, creates the `bwm` command, builds the Plasma plugin if your Hyprland is a different version, themes the apps you have and enables the welcome window.

### 3. Launch or reload the desktop

If you are already inside a Hyprland session:
```bash
hyprctl reload
```

To set your wallpaper and generate your initial Material You color palette:
```bash
# Press [ALT + W] or run:
~/.config/hypr/scripts/set-wallpaper.sh /path/to/your/image.jpg
```

### 4. Login screen and boot splash (Omarchy style)

`install.sh` offers to set this up (or pass `--login` / `--no-login`). It does what Omarchy's installer does: SDDM with Omarchy's login theme (BWM logo, active theme colours) inside a minimal Hyprland with your keyboard layout and monitor layout, remembering the last user and session. A root service then refreshes the colours on every wallpaper or theme change. By hand:

```bash
sudo ~/.config/hypr/scripts/install-boot-theme.sh --all            # SDDM + automatic updates
sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm --autologin   # no password (encrypted disk, like Omarchy)
sudo ~/.config/hypr/scripts/install-boot-theme.sh --disable-sddm   # back to the previous login (tty1 autologin)
sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth       # boot splash (rebuilds the initramfs)
sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert         # remove the boot splash
```

The boot splash is opt-in: it rebuilds the initramfs with dracut (keeping the same GPU drivers, refusing images that grow more than 50 %) and adds `splash` to the existing `grub.cfg` without regenerating it. Backups are kept and `--revert` restores them.

### 5. Omarchy bar plugins (Retro skin)

The Retro bar runs **Omarchy shell plugins** unchanged: Omarchy's `qs.Commons` / `qs.Ui` libraries (MIT) are vendored in `config/quickshell/ii/Commons` and `Ui`, and read BWM's Omarchy palette. Omarchy's clock and calendar dropdown are part of the Retro bar. These plugins come **preinstalled and enabled** (`config/quickshell/ii/omarchy-plugins`, all MIT): Omarchy's weather and Elsewhen (world clocks) after the clock, AI usage (`ai-usagebar`, its binary is built by `install.sh` with cargo), OmaStats, media controls with album art and active window. Turn each one off in **Settings → Bar** (Retro). More plugins, like `omarchy plugin add`:

```bash
~/.config/hypr/scripts/bwm-plugin.sh add https://github.com/<user>/<plugin>.git [--section left|center|centerEnd|right]
~/.config/hypr/scripts/bwm-plugin.sh list | update | enable <id> | disable <id> | remove <id> | build
```

Plugins are unsandboxed code running inside the bar (as in Omarchy): review the ones you add.

---

## 🎨 Application Theme Verification

The `./install.sh` script automatically configures and links themes for all supported applications. If you want to verify or fine-tune them manually:

### 1. 📁 Nautilus (File Manager)
- **Launch:** Press **`Super + E`** or **`Alt + E`** at any time to open Nautilus with active dark mode and dynamic accent colors.

### 2. 🌐 Firefox
- **Pywalfox & Custom Styles:**
  - The installer automatically deploys `userChrome.css`, the `pywalfox.xpi` extension into your Firefox profile, and sets up the native messaging host.
  - When opening Firefox for the first time, if prompted about the newly added Pywalfox extension, click **"Enable"**.
  - In the Firefox toolbar, click the **Pywalfox** icon and click **"Fetch Pywal Colors"** once to sync the tab bar and interface in real time.
  - *(Optional check)*: If custom styles do not appear, go to `about:config` and verify that `toolkit.legacyUserProfileCustomizations.stylesheets` is set to **`true`**.

### 3. 💬 Vesktop (Discord)
- **Theme check:** In Vesktop, navigate to **User Settings** → **Vencord** → **Themes** and confirm that the **bwm.theme.css** theme is enabled (its colours follow the skin).

### 4. 🎵 Spotify Desktop & Spicetify
- **Flatpak write permissions:** If Spicetify requires write permissions to inject the theme into the Spotify Flatpak, run:
  ```bash
  chmod a+wr "$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify" "$HOME/.local/share/flatpak/app/com.spotify.Client/x86_64/stable/active/files/extra/share/spotify/Apps" -R
  spicetify backup apply
  ```

---

## 🔄 Updating to the Latest Version

```bash
# 1. Enter the repository directory:
cd ~/dotfiles/bwm

# 2. Pull the latest updates:
git pull

# 3. If installed with symlinks (--symlink), updates are active immediately.
#    If installed with copy mode (--copy), re-run the copy:
#    ./install.sh --copy

# 4. Live-reload Hyprland to apply changes on the fly:
hyprctl reload
```

---

## ⌨️ Keybindings & Shortcuts

> Note: The primary modifier keys in this configuration are **`ALT`** and **`SUPER`**.

| Shortcut | Action |
| :--- | :--- |
| **`SUPER_L`** (Win) | Open Application Menu / Quickshell Search |
| **`SUPER + E`** / **`ALT + E`** | **Launch File Manager (Nautilus)** |
| **`CTRL + ENTER`** | Open Kitty terminal with dynamic colors |
| **`ALT + TAB`** | Visual window switcher with live thumbnails |
| **`ALT + W`** | Graphical wallpaper selector with instant re-theming |
| **`ALT + Q`** | Toggle and remember persistent floating rule for active window |
| **`ALT + X`** | Close focused window |
| **`ALT + 1` .. `ALT + 0`** | Switch to workspace (1 to 10) |
| **`ALT + SHIFT + [1-0]`** | Move active window to workspace |
| **`SUPER + A`** | Toggle Quickshell Quick Settings sidebar |
| **`SUPER + L`** | Lock screen with Quickshell Lock |
| **`SUPER + SHIFT + S`** / **`Print`** | Interactive area screenshot |
| **`ALT + A`** | Toggle on-screen interactive keybinding cheatsheet |

---

## 💖 Credits & Acknowledgments

This project is inspired by and builds upon the incredible work of the open-source community:

- **[end-4 / dots-hyprland](https://github.com/end-4/dots-hyprland)**: Foundation and inspiration for Quickshell widgets (Illogical Impulse), animations, and the Material You theming architecture.
- **[Hyprland](https://hyprland.org)**: Dynamic, extensible, and GPU-driven Wayland compositor.
- **[Quickshell](https://quickshell.outfoxxed.me)**: Modern and flexible desktop HUD & widget framework using Qt 6 and QML.
- **[Matugen](https://github.com/InioX/matugen)**: Dynamic Material Design 3 color palette generator.
- **[Omarchy](https://github.com/basecamp/omarchy)** (MIT): Retro skin app templates, Plymouth/SDDM login themes, the SDDM Hyprland greeter, hyprlock-style lock screen, screensaver, glass mode and font switcher.

---

## 🤝 Contributing & Development

Contributions, bug reports, and suggestions are warmly welcomed:

1. **Fork** the repository on GitHub or GitLab.
2. Create a feature branch (`git checkout -b feature/awesome-feature`).
3. Commit your changes (`git commit -m "feat: add support for..."`).
4. Push your branch (`git push origin feature/awesome-feature`) and open a **Pull Request** or **Merge Request**.
