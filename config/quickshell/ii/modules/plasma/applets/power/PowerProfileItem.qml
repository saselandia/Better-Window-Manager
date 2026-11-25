/*
    SPDX-FileCopyrightText: 2021 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2021 David Redondo <kde@david-redondo.de>
    SPDX-FileCopyrightText: 2024 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later
*/
// BWM: Plasma 6.7.5 PowerProfileItem adapted to Quickshell.Services.UPower.PowerProfiles.
// Hidden when no power-profiles-daemon / tuned-ppd service is present on the system bus.
import QtQuick
import QtQuick.Layouts
import Quickshell.Services.UPower
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3

ColumnLayout {
    id: root
    objectName: "plasma-power-profile"

    property var backend: PowerProfiles
    property var translator: null
    property bool readOnly: false

    readonly property bool hasPerformance: Boolean(backend?.hasPerformanceProfile)
    readonly property int maxIndex: hasPerformance ? 2 : 1
    readonly property int activeIndex: {
        const p = backend?.profile;
        if (p === PowerProfile.Performance && hasPerformance) return 2;
        if (p === PowerProfile.PowerSaver) return 0;
        return 1;
    }

    function tr(text) {
        return translator && typeof translator.i18n === "function" ? translator.i18n(text) : qsTr(text);
    }

    function profileLabel(index) {
        if (index === 0) return tr("Power Save");
        if (index === 2) return tr("Performance");
        return tr("Balanced");
    }

    function degradationText(reason) {
        if (reason === PerformanceDegradationReason.LapDetected)
            return tr("Performance mode has been disabled to reduce heat generation because the computer has detected that it may be sitting on your lap.");
        if (reason === PerformanceDegradationReason.HighTemperature)
            return tr("Performance mode has been disabled to reduce heat generation because the computer is running too hot.");
        return "";
    }

    spacing: Kirigami.Units.smallSpacing

    RowLayout {
        Layout.fillWidth: true
        spacing: Kirigami.Units.gridUnit

        Kirigami.Icon {
            source: "speedometer"
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: root.tr("Power Profile")
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                }
                PlasmaComponents3.Label {
                    objectName: "plasma-power-profile-label"
                    text: root.profileLabel(slider.value)
                    textFormat: Text.PlainText
                    opacity: 0.75
                }
            }

            PlasmaComponents3.Slider {
                id: slider
                objectName: "plasma-power-profile-slider"
                Layout.fillWidth: true
                from: 0
                to: root.maxIndex
                stepSize: 1
                snapMode: PlasmaComponents3.Slider.SnapAlways
                value: root.activeIndex
                enabled: !root.readOnly && !!root.backend
                onMoved: {
                    if (!root.backend || root.readOnly) return;
                    const idx = Math.round(value);
                    root.backend.profile = idx === 0
                        ? PowerProfile.PowerSaver
                        : (idx === 2 && root.hasPerformance ? PowerProfile.Performance : PowerProfile.Balanced);
                }
            }

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents3.Label {
                    text: root.tr("Power Save")
                    font: Kirigami.Theme.smallFont
                    textFormat: Text.PlainText
                    opacity: 0.75
                }
                Item { Layout.fillWidth: true }
                PlasmaComponents3.Label {
                    visible: root.hasPerformance
                    text: root.tr("Balanced")
                    font: Kirigami.Theme.smallFont
                    textFormat: Text.PlainText
                    opacity: 0.75
                }
                Item { visible: root.hasPerformance; Layout.fillWidth: true }
                PlasmaComponents3.Label {
                    text: root.hasPerformance ? root.tr("Performance") : root.tr("Balanced")
                    font: Kirigami.Theme.smallFont
                    textFormat: Text.PlainText
                    opacity: 0.75
                }
            }

            InhibitionHint {
                objectName: "plasma-power-degradation-hint"
                Layout.fillWidth: true
                visible: text.length > 0
                iconSource: "dialog-warning"
                text: root.degradationText(root.backend?.degradationReason ?? PerformanceDegradationReason.None)
            }

            Repeater {
                model: root.backend?.holds ?? []
                delegate: InhibitionHint {
                    required property var modelData
                    Layout.fillWidth: true
                    iconSource: "dialog-information"
                    text: (modelData.applicationId || root.tr("An application")) + (modelData.reason ? (": " + modelData.reason) : "")
                }
            }
        }
    }
}
