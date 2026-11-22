// BWM: Klipper history/search presentation with cliphist as the common BWM backend.
import QtQuick
import QtQuick.Layouts
import qs.services
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import "clipboard"
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.clipboard"
    property var backend:Cliphist
    onExpandedChanged:if(expanded&&!readOnly)backend.refresh()
    fullRepresentation: PlasmaExtras.Representation {
        header:PlasmaExtras.PlasmoidHeading {
            RowLayout {
                anchors.fill:parent
                PC3.TextField {
                    id:search; Layout.fillWidth:true; placeholderText:root.i18n("Search…")
                    Keys.onReturnPressed:if(!root.readOnly&&history.model.length>0)root.backend.copy(history.model[0])
                    Keys.onEnterPressed:if(!root.readOnly&&history.model.length>0)root.backend.copy(history.model[0])
                    Connections {
                        target:root
                        function onExpandedChanged() { if(root.expanded&&!root.readOnly){search.text="";search.forceActiveFocus();} }
                    }
                }
                PC3.ToolButton {
                    icon.name:"edit-clear-history"; text:root.i18n("Clear History")
                    display:PC3.AbstractButton.IconOnly
                    PC3.ToolTip.visible:hovered; PC3.ToolTip.text:text
                    enabled:!root.readOnly&&(root.backend.entries?.length??0)>0
                    onClicked:if(typeof root.backend.wipe==="function")root.backend.wipe();else if(typeof root.backend.clear==="function")root.backend.clear()
                }
            }
        }
        PC3.ScrollView {
            anchors.fill:parent
            ListView {
                id:history;clip:true
                model:(root.backend.entries??[]).filter(e=>e.toLowerCase().includes(search.text.toLowerCase()))
                delegate:TextItemDelegate {
                    required property string modelData
                    width:history.width
                    model:({display:modelData.replace(/^\d+\s+/,"")})
                    enabled:!root.readOnly
                    onSelected:root.backend.copy(modelData)
                    onRemove:root.backend.deleteEntry(modelData)
                }
                PlasmaExtras.PlaceholderMessage { anchors.centerIn:parent;visible:history.count===0;text:root.i18n("Clipboard is empty") }
            }
        }
    }
}
