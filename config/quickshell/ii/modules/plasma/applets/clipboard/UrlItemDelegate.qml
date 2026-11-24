/*
    SPDX-FileCopyrightText: 2014 Martin Gräßlin <mgraesslin@kde.org>
    SPDX-FileCopyrightText: 2014 Sebastian Kügler <sebas@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

// BWM: UrlItemDelegate.qml of plasma-workspace 6.7.5 (klipper). Klipper keeps the URL list in its
// history and its preview image provider asks KIO::PreviewJob for a thumbnail or the MIME icon.
// Here the cliphist entry is decoded once (the list text is truncated) and `gio info` gives the
// same freedesktop thumbnail cache entry or the MIME icon of each local file; remote URLs get no
// preview, like the provider. Drag stays disabled as in the BWM base delegate.
pragma ComponentBehavior: Bound

import QtQuick

import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import Quickshell.Io

ClipboardItemDelegate {
    id: menuItem
    objectName: "plasma-clipboard-urls"
    type: 8 // HistoryItemType::Url: only "Remove from history"

    required property string entry
    property string backendBinary: "cliphist"
    readonly property int entryId: Number((/^(\d+)\t/.exec(menuItem.entry) ?? [0, 0])[1])
    property var urls: []
    property var previews: ({})   // url -> {icon, thumbnail}
    model: ({ display: menuItem.urls.join(" ") })

    Process {
        running: menuItem.entryId > 0 && menuItem.maximumNumberOfPreviews > 0
        command: ["sh", "-c", "u=$(\"$1\" decode \"$2\" | tr ' \\t\\r' '\\n\\n\\n' | grep -v '^$'); printf '%s\\n' \"$u\" | sed 's/^/url\\t/'; printf '%s\\n' \"$u\" | grep '^file://' | head -n \"$3\" | while IFS= read -r f; do i=$(gio info -a standard::icon,thumbnail::path \"$f\" 2>/dev/null); printf 'preview\\t%s\\t%s\\t%s\\n' \"$f\" \"$(printf '%s\\n' \"$i\" | sed -n 's/^ *standard::icon: //p' | cut -d, -f1)\" \"$(printf '%s\\n' \"$i\" | sed -n 's/^ *thumbnail::path: //p')\"; done",
                  "sh", menuItem.backendBinary, String(menuItem.entryId), String(menuItem.maximumNumberOfPreviews)]
        stdout: StdioCollector {
            onStreamFinished: {
                const urls = [], previews = {};
                for (const line of text.split("\n")) {
                    const f = line.split("\t");
                    if (f[0] === "url" && f[1]) urls.push(f[1]);
                    else if (f[0] === "preview" && f[1]) previews[f[1]] = { icon: f[2] || "unknown", thumbnail: f[3] || "" };
                }
                menuItem.previews = previews;
                menuItem.urls = urls;
            }
        }
    }
    property int maximumNumberOfPreviews: Math.floor(width / (Kirigami.Units.gridUnit * 4 + Kirigami.Units.smallSpacing))
    Accessible.name: menuItem.model?.display ?? ""
    mainItem: Item {
        id: previewItem
        implicitHeight: Kirigami.Units.gridUnit * 4 + Kirigami.Units.smallSpacing * 2

        Drag.active: menuItem.dragHandler.active
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.CopyAction
        Drag.mimeData: {
            "text/uri-list": menuItem.model?.display?.split(" ") ?? [],
        }

        ListView {
            id: previewList
            model: menuItem.model?.display?.split(" ", menuItem.maximumNumberOfPreviews) ?? 0
            property int itemWidth: Kirigami.Units.gridUnit * 4
            property int itemHeight: Kirigami.Units.gridUnit * 4
            interactive: false

            spacing: Kirigami.Units.smallSpacing
            orientation: Qt.Horizontal
            width: (itemWidth + spacing) * model.length
            anchors {
                top: parent.top
                left: parent.left
                bottom: parent.bottom
            }

            delegate: Item {
                id: previewItemDelegate
                width: previewList.itemWidth
                height: previewList.itemHeight
                y: Math.round((previewList.height - previewList.itemHeight) / 2)
                required property string modelData
                clip: true

                readonly property var preview: menuItem.previews[previewItemDelegate.modelData] ?? null
                Image {
                    id: previewPixmap
                    anchors.centerIn: parent
                    asynchronous: true
                    visible: status === Image.Ready
                    sourceSize: Qt.size(previewList.itemWidth * 2, previewList.itemHeight * 2)
                    source: previewItemDelegate.preview?.thumbnail ? "file://" + previewItemDelegate.preview.thumbnail : ""
                }
                Kirigami.Icon {
                    anchors.centerIn: parent
                    width: previewList.itemWidth; height: previewList.itemHeight
                    visible: !previewPixmap.visible
                    source: previewItemDelegate.preview?.icon ?? "unknown"
                }
                Rectangle {
                    id: overlay
                    color: Kirigami.Theme.textColor
                    opacity: 0.6
                    height: Kirigami.Units.gridUnit
                    anchors {
                        left: parent.left
                        right: parent.right
                        bottom: parent.bottom
                    }
                }
                PlasmaComponents3.Label {
                    font: Kirigami.Theme.smallFont
                    color: Kirigami.Theme.backgroundColor
                    maximumLineCount: 1
                    anchors {
                        verticalCenter: overlay.verticalCenter
                        left: overlay.left
                        right: overlay.right
                        leftMargin: Kirigami.Units.smallSpacing
                        rightMargin: Kirigami.Units.smallSpacing
                    }
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignHCenter
                    text: {
                        let u = previewItemDelegate.modelData.split("/");
                        return decodeURIComponent(u[u.length - 1]);
                    }
                    textFormat: Text.PlainText
                    Accessible.ignored: true
                }
            }
        }
        PlasmaComponents3.Label {
            property int additionalItems: (menuItem.model?.display.split(" ").length ?? 0) - menuItem.maximumNumberOfPreviews
            visible: additionalItems > 0
            opacity: 0.75
            text: i18ndc("klipper", "Indicator that there are more urls in the clipboard than previews shown", "+%1", additionalItems)
            textFormat: Text.PlainText
            anchors {
                left: previewList.right
                right: parent.right
                bottom: parent.bottom
                margins: Kirigami.Units.smallSpacing

            }
            verticalAlignment: Text.AlignBottom
            horizontalAlignment: Text.AlignHCenter
            font: Kirigami.Theme.smallFont
        }
    }
}
