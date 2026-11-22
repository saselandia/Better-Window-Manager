// SPDX-License-Identifier: GPL-2.0-or-later
pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import ".."

QQC2.ScrollView {
    id: page
    property var entry
    readonly property QtObject kcm: store
    function t(en, es) { return SettingsState.spanish ? es : en; }
    EffectsStore { id: store }

    ColumnLayout {
        width: page.availableWidth
        spacing: Kirigami.Units.largeSpacing
        QQC2.Label {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            wrapMode: Text.Wrap
            text: page.t("Changes apply when you press Apply. Animation speed also affects KDE applications.",
                         "Los cambios se guardan al pulsar Aplicar. La velocidad de las animaciones también afecta a las aplicaciones KDE.")
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.largeSpacing
            Layout.rightMargin: Kirigami.Units.largeSpacing
            visible: store.error !== ""
            type: Kirigami.MessageType.Error
            text: store.error
            actions: [Kirigami.Action {
                text: page.t("Reload", "Volver a cargar")
                enabled: !store.busy
                onTriggered: store.load()
            }]
        }
        Repeater {
            model: store.fields
            delegate: RowLayout {
                id: row
                required property var modelData
                readonly property var spec: modelData
                readonly property string label: SettingsState.spanish ? spec.label : spec.label_en
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                enabled: store.ready && !store.busy
                QQC2.CheckBox {
                    visible: row.spec.type === "bool"
                    Layout.fillWidth: true
                    text: row.label
                    checked: store.values[row.spec.key] === true
                    onToggled: store.setValue(row.spec.key, checked)
                }
                QQC2.Label {
                    visible: row.spec.type !== "bool"
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: row.label
                }
                QQC2.SpinBox {
                    visible: row.spec.type !== "bool"
                    readonly property int multiplier: Math.pow(10, row.spec.decimals ?? 0)
                    from: Math.round((row.spec.min ?? 0) * multiplier)
                    to: Math.round((row.spec.max ?? 1) * multiplier)
                    stepSize: Math.round((row.spec.step ?? 1) * multiplier)
                    value: Math.round(Number(store.values[row.spec.key]) * multiplier)
                    editable: true
                    textFromValue: (value, locale) => Number(value / multiplier).toLocaleString(locale, 'f', row.spec.decimals ?? 0)
                    valueFromText: (text, locale) => Math.round(Number.fromLocaleString(locale, text) * multiplier)
                    validator: DoubleValidator {
                        bottom: row.spec.min ?? 0
                        top: row.spec.max ?? 1
                        decimals: row.spec.decimals ?? 0
                    }
                    onValueModified: store.setValue(row.spec.key, value / multiplier)
                }
            }
        }
        QQC2.Label {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            wrapMode: Text.Wrap
            font: Kirigami.Theme.smallFont
            text: page.t("Automatic scale duration is 200 ms before applying the duration factor. Panel and popup effects use Hyprland's layer animations.",
                         "La duración automática de escala es de 200 ms antes de aplicar el factor de duración. Los efectos de paneles y ventanas emergentes usan las animaciones de capas de Hyprland.")
        }
    }
}
