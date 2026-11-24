/*
    SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2014 Sebastian Kügler <sebas@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

// BWM: ImageItemDelegate.qml of plasma-workspace 6.7.5 (klipper/declarative/qml). Klipper's
// HistoryModel gives the image as `decoration`; here the cliphist entry
// ("<id>\t[[ binary data … png 800x600 ]]") is decoded once into a private file under
// $XDG_RUNTIME_DIR (mode 0700, removed with the row) and shown with the original layout.
// The drag of the original (text/uri-list) is kept disabled like the other BWM delegates.
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

import org.kde.kirigami as Kirigami

ClipboardItemDelegate {
    id: menuItem
    objectName: "plasma-clipboard-image"
    type: 4 // HistoryItemType::Image: no QR code or edit buttons

    required property string entry
    property string backendBinary: "cliphist"
    readonly property int entryId: Number((/^(\d+)\t/.exec(menuItem.entry) ?? [0, 0])[1])
    readonly property size imageSize: {
        const m = /(\d+)x(\d+)\s*\]\]\s*$/.exec(menuItem.entry);
        return m ? Qt.size(Number(m[1]), Number(m[2])) : Qt.size(1, 1);
    }
    readonly property string decodeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/bwm-plasma-clipboard"
    readonly property string decodePath: `${decodeDir}/${entryId}`
    property url decoration: ""

    model: ({ display: "", decoration: menuItem.decoration, imageSize: menuItem.imageSize })
    Accessible.name: menuItem.entry.replace(/^\d+\t/, "")

    Process {
        id: decoder
        running: menuItem.entryId > 0
        // Write to a temporary name and rename, so the Image never reads a partial file.
        command: ["sh", "-c", 'umask 077; mkdir -p "$1" && { [ -s "$2" ] || { "$4" decode "$3" > "$2.part" && mv -f "$2.part" "$2"; }; }',
                  "sh", menuItem.decodeDir, menuItem.decodePath, String(menuItem.entryId), menuItem.backendBinary]
        onExited: exitCode => menuItem.decoration = exitCode === 0 ? "file://" + menuItem.decodePath : ""
    }
    Component.onDestruction: if (menuItem.entryId > 0)
        Quickshell.execDetached(["rm", "-f", menuItem.decodePath, menuItem.decodePath + ".part"])

    mainItem: Item {
        implicitHeight: childrenRect.height

        Image {
            id: previewImage

            width: Math.min(Math.round(height * menuItem.imageSize.width / menuItem.imageSize.height), parent.width)
            height: sourceSize.height

            // align left
            // right in RTL
            anchors.left: parent.left

            cache: false
            source: menuItem.decoration
            sourceSize.height: Math.min(menuItem.imageSize.height, Kirigami.Units.gridUnit * 4 + Kirigami.Units.smallSpacing * 2)
            smooth: true
            fillMode: Image.PreserveAspectFit
        }
    }
}
