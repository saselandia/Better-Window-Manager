// BWM: Klipper history/search presentation with cliphist as the common BWM backend.
import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import "clipboard"
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.clipboard"
    property var backend:Cliphist
    onExpandedChanged:if(expanded&&!readOnly)backend.refresh()
    // BWM: like KlipperPopup, a StackView with the history, the QR code page and the edit page;
    // the heading follows the current page (BarcodePage brings its own, EditPage none).
    fullRepresentation: PlasmaExtras.Representation {
        id:dialog
        header:stack.depth>1?stack.currentItem?.header??null:searchHeading
        property PlasmaExtras.PlasmoidHeading searchHeading:PlasmaExtras.PlasmoidHeading {
            visible:stack.depth===1
            RowLayout {
                anchors.fill:parent
                PC3.TextField {
                    id:search; Layout.fillWidth:true; placeholderText:root.i18n("Search…")
                    Keys.onReturnPressed:if(!root.readOnly&&history.model.length>0)root.backend.copy(history.model[0])
                    Keys.onEnterPressed:if(!root.readOnly&&history.model.length>0)root.backend.copy(history.model[0])
                    Connections {
                        target:root
                        function onExpandedChanged() { if(root.expanded&&!root.readOnly){search.text="";search.forceActiveFocus();while(stack.depth>1)stack.pop(null);} }
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
        PC3.StackView {
            id:stack
            objectName:"plasma-clipboard-stack"
            anchors.fill:parent
            initialItem:PC3.ScrollView {
                ListView {
                    id:history;clip:true
                    model:(root.backend.entries??[]).filter(e=>e.toLowerCase().includes(search.text.toLowerCase()))
                    // BWM: like Klipper's DelegateChooser, images use ImageItemDelegate.
                    delegate:Loader {
                        id:row
                        required property string modelData
                        readonly property bool image:root.backend.entryIsImage?.(modelData)??false
                        readonly property string text:modelData.replace(/^\d+\s+/,"")
                        // Klipper's URL items (type 8): a list of local file URLs, e.g. copied in a
                        // file manager. cliphist truncates the list text, so the last word may be cut.
                        readonly property bool urls:!image&&/^file:\/\//.test(text)&&text.trim().split(/\s+/).every(t=>t.startsWith("file://")||"file://".startsWith(t))
                        width:history.width
                        sourceComponent:image?imageDelegate:urls?urlDelegate:textDelegate
                        Component {
                            id:textDelegate
                            TextItemDelegate {
                                model:({display:row.text})
                                enabled:!root.readOnly
                                onSelected:root.backend.copy(row.modelData)
                                onRemove:root.backend.deleteEntry(row.modelData)
                                onBarcode:stack.push(barcodeComponent,{text:row.text})
                                onEdit:stack.push(editComponent,{modelData:{display:row.text},entry:row.modelData})
                            }
                        }
                        Component {
                            id:urlDelegate
                            UrlItemDelegate {
                                entry:row.modelData
                                backendBinary:root.backend.cliphistBinary??"cliphist"
                                enabled:!root.readOnly
                                onSelected:root.backend.copy(row.modelData)
                                onRemove:root.backend.deleteEntry(row.modelData)
                            }
                        }
                        Component {
                            id:imageDelegate
                            ImageItemDelegate {
                                entry:row.modelData
                                backendBinary:root.backend.cliphistBinary??"cliphist"
                                enabled:!root.readOnly
                                onSelected:root.backend.copy(row.modelData)
                                onRemove:root.backend.deleteEntry(row.modelData)
                            }
                        }
                    }
                    PlasmaExtras.PlaceholderMessage { anchors.centerIn:parent;visible:history.count===0;text:root.i18n("Clipboard is empty") }
                }
            }
        }
        Component {
            id:barcodeComponent
            BarcodePage { expanded:root.expanded;stack:stack;barcodeType:"QRCode";showHeader:true }
        }
        Component {
            id:editComponent
            EditPage {
                property string entry:""
                dialogItem:dialog
                // Klipper replaces the item and moves it to the top: copy the new text (cliphist
                // stores it as the newest entry) and remove the old one.
                onSaved:text=> {
                    if(root.readOnly||text===modelData.display)return;
                    root.backend.deleteEntry(entry);
                    if(typeof root.backend.setText==="function")root.backend.setText(text);
                    else Quickshell.clipboardText=text;
                }
            }
        }
    }
}
