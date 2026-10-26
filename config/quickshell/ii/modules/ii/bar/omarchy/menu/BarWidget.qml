import QtQuick
import qs.Commons
import qs.Ui

// Omarchy's omarchy.menu launcher (shell/plugins/menu/BarWidget.qml, MIT). BWM shows the distro
// logo the user picked (settings.icon, a Nerd Font glyph) instead of Omarchy's own font glyph, and
// opens Retro's menu through BWM's IPC; right click opens the default terminal.
BarWidget {
  id: root
  moduleName: "omarchy.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.settings && root.settings.icon ? root.settings.icon : ""
    fontFamily: root.settings && root.settings.fontFamily ? root.settings.fontFamily : (root.bar ? root.bar.fontFamily : Style.font.family)
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("$HOME/.config/hypr/scripts/bwm-terminal")
      else root.bar.run("qs -c ii ipc call omarchyMenu toggle")
    }
  }
}
