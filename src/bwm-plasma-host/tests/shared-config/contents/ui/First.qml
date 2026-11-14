// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
Column {
    property alias cfg_enabled: toggle.checked
    property alias cfg_amount: amount.value
    property alias cfg_caption: caption.text
    property bool cfg_enabledDefault
    property bool cfg_enabledImmutable
    QQC2.CheckBox { id: toggle; objectName: "sharedToggle"; text: "Enabled" }
    QQC2.SpinBox { id: amount; objectName: "sharedAmount"; from: 0; to: 100 }
    QQC2.TextField { id: caption; objectName: "sharedCaption" }
}
