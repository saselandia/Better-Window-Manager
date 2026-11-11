/*
    SPDX-FileCopyrightText: 2009 Chani Armitage <chani@kde.org>
    SPDX-FileCopyrightText: 2026 BWM

    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM (F9): el menú del panel de Plasma 6.7.5 (clic derecho en un hueco del panel): el orden de
// ContextMenu::restore() para paneles — «add widgets» (Añadir o gestionar elementos gráficos…,
// libplasma), acciones del contenedor y «configure» (Entrar/Salir del modo de edición).
// «Mostrar alternativas…» es de cada elemento gráfico con alternativas; los de BWM no tienen, así
// que no aparece. El modo de edición y el editor de elementos son los del panel portado (F3).
import QtQuick
import Quickshell
import org.kde.plasma.components as PC3

PC3.Menu {
    id: root
    required property string panelScreen
    readonly property bool editing: PlasmaMenus.panelEditing

    PC3.MenuItem {
        text: MenuI18n.i18n("Add or Manage Widgets…")
        icon.name: "list-add"
        onTriggered: PlasmaMenus.openWidgets(root.panelScreen)
    }
    PC3.MenuSeparator {}
    PC3.MenuItem {
        text: root.editing ? MenuI18n.i18n("Exit Edit Mode") : MenuI18n.i18n("Enter Edit Mode")
        icon.name: "document-edit"
        onTriggered: PlasmaMenus.editModeRequested(root.panelScreen, !root.editing)
    }
}
