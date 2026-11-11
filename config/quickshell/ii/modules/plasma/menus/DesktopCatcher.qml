/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM (F9): recoge el clic derecho en el fondo del escritorio de Breeze para abrir el menú del
// escritorio. En Breeze el fondo lo pinta swww, que no recibe clics: una capa transparente en
// «bottom» (debajo de las ventanas, encima del fondo) por pantalla. Sólo actúa con el botón derecho;
// el resto de pulsaciones no hace nada, como pulsar en un escritorio vacío.
import QtQuick
import Quickshell
import Quickshell.Wayland

Scope {
    Variants {
        model: Quickshell.screens
        PanelWindow {
            required property var modelData
            screen: modelData
            color: "transparent"
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "quickshell:plasmaDesktop"
            WlrLayershell.layer: WlrLayer.Bottom
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            anchors { top: true; bottom: true; left: true; right: true }
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onPressed: mouse => PlasmaMenus.openLocal("desktop", modelData.name, mouse.x, mouse.y, {})
            }
        }
    }
}
