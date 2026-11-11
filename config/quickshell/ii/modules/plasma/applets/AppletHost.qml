// BWM: minimal PlasmoidItem contract. No containment, service registration or kded.
import QtQuick
import org.kde.ki18n
import QtQuick.Controls as QQC2
import org.kde.plasma.core as PlasmaCore
Item {
    id:host
    property string translationDomain: ""
    KI18nContext { id:translations; translationDomain:host.translationDomain }
    function i18n(...args) { return translations.i18n(...args); }
    function i18nc(...args) { return translations.i18nc(...args); }
    function i18np(...args) { return translations.i18np(...args); }
    function i18ncp(...args) { return translations.i18ncp(...args); }
    property bool expanded: visible
    enabled:!readOnly
    property bool readOnly: false // isolated harness supplies mocks and disables actions
    property var configuration: QtObject { property bool pin: false }
    readonly property var plasmoid: host
    property int location: PlasmaCore.Types.BottomEdge
    property int formFactor: PlasmaCore.Types.Horizontal
    property int containmentDisplayHints: 0
    readonly property var containment: ({pluginName:"org.kde.plasma.systemtray"})
    property string title: ""
    property string icon: ""
    property int status: PlasmaCore.Types.PassiveStatus
    property bool busy:false
    property real switchWidth:280
    property real switchHeight:280
    property bool hideOnWindowDeactivate:true
    property string toolTipMainText:""
    property string toolTipSubText:""
    property int toolTipTextFormat:Text.PlainText
    property list<QtObject> contextualActions:[]
    property Component compactRepresentation
    property Component fullRepresentation
    readonly property Item compactRepresentationItem:null
    readonly property Item fullRepresentationItem:representation.item
    property var internalActions: ({})
    function setInternalAction(name,action) { internalActions=Object.assign({},internalActions,{[name]:action}); }
    function removeInternalAction(name) {}
    readonly property var unavailableAction: QQC2.Action { enabled:false; text:"" }
    function internalAction(name) { return internalActions[name] ?? unavailableAction; }
    signal secondaryActivated()
    signal activated()
    Loader { id:representation; anchors.fill:parent; sourceComponent:host.fullRepresentation }
}
