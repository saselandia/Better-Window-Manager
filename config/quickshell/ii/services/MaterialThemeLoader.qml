pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

/**
 * Automatically reloads generated theme colors (Material You or Omarchy Retro).
 * Synchronizes colors across Quickshell based on the active BWM skin.
 */
Singleton {
    id: root
    property string filePath: Directories.generatedMaterialThemePath
    property string retroFilePath: Directories.generatedRetroThemePath
    // Breeze: the active Plasma colour scheme (kdeglobals) mapped onto the Material 3 roles by
    // skins/plasma/scripts/plasma_palette.py, instead of the wallpaper colors.
    property string plasmaFilePath: `${Directories.home}/.local/state/bwm/plasma/colors.json`
    // Only set by the Plasma settings app (its own process), not by the shell.
    property bool forceBreeze: false

    onForceBreezeChanged: if (forceBreeze) applyPlasmaColors()

    function applyPlasmaColors() {
        const text = plasmaThemeFileView.loaded ? plasmaThemeFileView.text() : "";
        if (text) {
            try {
                const json = JSON.parse(text);
                if (json.primary) {
                    for (const key in json) {
                        if (key === "darkmode" || key === "scheme" || typeof json[key] !== "string" || !json[key].startsWith("#"))
                            continue;
                        Appearance.m3colors["m3" + key.replace(/_([a-z])/g, g => g[1].toUpperCase())] = json[key];
                    }
                    Appearance.m3colors.darkmode = json.darkmode !== false;
                    return;
                }
            } catch (e) {
                console.log("[MaterialThemeLoader] Error parsing Plasma colors:", e);
            }
        }
        // Keep the current palette until plasma_palette.py publishes KDE's scheme.
        // The skin hook generates this file before the shell switches to Breeze.
    }

    function reapplyTheme() {
        if (root.forceBreeze || Appearance.isPlasma) {
            applyPlasmaColors()
        } else if (Appearance.isRetro) {
            retroThemeFileView.reload()
            delayedRetroFileRead.start()
        } else {
            themeFileView.reload()
            delayedFileRead.start()
        }
    }

    function applyRetroColors(fileContent) {
        if (!fileContent) return;
        try {
            const json = JSON.parse(fileContent);
            if (!json.accent) return;

            const accent = json.accent;
            const secondary = json.secondary || "#3f16ec";
            const bg = json.bg || "#090c0f";
            const fg = json.fg || "#f8fafc";
            const dim = json.dim || "#475569";
            const muted = json.muted || "#94a3b8";
            const border = json.border || accent;

            Appearance.m3colors.m3primary = accent;
            Appearance.m3colors.m3surfaceTint = accent;
            Appearance.m3colors.m3onPrimary = "#090c0f";
            Appearance.m3colors.m3primaryContainer = "#161f2e";
            Appearance.m3colors.m3onPrimaryContainer = accent;
            Appearance.m3colors.m3inversePrimary = accent;

            Appearance.m3colors.m3background = bg;
            Appearance.m3colors.m3onBackground = fg;
            Appearance.m3colors.m3surface = bg;
            Appearance.m3colors.m3surfaceDim = bg;
            Appearance.m3colors.m3surfaceBright = "#1c2533";

            Appearance.m3colors.m3surfaceContainerLowest = "#05070a";
            Appearance.m3colors.m3surfaceContainerLow = "#0d1117";
            Appearance.m3colors.m3surfaceContainer = "#121820";
            Appearance.m3colors.m3surfaceContainerHigh = "#18202a";
            Appearance.m3colors.m3surfaceContainerHighest = "#202a37";

            Appearance.m3colors.m3onSurface = fg;
            Appearance.m3colors.m3surfaceVariant = "#1a222d";
            Appearance.m3colors.m3onSurfaceVariant = muted;
            Appearance.m3colors.m3inverseSurface = fg;
            Appearance.m3colors.m3inverseOnSurface = bg;

            Appearance.m3colors.m3outline = border;
            Appearance.m3colors.m3outlineVariant = dim;

            Appearance.m3colors.m3secondary = secondary;
            Appearance.m3colors.m3onSecondary = "#ffffff";
            Appearance.m3colors.m3secondaryContainer = "#161e29";
            Appearance.m3colors.m3onSecondaryContainer = muted;

            Appearance.m3colors.m3tertiary = secondary;
            Appearance.m3colors.m3onTertiary = "#ffffff";
            Appearance.m3colors.m3tertiaryContainer = "#181f2b";
            Appearance.m3colors.m3onTertiaryContainer = muted;

            Appearance.m3colors.darkmode = true;
        } catch (e) {
            console.log("[MaterialThemeLoader] Error parsing retro colors:", e);
        }
    }

    function applyColors(fileContent) {
        if (root.forceBreeze || Appearance.isPlasma) {
            applyPlasmaColors();
            return;
        }
        if (!fileContent) return;
        try {
            const json = JSON.parse(fileContent);
            for (const key in json) {
                if (json.hasOwnProperty(key)) {
                    // Convert snake_case to CamelCase
                    const camelCaseKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase())
                    const m3Key = "m3" + camelCaseKey;
                    Appearance.m3colors[m3Key] = json[key]
                }
            }
            Appearance.m3colors.darkmode = (Appearance.m3colors.m3background.hslLightness < 0.5)
        } catch (e) {
            console.log("[MaterialThemeLoader] Error parsing material colors:", e);
        }
    }

    function resetFilePathNextTime() {
        resetFilePathNextWallpaperChange.enabled = true
    }

    Connections {
        target: Appearance
        function onIsRetroChanged() {
            root.reapplyTheme();
        }
        function onIsPlasmaChanged() {
            root.reapplyTheme();
        }
    }

    Connections {
        id: resetFilePathNextWallpaperChange
        enabled: false
        target: Config.options.background
        function onWallpaperPathChanged() {
            root.filePath = ""
            root.filePath = Directories.generatedMaterialThemePath
            resetFilePathNextWallpaperChange.enabled = false
        }
    }

    Timer {
        id: delayedFileRead
        interval: Config.options?.hacks?.arbitraryRaceConditionDelay ?? 100
        repeat: false
        running: false
        onTriggered: {
            if (!Appearance.isRetro) {
                root.applyColors(themeFileView.text())
            }
        }
    }

    Timer {
        id: delayedRetroFileRead
        interval: Config.options?.hacks?.arbitraryRaceConditionDelay ?? 100
        repeat: false
        running: false
        onTriggered: {
            if (Appearance.isRetro) {
                root.applyRetroColors(retroThemeFileView.text())
            }
        }
    }

    FileView { 
        id: themeFileView
        path: Qt.resolvedUrl(root.filePath)
        watchChanges: true
        onFileChanged: {
            this.reload()
            if (!Appearance.isRetro) {
                delayedFileRead.start()
            }
        }
        onLoadedChanged: {
            if (!Appearance.isRetro) {
                const fileContent = themeFileView.text()
                root.applyColors(fileContent)
            }
        }
        onLoadFailed: root.resetFilePathNextTime();
    }

    FileView {
        id: plasmaThemeFileView
        // Sólo en Breeze: fuera de ella no hace falta (ni existe hasta entrar la primera vez)
        path: (root.forceBreeze || Appearance.isPlasma) ? root.plasmaFilePath : ""
        watchChanges: true
        onFileChanged: {
            this.reload()
            delayedPlasmaFileRead.start()
        }
        onLoadedChanged: if (root.forceBreeze || Appearance.isPlasma) root.applyPlasmaColors()
    }

    Timer {
        id: delayedPlasmaFileRead
        interval: Config.options?.hacks?.arbitraryRaceConditionDelay ?? 100
        onTriggered: if (root.forceBreeze || Appearance.isPlasma) root.applyPlasmaColors()
    }

    FileView { 
        id: retroThemeFileView
        path: Qt.resolvedUrl(root.retroFilePath)
        watchChanges: true
        onFileChanged: {
            this.reload()
            if (Appearance.isRetro) {
                delayedRetroFileRead.start()
            }
        }
        onLoadedChanged: {
            if (Appearance.isRetro) {
                const fileContent = retroThemeFileView.text()
                root.applyRetroColors(fileContent)
            }
        }
    }

    Component.onCompleted: {
        root.reapplyTheme();
    }

    function toggleLightDark() {
        const currentlyDark = Appearance.m3colors.darkmode;
        Quickshell.execDetached([Directories.wallpaperSwitchScriptPath, "--mode", currentlyDark ? "light" : "dark", "--noswitch"]);
    }

    GlobalShortcut {
        name: "toggleLightDark"
        description: "Toggles between dark theme and light theme"

        onPressed: {
            root.toggleLightDark();
        }
    }

    IpcHandler {
        target: "theme"

        function reload(): void {
            root.reapplyTheme();
        }

        function toggleLightDark(): void {
            root.toggleLightDark();
        }
    }
}
