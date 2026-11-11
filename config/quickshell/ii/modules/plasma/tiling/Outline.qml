/*
    SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2017 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
*/
// BWM: port of KWin v6.7.5 src/qml/outline/plasma/outline.qml.
// Workspace/outline context replaced by Hyprland logical geometry through IPC; no input.
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import qs.services
import "../theme"

Scope {
    id: root
    property var geometry: null
    property bool active: false
    property double sequence: 0
    property bool animate: false
    IpcHandler {
        target: "plasmaOutline"
        function display(payload: string): void {
            try {
                const g = JSON.parse(payload);
                if (![g.x,g.y,g.width,g.height,...g.area].every(Number.isFinite) || g.width<=0 || g.height<=0) return;
                if (!Number.isFinite(g.sequence) || g.sequence<root.sequence) return;
                root.sequence=g.sequence; root.animate=root.active;
                root.geometry=g; root.active=true;
            } catch (e) { console.warn("Breeze outline: " + e); }
        }
        function hide(serial: string): void {
            const n=Number(serial);
            if (Number.isFinite(n) && n>=root.sequence) {root.sequence=n;root.active=false;}
        }
        function inspect(): string { return JSON.stringify({active:root.active,sequence:root.sequence,geometry:root.geometry}); }
    }
    Variants {
        model: Quickshell.screens
        PanelWindow {
            id: win
            required property var modelData
            readonly property var monitor: HyprlandData.monitors.find(m=>m.name===modelData.name)
            readonly property var g: root.geometry
            readonly property real ox: monitor?.x ?? 0
            readonly property real oy: monitor?.y ?? 0
            screen: modelData
            visible: root.active && !!g && !!monitor && g.x<ox+width && g.x+g.width>ox && g.y<oy+height && g.y+g.height>oy
            anchors { top:true; bottom:true; left:true; right:true }
            color: "transparent"
            mask: Region {}
            exclusionMode: ExclusionMode.Ignore
            WlrLayershell.namespace: "quickshell:plasmaOutline"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            KSvg.FrameSvgItem {
                id: svg
                x: (win.g?.x ?? 0)-win.ox
                y: (win.g?.y ?? 0)-win.oy
                width: win.g?.width ?? 0
                height: win.g?.height ?? 0
                imagePath: "widgets/translucentbackground"
                enabledBorders: {
                    if (!win.g) return KSvg.FrameSvgItem.AllBorders;
                    const a=win.g.area;
                    const left=win.g.x===a[0], right=win.g.x+win.g.width===a[0]+a[2];
                    const top=win.g.y===a[1], bottom=win.g.y+win.g.height===a[1]+a[3];
                    if (left&&right&&top&&bottom) return KSvg.FrameSvgItem.AllBorders;
                    let borders=KSvg.FrameSvgItem.AllBorders;
                    if(left) borders &= ~KSvg.FrameSvgItem.LeftBorder;
                    if(right) borders &= ~KSvg.FrameSvgItem.RightBorder;
                    if(top) borders &= ~KSvg.FrameSvgItem.TopBorder;
                    if(bottom) borders &= ~KSvg.FrameSvgItem.BottomBorder;
                    return borders;
                }
                Behavior on x { enabled:root.animate; NumberAnimation {duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic} }
                Behavior on y { enabled:root.animate; NumberAnimation {duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic} }
                Behavior on width { enabled:root.animate; NumberAnimation {duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic} }
                Behavior on height { enabled:root.animate; NumberAnimation {duration:Kirigami.Units.longDuration;easing.type:Easing.InOutCubic} }
            }
        }
    }
}
