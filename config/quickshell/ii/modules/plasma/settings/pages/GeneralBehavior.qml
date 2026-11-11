// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import ".."

/**
 * BWM F11: «General Behavior» as Plasma's kcm_workspace (plasma-desktop, not installed here): how a
 * click opens files and the animation speed. Both live in kdeglobals [KDE]; the F2 bridge turns the
 * animation factor into Hyprland's animation speeds and KDE apps follow SingleClick themselves.
 */
QQC2.ScrollView {
    id: page
    property var entry
    function t(en, es) { return SettingsState.spanish ? es : en; }
    KdeSettingsStore { id: store }
    readonly property real factor: store.values.animationFactor ?? 1

    Kirigami.FormLayout {
        width: page.availableWidth
        enabled: store.ready

        Item { Kirigami.FormData.isSection: true }
        QQC2.RadioButton {
            Kirigami.FormData.label: page.t("Clicking files or folders:", "Al pulsar archivos o carpetas:")
            text: page.t("Selects them", "Los selecciona")
            checked: !(store.values.singleClick ?? false)
            onToggled: if (checked) store.write("kdeglobals", "KDE", "SingleClick", "false", "singleClick")
        }
        QQC2.RadioButton {
            text: page.t("Opens them", "Los abre")
            checked: store.values.singleClick ?? false
            onToggled: if (checked) store.write("kdeglobals", "KDE", "SingleClick", "true", "singleClick")
        }
        QQC2.Label {
            text: page.t("Select by clicking on the item's selection marker", "Para seleccionar, pulsa en el marcador de selección del elemento")
            visible: store.values.singleClick ?? false
            font: Kirigami.Theme.smallFont
            opacity: 0.7
        }

        Item { Kirigami.FormData.isSection: true }
        RowLayout {
            Kirigami.FormData.label: page.t("Animation speed:", "Velocidad de las animaciones:")
            QQC2.Label { text: page.t("Slow", "Lenta") }
            QQC2.Slider {
                id: speed
                Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                // kcm_workspace: factor = 1/2^value; the rightmost stop is «Instant» (factor 0)
                from: -4; to: 4; stepSize: 0.5; snapMode: QQC2.Slider.SnapAlways
                value: page.factor <= 0 ? 4 : Math.max(-4, Math.min(3.5, -Math.log2(page.factor)))
                onMoved: {
                    const f = value >= 4 ? 0 : Math.pow(2, -value);
                    store.write("kdeglobals", "KDE", "AnimationDurationFactor", Number(f.toFixed(4)), "animationFactor");
                }
            }
            QQC2.Label { text: page.t("Instant", "Instantánea") }
        }
    }
}
