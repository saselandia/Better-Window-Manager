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
            PC3.TextField { id:search; anchors.fill:parent;placeholderText:root.i18n("Search…") }
        }
        PC3.ScrollView {
            anchors.fill:parent
            ListView {
                id:history;clip:true
                model:root.backend.entries.filter(e=>e.toLowerCase().includes(search.text.toLowerCase()))
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
