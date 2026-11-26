// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
Kirigami.FormLayout {
    property string cfg_Video
    property string cfg_Poster
    Controls.TextField {
        Kirigami.FormData.label: qsTr("Video file (file:///…):")
        text: cfg_Video
        onTextEdited: cfg_Video = text
    }
    Controls.TextField {
        Kirigami.FormData.label: qsTr("Still image (file:///…):")
        text: cfg_Poster
        onTextEdited: cfg_Poster = text
    }
}
