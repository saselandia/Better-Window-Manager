/*
    SPDX-FileCopyrightText: 2009 Chani Armitage <chani@kde.org>
    SPDX-FileCopyrightText: 2026 BWM

    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM (F9): el menú del escritorio (clic derecho en el fondo) de Plasma 6.7.5: el complemento de
// acciones «contextmenu» del contenedor (plasma-workspace/containmentactions/contextmenu/root.cpp)
// con el orden de ContextMenu::restore(): Abrir terminal, —, Bloquear la pantalla, Mostrar la
// pantalla de salida, —, acciones del fondo (Abrir la imagen de fondo), —, Escritorio y fondo,
// Configuración de la pantalla.
// Adaptado a BWM: en Plasma Abrir terminal, Bloquear y Salir vienen desactivados de fábrica; aquí
// están, como pide el plan. Sin elementos gráficos en el escritorio ni actividades: no aparecen
// «Añadir o gestionar elementos gráficos», el modo de edición del escritorio ni KRunner.
// «Escritorio y fondo» abre el selector de fondos de Breeze; «Configuración de la pantalla», la
// página de pantallas de los ajustes comunes (KScreen no controla Hyprland).
import QtQuick
import Quickshell
import qs
import qs.modules.common
import org.kde.plasma.components as PC3

PC3.Menu {
    id: root
    readonly property string scripts: Quickshell.env("HOME") + "/.config/hypr/scripts/"
    readonly property string wallpaper: Config.options.background?.wallpaperPath ?? ""
    function trc(context, text) { return MenuI18n.i18nc(context, text); }

    PC3.MenuItem {
        text: MenuI18n.i18n("Open Terminal")
        icon.name: "utilities-terminal"
        onTriggered: Quickshell.execDetached([root.scripts + "bwm-terminal"])
    }
    PC3.MenuSeparator {}
    PC3.MenuItem {
        text: root.trc("plasma_containmentactions_contextmenu", "Lock Screen")
        icon.name: "system-lock-screen"
        onTriggered: Quickshell.execDetached([root.scripts + "bwm-power", "lock"])
    }
    PC3.MenuItem {
        text: root.trc("plasma_containmentactions_contextmenu", "Show Logout Screen")
        icon.name: "system-log-out"
        onTriggered: GlobalStates.sessionOpen = true
    }
    PC3.MenuSeparator {}
    PC3.MenuItem {
        // Acción del fondo de imagen (plasma_wallpaper_org.kde.image)
        text: MenuI18n.i18n("Open Wallpaper Image")
        icon.name: "document-open"
        visible: root.wallpaper !== ""; height: visible ? implicitHeight : 0
        onTriggered: Quickshell.execDetached(["xdg-open", root.wallpaper])
    }
    PC3.MenuSeparator {}
    PC3.MenuItem {
        text: root.trc("@action:inmenu opens config dialog", "Desktop and Wallpaper")
        icon.name: "preferences-desktop-wallpaper"
        onTriggered: Quickshell.execDetached([root.scripts + "wallpaper-picker.sh"])
    }
    PC3.MenuItem {
        text: root.trc("plasma_containmentactions_contextmenu", "Display Configuration")
        icon.name: "preferences-desktop-display-randr"
        onTriggered: Quickshell.execDetached([root.scripts + "open-settings.sh", "display"])
    }
}
