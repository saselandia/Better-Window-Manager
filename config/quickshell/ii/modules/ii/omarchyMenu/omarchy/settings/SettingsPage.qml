import QtQuick

// The only graphical settings view is the monitor layout. All other settings are menu rows.
Item {
    id: root
    required property var controller
    property alias pageItem: pageLoader.item
    Loader {
        id: pageLoader
        anchors.fill: parent
        sourceComponent: DisplaySettings { controller: root.controller }
        onLoaded: Qt.callLater(function() { item.forceActiveFocus(); })
    }
}
