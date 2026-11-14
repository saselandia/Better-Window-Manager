// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import org.kde.plasma.plasmoid
PlasmoidItem {
    fullRepresentation: Text { text: Plasmoid.configuration.derived }
}
