// SPDX-License-Identifier: GPL-2.0-or-later
import QtQuick
import QtMultimedia
import org.kde.plasma.plasmoid
WallpaperItem {
    id: root
    loading: false
    Rectangle { anchors.fill: parent; color: "black" }
    Image { anchors.fill: parent; source: root.configuration.Poster; fillMode: Image.PreserveAspectCrop }
    VideoOutput { id: output; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectCrop }
    MediaPlayer {
        id: player
        source: root.configuration.Video
        videoOutput: output
        audioOutput: AudioOutput { muted: true }
        loops: MediaPlayer.Infinite
        autoPlay: true
    }
}
