// BWM: D-Bus menus rendered by PC3 inside MenuHost's overlay layer, including nested submenus.
import QtQuick
import QtQml.Models
import Quickshell
import org.kde.plasma.components as PC3
import qs.modules.plasma.menus
PC3.Menu {
    id: menu
    property bool pendingOpen: false
    property var handle: null
    property var mockEntries: null
    readonly property var entries: mockEntries ?? opener.children.values
    delegate: PC3.MenuItem {
        width: parent ? parent.width : 0
    }
    function openFor(value, button) {
        if (button?.QsWindow?.window) {
            PlasmaMenus.openFor("tray", button, button.tray?.edge || "bottom", { trayMenu: value });
            return;
        }
        parent = button;
        pendingOpen = true;
        handle = value?.menu !== undefined ? value.menu : value;
        mockEntries = value?.mockEntries ?? null;
        tryOpen();
    }
    function tryOpen() { if (pendingOpen && entries.length > 0) { pendingOpen = false; Qt.callLater(() => popup()); } }
    onEntriesChanged: tryOpen()
    QsMenuOpener { id: opener; menu: menu.handle }
    Component { id: separatorComponent; PC3.MenuSeparator {} }
    Component {
        id: entryComponent
        PC3.MenuItem {
            required property var modelData
            text: modelData.text ?? ""
            enabled: modelData.enabled ?? true
            checkable: (modelData.buttonType ?? 0) !== 0
            checked: (modelData.checkState ?? Qt.Unchecked) !== Qt.Unchecked
            icon.source: modelData.icon ?? ""
            onTriggered: {
                modelData.triggered();
                PlasmaMenus.close();
            }
        }
    }
    Instantiator {
        model: menu.entries
        delegate: QtObject {
            id: wrapper
            required property var modelData
            required property int index
            property var created: null
            readonly property bool isSub: modelData?.hasChildren ?? false
            Component.onCompleted: {
                const hostItem = menu.parent ?? menu;
                if (isSub) {
                    const comp = Qt.createComponent(Qt.resolvedUrl("TrayMenu.qml"));
                    created = comp.createObject(hostItem, {
                        title: modelData.text ?? "",
                        handle: modelData.mockEntries ? null : modelData,
                        mockEntries: modelData.mockEntries ?? null
                    });
                    if (created) menu.insertMenu(index, created);
                } else if (modelData?.isSeparator) {
                    created = separatorComponent.createObject(menu.contentItem);
                    menu.insertItem(index, created);
                } else {
                    created = entryComponent.createObject(menu.contentItem, { modelData: modelData });
                    menu.insertItem(index, created);
                }
            }
            Component.onDestruction: {
                if (!created) return;
                if (isSub) menu.removeMenu(created);
                else menu.removeItem(created);
                created.destroy();
            }
        }
    }
}
