/*
    SPDX-FileCopyrightText: 2020 Aleix Pol Gonzalez <aleixpol@kde.org>
    SPDX-License-Identifier: LGPL-2.0-or-later

    BWM: Plasma 6.7.5 PipeWireThumbnail.qml, retaining the original tooltip's
    interface. Replace only the KWin/PipeWire capture endpoint with a native
    Hyprland toplevel capture item. Tooltip layout and interaction stay upstream.
*/
import QtQuick
import org.bwm.nativetasks 1.0 as Native

Native.WindowThumbnail {
    id: thumbnail
    readonly property alias hasThumbnail: thumbnail.ready
    anchors.fill: parent
    uuid: thumbnailSourceItem.winId ?? ""
}
