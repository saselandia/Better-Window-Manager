// BWM: D-Bus menus rendered by PC3, including nested menus; no native QMenu from layer-shell.
import QtQuick
import QtQml.Models
import Quickshell
import org.kde.plasma.components as PC3
PC3.Menu {
    id:menu
    property bool pendingOpen:false
    function openFor(value,button) { parent=button;pendingOpen=true;handle=value;tryOpen(); }
    function tryOpen() { if(pendingOpen&&entries.length>0) { pendingOpen=false;Qt.callLater(()=>popup()); } }
    onEntriesChanged:tryOpen()
    property var handle:null
    property var entries:opener.children.values
    QsMenuOpener { id:opener; menu:menu.handle }
    Instantiator {
        model:menu.entries
        delegate:Loader {
            required property var modelData
            required property int index
            source:modelData.hasChildren?Qt.resolvedUrl("TrayMenu.qml"):""
            sourceComponent:modelData.hasChildren?null:modelData.isSeparator?separator:entry
            onLoaded: {
                if(modelData.hasChildren) { item.title=modelData.text;item.handle=modelData;menu.insertMenu(index,item); }
                else menu.insertItem(index,item);
            }
            Component { id:separator; PC3.MenuSeparator {} }
            Component { id:entry; PC3.MenuItem { text:modelData.text; enabled:modelData.enabled; checkable:modelData.buttonType!==0; checked:modelData.checkState!==Qt.Unchecked; icon.source:modelData.icon;onTriggered:modelData.triggered() } }

        }
        onObjectRemoved:(index,object)=>{if(object.item){if(object.modelData.hasChildren)menu.removeMenu(object.item);else menu.removeItem(object.item);}}
    }
}
