// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
Column {
    id: root
    required property string title
    required property string cfg_greeting
    required property int cfg_amount
    property int cfg_amountDefault
    property bool cfg_amountImmutable
    property string completionGreeting
    property int completionAmount
    property string completionTitle
    property var owner: plasmoid
    property string localizedText: i18nc("@info", "Module fixture")
    Component.onCompleted: {
        completionGreeting = cfg_greeting;
        completionAmount = cfg_amount;
        completionTitle = title;
    }
    QQC2.TextField { text: root.cfg_greeting; onTextEdited: root.cfg_greeting = text }
    QQC2.SpinBox { from: 0; to: 100; value: root.cfg_amount; onValueModified: root.cfg_amount = value }
}
