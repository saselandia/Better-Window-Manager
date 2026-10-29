import QtQuick
import QtQml.Models
import qs.Commons as Om
import qs.modules.common

// This adapter belongs to Retro. Shared settings pages keep their data and controls,
// while this process renders them with Omarchy's live colors and typography.
Item {
    id: root
    readonly property color bg: Om.Color.popups.background
    readonly property color fg: Om.Color.popups.text
    function surface(amount) { return Qt.rgba(bg.r * (1 - amount) + fg.r * amount, bg.g * (1 - amount) + fg.g * amount, bg.b * (1 - amount) + fg.b * amount, 1); }

    Binding { target: Appearance; property: "outlinedControls"; value: true }
    Binding { target: Appearance; property: "backgroundTransparency"; value: 0 }
    Binding { target: Appearance; property: "contentTransparency"; value: 0 }
    Binding { target: Appearance.font.family; property: "main"; value: Om.Style.font.menuFamily }
    Binding { target: Appearance.font.family; property: "numbers"; value: Om.Style.font.menuFamily }
    Binding { target: Appearance.font.family; property: "title"; value: Om.Style.font.menuFamily }
    Binding { target: Appearance.font.pixelSize; property: "small"; value: Om.Style.font.body }
    Binding { target: Appearance.font.pixelSize; property: "larger"; value: Om.Style.font.heading }

    Instantiator {
        model: [
            { role: "m3background", value: root.bg }, { role: "m3onBackground", value: root.fg },
            { role: "m3surface", value: root.surface(0.025) }, { role: "m3onSurface", value: root.fg },
            { role: "m3surfaceDim", value: root.bg }, { role: "m3surfaceBright", value: root.surface(0.12) },
            { role: "m3surfaceContainerLowest", value: root.bg },
            { role: "m3surfaceContainerLow", value: root.surface(0.025) },
            { role: "m3surfaceContainer", value: root.surface(0.05) },
            { role: "m3surfaceContainerHigh", value: root.surface(0.075) },
            { role: "m3surfaceContainerHighest", value: root.surface(0.1) },
            { role: "m3surfaceVariant", value: root.surface(0.075) },
            { role: "m3onSurfaceVariant", value: root.surface(0.68) },
            { role: "m3outline", value: root.surface(0.48) }, { role: "m3outlineVariant", value: root.surface(0.22) },
            { role: "m3primary", value: Om.Color.accent }, { role: "m3onPrimary", value: root.bg },
            { role: "m3surfaceTint", value: Om.Color.accent },
            { role: "m3primaryContainer", value: Om.Color.menu.selectedBackground },
            { role: "m3onPrimaryContainer", value: root.fg },
            { role: "m3secondary", value: Om.Color.accent }, { role: "m3onSecondary", value: root.bg },
            { role: "m3secondaryContainer", value: root.surface(0.065) }, { role: "m3onSecondaryContainer", value: root.fg },
            { role: "m3tertiary", value: Om.Color.accent }, { role: "m3onTertiary", value: root.bg },
            { role: "m3tertiaryContainer", value: root.surface(0.065) }, { role: "m3onTertiaryContainer", value: root.fg },
            { role: "m3inverseSurface", value: root.fg }, { role: "m3inverseOnSurface", value: root.bg },
            { role: "m3error", value: Om.Color.urgent }, { role: "m3onError", value: root.bg },
            { role: "m3errorContainer", value: root.surface(0.1) }, { role: "m3onErrorContainer", value: Om.Color.urgent },
            { role: "darkmode", value: root.bg.hslLightness < 0.5 }
        ]
        delegate: Binding {
            required property var modelData
            // The model is replaced when a theme arrives. Old delegates must not
            // restore their saved palette over the replacement bindings.
            restoreMode: Binding.RestoreNone
            target: Appearance.m3colors
            property: modelData.role
            value: modelData.value
        }
    }
}
