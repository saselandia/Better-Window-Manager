import QtQuick
import Quickshell
import Quickshell.Services.Mpris
import qs.Commons
import qs.Ui

// BWM addition to omarchy-mpris (not upstream): the "now playing" dropdown that opens on a left
// click, in the same Omarchy card style as the clock's calendar: big album art, title, artist and
// album, a seekable progress bar, shuffle / previous / play-pause / next / repeat, the open-player
// button and a chip per player when there are several.
PopupCard {
  id: root

  required property var widget        // the BarWidget (service, colours, bar)
  readonly property var service: widget.mediaService
  readonly property var player: service ? service.activePlayer : null
  readonly property color fg: widget.bar ? widget.bar.foreground : Color.foreground
  readonly property color dim: Qt.rgba(fg.r, fg.g, fg.b, 0.55)
  readonly property string fontFamily: widget.bar ? widget.bar.fontFamily : Style.font.family
  readonly property real length: player && player.lengthSupported ? player.length : 0
  property real position: 0

  anchorItem: widget
  bar: widget.bar
  owner: widget
  contentWidth: fittedContentWidth(Style.space(340))
  contentHeight: fittedContentHeight(column.implicitHeight)

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0
    var s = Math.floor(seconds % 60)
    var m = Math.floor(seconds / 60) % 60
    var h = Math.floor(seconds / 3600)
    var mm = h > 0 && m < 10 ? "0" + m : String(m)
    return (h > 0 ? h + ":" : "") + mm + ":" + (s < 10 ? "0" + s : s)
  }

  // MprisPlayer.position is not pushed by players: poll it while the card is open
  property Timer poller: Timer {
    interval: 500
    repeat: true
    running: root.open && !!root.player
    triggeredOnStart: true
    onTriggered: root.position = root.player ? root.player.position : 0
  }

  component Glyph: Text {
    id: glyph
    property bool active: false
    property bool enabledState: true
    signal activated()
    color: !enabledState ? Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.25)
      : (glyphMouse.containsMouse || active ? Color.accent : root.fg)
    font.family: Style.font.family
    font.pixelSize: Style.font.title
    MouseArea {
      id: glyphMouse
      anchors.fill: parent
      anchors.margins: -Style.space(4)
      hoverEnabled: true
      enabled: glyph.enabledState
      cursorShape: Qt.PointingHandCursor
      onClicked: glyph.activated()
    }
  }

  Column {
    id: column
    anchors.fill: parent
    spacing: Style.space(10)

    Text {
      text: "NOW PLAYING"
      color: root.fg
      font.family: root.fontFamily
      font.pixelSize: Style.font.subtitle
      font.bold: true
    }

    // Album art, square, framed like the rest of the card
    Rectangle {
      width: parent.width
      height: width
      color: Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.06)
      border.width: 1
      border.color: Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.25)

      Image {
        id: art
        anchors.fill: parent
        anchors.margins: 1
        source: root.service ? root.service.artUrl : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        sourceSize.width: 600
        sourceSize.height: 600
      }
      Text {
        anchors.centerIn: parent
        visible: art.status !== Image.Ready
        text: "󰝚"
        color: root.dim
        font.family: Style.font.family
        font.pixelSize: Style.space(64)
      }
    }

    Column {
      width: parent.width
      spacing: Style.space(2)
      Text {
        width: parent.width
        text: root.service && root.service.title !== "" ? root.service.title : "No track"
        color: root.fg
        font.family: root.fontFamily
        font.pixelSize: Style.font.subtitle
        font.bold: true
        elide: Text.ElideRight
      }
      Text {
        width: parent.width
        visible: text !== ""
        text: root.service ? root.service.artist : ""
        color: root.fg
        font.family: root.fontFamily
        font.pixelSize: Style.font.body
        elide: Text.ElideRight
      }
      Text {
        width: parent.width
        visible: text !== ""
        text: root.service ? root.service.album : ""
        color: root.dim
        font.family: root.fontFamily
        font.pixelSize: Style.font.caption
        elide: Text.ElideRight
      }
    }

    // Progress: click or drag to seek when the player allows it
    Column {
      width: parent.width
      spacing: Style.space(4)
      visible: root.length > 0

      Item {
        width: parent.width
        height: Style.space(14)
        Rectangle {
          anchors.verticalCenter: parent.verticalCenter
          width: parent.width
          height: Style.space(4)
          color: Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.18)
          Rectangle {
            width: root.length > 0 ? parent.width * Math.min(1, root.position / root.length) : 0
            height: parent.height
            color: Color.accent
          }
        }
        MouseArea {
          anchors.fill: parent
          enabled: !!(root.player && root.player.canSeek)
          cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
          function seekTo(x) {
            var target = Math.max(0, Math.min(1, x / width)) * root.length
            root.player.position = target
            root.position = target
          }
          onPressed: mouse => seekTo(mouse.x)
          onPositionChanged: mouse => { if (pressed) seekTo(mouse.x) }
        }
      }
      Item {
        width: parent.width
        height: elapsed.implicitHeight
        Text {
          id: elapsed
          text: root.formatTime(root.position)
          color: root.dim
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
        }
        Text {
          anchors.right: parent.right
          text: root.formatTime(root.length)
          color: root.dim
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
        }
      }
    }

    // Transport
    Row {
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: Style.space(22)
      Glyph {
        text: "󰒝"
        visible: !!(root.player && root.player.shuffleSupported)
        active: !!(root.player && root.player.shuffle)
        onActivated: root.player.shuffle = !root.player.shuffle
      }
      Glyph {
        text: "󰒮"
        enabledState: !!(root.player && root.player.canGoPrevious)
        onActivated: root.widget.previous()
      }
      Glyph {
        text: root.player && root.player.isPlaying ? "󰏤" : "󰐊"
        enabledState: !!(root.player && (root.player.canPause || root.player.canPlay))
        onActivated: root.widget.playPause()
      }
      Glyph {
        text: "󰒭"
        enabledState: !!(root.player && root.player.canGoNext)
        onActivated: root.widget.next()
      }
      Glyph {
        text: root.player && root.player.loopState === MprisLoopState.Track ? "󰑘" : "󰑖"
        visible: !!(root.player && root.player.loopSupported)
        active: !!(root.player && root.player.loopState !== MprisLoopState.None)
        onActivated: {
          var s = root.player.loopState
          root.player.loopState = s === MprisLoopState.None ? MprisLoopState.Playlist
            : (s === MprisLoopState.Playlist ? MprisLoopState.Track : MprisLoopState.None)
        }
      }
    }

    // Players (when there is more than one) and "open player"
    Flow {
      width: parent.width
      spacing: Style.space(6)

      Repeater {
        // One chip per app: some players (Spotify) publish more than one MPRIS name
        readonly property var uniquePlayers: {
          var seen = {}, out = []
          var list = root.service ? root.service.sourcePlayers : []
          for (var i = 0; i < list.length; i++) {
            var p = list[i], key = String(p.identity || p.dbusName || i)
            if (seen[key] !== undefined) {
              if (p === root.player) out[seen[key]] = p   // keep the one that is playing
              continue
            }
            seen[key] = out.length
            out.push(p)
          }
          return out
        }
        model: uniquePlayers.length > 1 ? uniquePlayers : []
        delegate: Rectangle {
          id: chip
          required property var modelData
          readonly property bool current: modelData === root.player
          width: chipText.implicitWidth + Style.space(14)
          height: chipText.implicitHeight + Style.space(8)
          color: current ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.18) : "transparent"
          border.width: 1
          border.color: current || chipMouse.containsMouse ? Color.accent : Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.35)
          Text {
            id: chipText
            anchors.centerIn: parent
            text: String(chip.modelData.identity || chip.modelData.dbusName || "player")
            color: chip.current ? Color.accent : root.fg
            font.family: root.fontFamily
            font.pixelSize: Style.font.caption
          }
          MouseArea {
            id: chipMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: if (typeof root.service.remember === "function") root.service.remember(chip.modelData)
          }
        }
      }

      Rectangle {
        width: openText.implicitWidth + Style.space(14)
        height: openText.implicitHeight + Style.space(8)
        visible: !!(root.player && root.player.canRaise)
        color: "transparent"
        border.width: 1
        border.color: openMouse.containsMouse ? Color.accent : Qt.rgba(root.fg.r, root.fg.g, root.fg.b, 0.35)
        Text {
          id: openText
          anchors.centerIn: parent
          text: "open player"
          color: openMouse.containsMouse ? Color.accent : root.fg
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
        }
        MouseArea {
          id: openMouse
          anchors.fill: parent
          hoverEnabled: true
          cursorShape: Qt.PointingHandCursor
          onClicked: { root.widget.raisePlayer(); root.widget.closeNowPlaying() }
        }
      }
    }
  }
}
