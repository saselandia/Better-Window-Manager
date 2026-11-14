// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as QQC2
Column {
    id: root
    required property string title
    required property string cfg_greeting
    property string completionGreeting
    Component.onCompleted: completionGreeting = cfg_greeting
    QQC2.TextField { text: root.cfg_greeting; onTextEdited: root.cfg_greeting = text }
}
