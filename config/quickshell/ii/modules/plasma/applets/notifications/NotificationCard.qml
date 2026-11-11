// BWM: upstream Summary/Body/ActionContainer with an adapter for BWM's existing notification server.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami
Item {
    id:card
    required property var notification
    required property var backend
    property bool readOnly:false
    implicitHeight:content.implicitHeight+16
    ModelInterface {
        id:adapter
        applicationName:card.notification.appName??""
        applicationIconSource:card.notification.appIcon??""
        summary:card.notification.summary??""
        body:card.notification.body??""
        actionNames:(card.notification.actions??[]).map(a=>a.identifier)
        actionLabels:(card.notification.actions??[]).map(a=>a.text)
        hasSomeActions:actionNames.length>0
        onActionInvoked:actionName=> { if(!card.readOnly)card.backend.attemptInvokeAction(card.notification.notificationId,actionName); }
    }
    ColumnLayout {
        id:content; anchors { left:parent.left;right:parent.right; margins:8 }
        spacing:4
        RowLayout {
            Kirigami.Icon { source:adapter.applicationIconSource||"notifications"; implicitWidth:22;implicitHeight:22 }
            PC3.Label { Layout.fillWidth:true; text:adapter.applicationName; font:Kirigami.Theme.smallFont; textFormat:Text.PlainText }
            PC3.ToolButton { icon.name:"window-close"; enabled:!card.readOnly; onClicked:card.backend.discardNotification(card.notification.notificationId) }
        }
        Summary { modelInterface:adapter }
        Body { modelInterface:adapter; visible:adapter.body.length>0 }
        Image { source:card.notification.image??""; visible:source.toString().length>0; Layout.fillWidth:true; Layout.preferredHeight:visible?100:0; fillMode:Image.PreserveAspectFit }
        ActionContainer { Layout.fillWidth:true; modelInterface:adapter; visible:adapter.hasSomeActions; enabled:!card.readOnly }
    }
}
