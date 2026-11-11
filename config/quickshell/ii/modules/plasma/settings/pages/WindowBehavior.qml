// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import ".."

/**
 * BWM F11: «Window Behavior». Plasma's kcm_kwinoptions is a QWidget module (not embeddable in this
 * QML window), so this page offers the same kwinrc keys, limited to what BWM really applies (the F2
 * bridge, placement.lua, breezebars): focus, placement, title bar actions and screen-edge/magnet
 * snapping. Values not supported by BWM are not offered rather than pretending they work.
 */
QQC2.ScrollView {
    id: page
    property var entry
    function t(en, es) { return SettingsState.spanish ? es : en; }
    KdeSettingsStore { id: store }
    readonly property var v: store.values

    component Choice: QQC2.ComboBox {
        id: combo
        required property var options   // [[value, en, es], …]
        required property string current
        required property var onPick
        model: options.map(o => SettingsState.spanish ? o[2] : o[1])
        implicitContentWidthPolicy: QQC2.ComboBox.WidestText
        currentIndex: Math.max(0, options.findIndex(o => o[0] === current))
        onActivated: index => onPick(options[index][0])
    }
    component Zone: QQC2.SpinBox {
        required property int current
        required property var onPick
        from: 0; to: 100
        value: current
        textFromValue: (v) => v === 0 ? page.t("None", "Ninguna") : v + " px"
        valueFromText: (text) => parseInt(text) || 0
        onValueModified: onPick(value)
    }

    Kirigami.FormLayout {
        width: page.availableWidth
        enabled: store.ready

        Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: page.t("Focus", "Foco") }
        Choice {
            Kirigami.FormData.label: page.t("Window activation policy:", "Política de activación de ventanas:")
            options: [["ClickToFocus", "Click to focus", "Pulsar para enfocar"],
                      ["FocusFollowsMouse", "Focus follows mouse", "El foco sigue al ratón"],
                      ["FocusUnderMouse", "Focus under mouse", "Foco bajo el ratón"],
                      ["FocusStrictlyUnderMouse", "Focus strictly under mouse", "Foco estrictamente bajo el ratón"]]
            current: page.v.focus ?? "ClickToFocus"
            onPick: (value) => store.write("kwinrc", "Windows", "FocusPolicy", value, "focus")
        }
        QQC2.Label {
            text: page.t("In BWM every «follows mouse» policy behaves the same (Hyprland follow_mouse).",
                         "En BWM las políticas en las que el foco sigue al ratón se comportan igual (follow_mouse de Hyprland).")
            visible: (page.v.focus ?? "ClickToFocus") !== "ClickToFocus"
            font: Kirigami.Theme.smallFont; opacity: 0.7; wrapMode: Text.Wrap
            Layout.maximumWidth: Kirigami.Units.gridUnit * 24
        }

        Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: page.t("Placement", "Colocación") }
        Choice {
            Kirigami.FormData.label: page.t("Placement of new windows:", "Colocación de las ventanas nuevas:")
            options: [["Smart", "Minimal Overlapping", "Mínimo solapamiento"],
                      ["Maximizing", "Maximized", "Maximizada"],
                      ["Random", "Random", "Aleatoria"],
                      ["Centered", "Centered", "Centrada"],
                      ["ZeroCornered", "In Top-Left Corner", "En la esquina superior izquierda"],
                      ["UnderMouse", "Under mouse", "Bajo el ratón"]]
            current: page.v.placement ?? "Smart"
            onPick: (value) => store.write("kwinrc", "Windows", "Placement", value, "placement")
        }

        Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: page.t("Title bar actions", "Acciones de la barra de título") }
        Choice {
            Kirigami.FormData.label: page.t("Double-click:", "Doble clic:")
            options: [["Maximize", "Maximize", "Maximizar"],
                      ["Maximize (vertical only)", "Vertically maximize", "Maximizar verticalmente"],
                      ["Maximize (horizontal only)", "Horizontally maximize", "Maximizar horizontalmente"],
                      ["Minimize", "Minimize", "Minimizar"],
                      ["Close", "Close", "Cerrar"],
                      ["Nothing", "Do nothing", "No hacer nada"]]
            current: page.v.doubleClick ?? "Maximize"
            onPick: (value) => store.write("kwinrc", "Windows", "TitlebarDoubleClickCommand", value, "doubleClick")
        }
        Choice {
            Kirigami.FormData.label: page.t("Mouse wheel:", "Rueda del ratón:")
            options: [["Nothing", "Do nothing", "No hacer nada"],
                      ["Raise/Lower", "Raise/Lower", "Elevar/Bajar"],
                      ["Maximize/Restore", "Maximize/Restore", "Maximizar/Restaurar"],
                      ["Previous/Next Desktop", "Switch to Previous/Next Desktop", "Cambiar al escritorio anterior/siguiente"]]
            current: page.v.wheel ?? "Nothing"
            onPick: (value) => store.write("kwinrc", "MouseBindings", "CommandTitlebarWheel", value, "wheel")
        }

        Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: page.t("Screen edges and snapping", "Bordes de la pantalla y encaje") }
        QQC2.CheckBox {
            Kirigami.FormData.label: page.t("Drag to an edge:", "Arrastrar a un borde:")
            text: page.t("Tile windows to the left and right edges", "Encajar las ventanas en los bordes izquierdo y derecho")
            checked: page.v.quickTile ?? true
            onToggled: store.write("kwinrc", "Windows", "ElectricBorderTiling", checked, "quickTile")
        }
        QQC2.CheckBox {
            text: page.t("Maximize windows dragged to the top edge", "Maximizar las ventanas arrastradas al borde superior")
            checked: page.v.edgeMaximize ?? true
            onToggled: store.write("kwinrc", "Windows", "ElectricBorderMaximize", checked, "edgeMaximize")
        }
        RowLayout {
            Kirigami.FormData.label: page.t("Quarter tiling area:", "Zona de los cuartos:")
            QQC2.Slider {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 10
                from: 0; to: 0.5; stepSize: 0.05
                value: page.v.cornerRatio ?? 0.25
                onMoved: store.write("kwinrc", "Windows", "ElectricBorderCornerRatio", Number(value.toFixed(2)), "cornerRatio")
            }
            QQC2.Label { text: Math.round((page.v.cornerRatio ?? 0.25) * 100) + " %" }
        }
        Zone {
            Kirigami.FormData.label: page.t("Screen edge snap zone:", "Zona de imán de los bordes:")
            current: page.v.borderSnap ?? 10
            onPick: (value) => store.write("kwinrc", "Windows", "BorderSnapZone", value, "borderSnap")
        }
        Zone {
            Kirigami.FormData.label: page.t("Window snap zone:", "Zona de imán de las ventanas:")
            current: page.v.windowSnap ?? 10
            onPick: (value) => store.write("kwinrc", "Windows", "WindowSnapZone", value, "windowSnap")
        }
        Zone {
            Kirigami.FormData.label: page.t("Center snap zone:", "Zona de imán del centro:")
            current: page.v.centerSnap ?? 0
            onPick: (value) => store.write("kwinrc", "Windows", "CenterSnapZone", value, "centerSnap")
        }
        QQC2.CheckBox {
            text: page.t("Snap windows only when overlapping", "Atraer las ventanas sólo cuando se solapan")
            checked: page.v.snapOnlyOverlapping ?? false
            onToggled: store.write("kwinrc", "Windows", "SnapOnlyWhenOverlapping", checked, "snapOnlyOverlapping")
        }
        QQC2.Label {
            Layout.maximumWidth: Kirigami.Units.gridUnit * 24
            wrapMode: Text.Wrap
            font: Kirigami.Theme.smallFont; opacity: 0.7
            text: page.t("Title bar buttons are chosen in Window Decorations; per-application exceptions in Window Rules.",
                         "Los botones de la barra de título se eligen en Decoraciones de ventana; las excepciones por aplicación, en Reglas de ventana.")
        }
    }
}
