/*
    SPDX-FileCopyrightText: 2014 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2023 Alexander Lohnau <alexander.lohnau@gmx.de>

    SPDX-License-Identifier: LGPL-2.0-only
*/
// BWM: the QML that kcmutils v6.29.0 builds in src/kcmoduleqml.cpp (KCModuleQml) to show a QML KCM
// inside a widget, and the C++ wiring around it (initial page, sub pages, pagePushed/pageRemoved,
// currentIndex), here in QML around KcmHost from org.bwm.kcm (src/bwm-kcmhost), which loads the
// module in this window's engine. Its own file, loaded by a Loader, so a missing org.bwm.kcm only
// affects KCM pages.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami 2 as Kirigami
import org.bwm.kcm

Kirigami.ApplicationItem {
    id: root
    property var entry
    readonly property QtObject kcm: host.kcm
    readonly property string error: host.error
    function pop() { host.pop(); }

    implicitWidth: Math.max(pageStack.implicitWidth, Kirigami.Units.gridUnit * 36)
    implicitHeight: Math.max(pageStack.implicitHeight, Kirigami.Units.gridUnit * 20)
    activeFocusOnTab: true

    KcmHost {
        id: host
        visible: false // BWM: only loads the module; its pages live in pageStack
        module: root.entry ? root.entry.module : ""
        onKcmChanged: root.showModule()
    }

    QQC2.ToolButton {
        id: toolButton
        visible: false
        icon.name: "go-previous"
    }

    pageStack.separatorVisible: pageStack.depth > 0 && (pageStack.items[0].sidebarMode ?? false)
    pageStack.globalToolBar.style: Kirigami.ApplicationHeaderStyle.ToolBar
    pageStack.globalToolBar.showNavigationButtons: Kirigami.ApplicationHeaderStyle.ShowBackButton

    pageStack.columnView.columnResizeMode: pageStack.items.length > 0 && (pageStack.items[0].Kirigami.ColumnView.fillWidth || pageStack.items.filter(item => item.visible).length === 1)
        ? Kirigami.ColumnView.SingleColumn
        : Kirigami.ColumnView.FixedColumns

    pageStack.defaultColumnWidth: kcm && kcm.columnWidth > 0 ? kcm.columnWidth : Kirigami.Units.gridUnit * 15

    footer: null
    Keys.onReturnPressed: event => {
        event.accepted = true
    }
    Keys.onEnterPressed: event => {
        event.accepted = true
    }

    // BWM: KCModuleQml's C++ (initialPage, existing sub pages, sidebarMode) in QML
    function showModule() {
        pageStack.clear();
        if (!host.kcm || !host.mainUi)
            return;
        pageStack.push(host.mainUi);
        for (let i = 0; i < host.depth - 1; i++) {
            pageStack.push(host.subPage(i));
            if (host.mainUi.sidebarMode ?? false) {
                pageStack.currentIndex = 0;
                host.kcm.currentIndex = 0;
            }
        }
    }
    Connections {
        target: host.kcm
        function onPagePushed(page) { root.pageStack.push(page); }
        function onPageRemoved() { root.pageStack.pop(); }
        function onCurrentIndexChanged() { root.pageStack.currentIndex = host.kcm.currentIndex; }
    }
    Connections {
        target: root.pageStack
        function onCurrentIndexChanged() { if (host.kcm) host.kcm.currentIndex = root.pageStack.currentIndex; }
    }
}
