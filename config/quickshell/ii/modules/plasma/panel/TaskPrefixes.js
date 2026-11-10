/*
    SPDX-FileCopyrightText: 2012-2016 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2020 Nate Graham <nate@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

// BWM: location is the panel edge string; KWin tasks/model helpers are replaced by TasksModel.qml.
function taskPrefix(prefix, location) {
    let effectivePrefix;

    switch (location) {
    case "left":
        effectivePrefix = "west-" + prefix;
        break;
    case "top":
        effectivePrefix = "north-" + prefix;
        break;
    case "right":
        effectivePrefix = "east-" + prefix;
        break;
    default:
        effectivePrefix = "south-" + prefix;
    }
    return [effectivePrefix, prefix];
}

function taskPrefixHovered(prefix, location) {
    return [
        ...taskPrefix((prefix || "launcher") + "-hover", location),
        ...prefix ? taskPrefix("hover", location) : [],
        ...taskPrefix(prefix, location),
    ];
}
