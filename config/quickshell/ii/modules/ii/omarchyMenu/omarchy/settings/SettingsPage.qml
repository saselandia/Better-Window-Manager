import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui as Ui
import qs.services
import "../../../../settings/retro" as Retro

// Complex existing controls live inside the same Omarchy card and layer surface.
// They never open an ApplicationWindow or change the compositor's window focus.
Item {
    id: root
    required property var controller
    property alias pageItem: pageLoader.item
    property var sections: []
    property int sectionIndex: 0
    readonly property bool nativeDisplay: controller.page?.[0] === "display"
    readonly property var focusedControl: Window.window ? Window.window.activeFocusItem : null
    readonly property bool controlFocused: within(pageLoader.item, focusedControl)
    function within(parent, item) {
        if (!parent) return false;
        for (let it = item; it; it = it.parent) if (it === parent) return true;
        return false;
    }
    onFocusedControlChanged: Qt.callLater(revealFocus)
    function refresh() {
        const list = [];
        function visit(item) {
            if (!item || !item.visible) return;
            if (item.title !== undefined && item.icon !== undefined && item.contentData !== undefined && item.height > 0) { list.push(item); return; }
            for (const child of item.children ?? []) visit(child);
        }
        visit(pageLoader.item?.contentItem);
        sections = list;
    }
    function goSection(index) {
        if (!sections.length) return;
        sectionIndex = Math.max(0, Math.min(sections.length - 1, index));
        const page = pageLoader.item;
        const top = sections[sectionIndex].mapToItem(page.contentItem, 0, 0).y;
        page.contentY = Math.max(0, Math.min(page.contentHeight - page.height, top - 20));
        Qt.callLater(focusPage);
    }
    function focusPage() {
        if (!pageLoader.item) return;
        if (nativeDisplay) { pageLoader.item.forceActiveFocus(); return; }
        const section = sections[sectionIndex] ?? pageLoader.item;
        let item = section.nextItemInFocusChain(true);
        const seen = new Set();
        while (item && !seen.has(item)) {
            seen.add(item);
            if (within(section, item) && item.activeFocusOnTab && item.enabled && item.visible) { item.forceActiveFocus(Qt.TabFocusReason); return; }
            item = item.nextItemInFocusChain(true);
        }
    }
    function revealFocus() {
        const page = pageLoader.item;
        if (!controlFocused || !page || page.contentY === undefined) return;
        const section = sections.findIndex(s => within(s, focusedControl));
        if (section >= 0) sectionIndex = section;
        const top = focusedControl.mapToItem(page.contentItem, 0, 0).y;
        const bottom = top + Math.min(focusedControl.height, page.height - 32);
        if (top < page.contentY + 12) page.contentY = Math.max(0, top - 20);
        else if (bottom > page.contentY + page.height - 12) page.contentY = Math.min(Math.max(0, page.contentHeight - page.height), bottom - page.height + 20);
    }
    Keys.priority: Keys.AfterItem
    Keys.onEscapePressed: event => { controller.back(); event.accepted = true; }
    Shortcut { enabled: !root.nativeDisplay; sequence: "Alt+Down"; onActivated: root.goSection(root.sectionIndex + 1) }
    Shortcut { enabled: !root.nativeDisplay; sequence: "Alt+Up"; onActivated: root.goSection(root.sectionIndex - 1) }
    Loader { active: !root.nativeDisplay; sourceComponent: Component { Retro.SettingsStyle { } } }
    Component.onDestruction: MaterialThemeLoader.reapplyTheme()
    ColumnLayout {
        anchors.fill: parent
        spacing: Style.spacing.sm
        RowLayout {
            visible: !root.nativeDisplay
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: root.sections.length ? (root.sectionIndex + 1) + " / " + root.sections.length + " · " + root.sections[root.sectionIndex].title : root.controller.page?.[2] ?? ""
                color: Commons.Color.menu.text
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.body
                elide: Text.ElideRight
            }
            Ui.Button { text: "‹"; tooltipText: "Sección anterior · Alt+↑"; focusable: true; enabled: root.sectionIndex > 0; onClicked: root.goSection(root.sectionIndex - 1) }
            Ui.Button { text: "›"; tooltipText: "Sección siguiente · Alt+↓"; focusable: true; enabled: root.sectionIndex < root.sections.length - 1; onClicked: root.goSection(root.sectionIndex + 1) }
        }
        Loader {
            id: pageLoader
            clip: true
            Layout.fillWidth: true
            Layout.fillHeight: true
            function loadPage() {
                if (!root.controller.page) return;
                setSource(root.nativeDisplay ? Qt.resolvedUrl("DisplaySettings.qml") : Qt.resolvedUrl("../../../../settings/" + root.controller.page[4]), root.nativeDisplay ? {controller:root.controller} : {});
            }
            Component.onCompleted: loadPage()
            Connections { target: root.controller; function onPageChanged() { pageLoader.loadPage(); } }
            onLoaded: { refreshTimer.restart(); Qt.callLater(root.focusPage); }
            Rectangle {
                readonly property point position: {
                    const scroll = pageLoader.item?.contentY;
                    return root.controlFocused ? root.focusedControl.mapToItem(pageLoader, 0, 0) : Qt.point(0, 0);
                }
                visible: !root.nativeDisplay && root.controlFocused && width > 4 && height > 4
                x: position.x - 2
                y: position.y - 2
                width: root.controlFocused ? root.focusedControl.width + 4 : 0
                height: root.controlFocused ? root.focusedControl.height + 4 : 0
                color: "transparent"
                border.width: 1
                border.color: Commons.Color.accent
                z: 2
            }
        }
        Binding { target: pageLoader.item; property: "baseWidth"; value: Math.max(400, pageLoader.width - 48); when: !!pageLoader.item && pageLoader.item.baseWidth !== undefined }
        Binding { target: pageLoader.item; property: "bottomContentPadding"; value: 36; when: !!pageLoader.item && pageLoader.item.bottomContentPadding !== undefined }
        Connections { target: pageLoader.item; ignoreUnknownSignals: true; function onContentHeightChanged() { refreshTimer.restart(); } }
    }
    Timer { id: refreshTimer; interval: 60; onTriggered: root.refresh() }
}
