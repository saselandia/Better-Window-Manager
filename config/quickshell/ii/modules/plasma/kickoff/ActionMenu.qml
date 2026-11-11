/*
    SPDX-FileCopyrightText: 2013 Aurélien Gâteau <agateau@kde.org>
    SPDX-FileCopyrightText: 2014-2015 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2021 Mikel Johnson <mikel5764@gmail.com>
    SPDX-FileCopyrightText: 2021 Noah Davis <noahadvs@gmail.com>
    SPDX-FileCopyrightText: 2024 ivan tkachenko <me@ratijas.tk>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound
pragma Singleton // NOTE: Singletons are shared between all instances of a plasmoid

import QtQuick
import Quickshell
import Quickshell.Io
import org.kde.plasma.components as PC3
import "code/tools.js" as Tools

// BWM: el original usa PlasmaExtras.Menu, que es un QMenu (Qt Widgets). Sin QApplication hace caer
// Quickshell, y con ella (shell.qml usa UseQApplication) Qt no puede abrir su ventana emergente
// desde una capa de layer-shell («Failed to create grabbing popup … transientParent»). Misma interfaz (actionList, plasmoid, menu.visualParent,
// menu.open(x, y), menu.openRelative()) con un PC3.Menu de QtQuick creado sobre el elemento que
// lo abre. Las entradas son las del modelo de Kicker (título, separador, submenús, marcables) y
// se activan igual, con Tools.triggerAction sobre el modelo y la fila del elemento.
Singleton {
    id: root

    property var actionList: null

    // Only one action menu can be open at a time, so this should be safe to use.
    property Item plasmoid: null

    readonly property QtObject menu: QtObject {
        property Item visualParent: null
        property var current: null

        function _show(x, y) {
            if (current)
                current.close();
            if (!visualParent || !root.actionList)
                return;
            current = menuComponent.createObject(visualParent);
            root.fill(current, root.actionList, visualParent);
            current.popup(visualParent, x, y);
        }
        function open(x, y) { _show(x, y); }
        function openRelative() { _show(0, visualParent ? visualParent.height : 0); }
    }

    // «Editar aplicación…» abre kmenuedit (paquete kde-plasma/kmenuedit): sólo si está instalado
    property bool hasMenuEditor: false
    readonly property Process __menuEditorCheck: Process {
        running: true
        command: ["sh", "-c", "command -v kmenuedit"]
        onExited: (code, status) => root.hasMenuEditor = code === 0
    }

    // Sin separadores al principio, al final ni seguidos (QMenu los oculta solo)
    function cleaned(actions) {
        const out = [];
        for (const entry of actions) {
            if (!entry || (entry.actionId === "editApplication" && !root.hasMenuEditor))
                continue;
            if (entry.type === "separator" && (out.length === 0 || out[out.length - 1].type === "separator"))
                continue;
            out.push(entry);
        }
        while (out.length && out[out.length - 1].type === "separator")
            out.pop();
        return out;
    }

    function fill(menu, actions, source) {
        for (const entry of cleaned(Array.from(actions))) {
            if (entry.type === "separator") {
                menu.addItem(separatorComponent.createObject(menu.contentItem));
            } else if (entry.subActions) {
                const sub = subMenuComponent.createObject(menu.contentItem, { title: entry.text ?? "" });
                fill(sub, entry.subActions, source);
                menu.addMenu(sub);
            } else {
                menu.addItem(itemComponent.createObject(menu.contentItem, { entry: entry, source: source }));
            }
        }
    }

    Component {
        id: menuComponent
        PC3.Menu {
            onClosed: destroy()
        }
    }
    Component {
        id: subMenuComponent
        PC3.Menu {}
    }
    Component {
        id: separatorComponent
        PC3.MenuSeparator {}
    }
    Component {
        id: itemComponent

        PC3.MenuItem {
            id: menuItem
            property var entry
            property Item source

            text: entry.text ?? ""
            enabled: entry.type !== "title" && (entry.enabled ?? true)
            font.bold: entry.type === "title"
            icon.name: typeof entry.icon === "string" ? entry.icon : ""
            icon.source: typeof entry.icon === "string" ? "" : (entry.icon ?? "")
            checkable: entry.checkable ?? false
            checked: entry.checked ?? false

            onClicked: {
                const modelActionTriggered = Tools.triggerAction(
                    source.view.model,
                    source.index,
                    entry.actionId,
                    entry.actionArgument
                )
                // close early (if marked as such) to be more responsive to user input
                if (modelActionTriggered && root.plasmoid && root.plasmoid.hideOnWindowDeactivate) {
                    root.plasmoid.expanded = false
                }
            }
        }
    }
}
