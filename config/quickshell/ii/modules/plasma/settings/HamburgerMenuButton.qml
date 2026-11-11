/*
   SPDX-FileCopyrightText: 2017 Marco Martin <mart@kde.org>
   SPDX-FileCopyrightText: 2023 ivan tkachenko <me@ratijas.tk>

   SPDX-License-Identifier: LGPL-2.0-only
*/

import QtQuick 2.15
import QtQuick.Controls 2.15 as QQC2

import org.kde.kirigami 2.20 as Kirigami
import Quickshell

// BWM: the C++ action menu (Highlight Changed Settings, Help, About…) becomes a QQC2.Menu here

QQC2.ToolButton {
    icon.name: "application-menu"

    checkable: true
    checked: actionMenu.visible
    onToggled: if (checked) actionMenu.popup(this, 0, height)
    QQC2.Menu {
        id: actionMenu
        QQC2.MenuItem {
            text: SettingsI18n.i18n("Highlight Changed Settings")
            icon.name: "draw-highlight"
            checkable: true
            checked: SettingsState.defaultsIndicatorsVisible
            onToggled: SettingsState.defaultsIndicatorsVisible = checked
        }
        QQC2.MenuSeparator {}
        QQC2.MenuItem {
            text: SettingsState.spanish ? "Abrir el archivo de configuración de BWM" : "Open BWM configuration file"
            icon.name: "document-edit"
            onTriggered: Qt.openUrlExternally("file://" + Quickshell.env("HOME") + "/.config/illogical-impulse/config.json")
        }
    }

    Accessible.role: Accessible.ButtonMenu
    Accessible.name: SettingsI18n.i18n("Show menu")
    QQC2.ToolTip.text: Accessible.name
    QQC2.ToolTip.visible: hovered && !pressed
    QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
}
