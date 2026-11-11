/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM: entradas generadas de un modelo dentro de un PC3.Menu (escritorios, pantallas, acciones del
// .desktop…). Un Repeater no sirve dentro de un Menu de QtQuick; se insertan delante de `before`
// (o al final), en el orden del modelo, como los addAction de los QMenu de KWin y Plasma.
import QtQuick
import QtQml.Models

Instantiator {
    id: root

    required property var menu
    property var before: null       // elemento del menú delante del que van (null = al final)

    function indexFor(i) {
        const menuRef = root.menu;
        if (!root.before)
            return menuRef.count;
        for (let k = 0; k < menuRef.count; ++k)
            if (menuRef.itemAt(k) === root.before)
                return k;
        return menuRef.count;
    }
    onObjectAdded: (index, object) => root.menu.insertItem(root.indexFor(index), object)
    onObjectRemoved: (index, object) => root.menu.removeItem(object)
}
