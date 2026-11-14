// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
Column {
    property alias cfg_enabled: toggle.checked
    property alias cfg_amount: amount.value
    property bool configurationValid: true
    QQC2.CheckBox { id: toggle; objectName: "sharedToggle"; text: "Same enabled setting" }
    QQC2.SpinBox { id: amount; objectName: "sharedAmount"; from: 0; to: 100 }
}
