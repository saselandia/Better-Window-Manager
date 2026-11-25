// BWM: Plasma battery/brightness/power presentation backed by common UPower, Idle and brightness services.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Services.UPower
import qs.services
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import "power"
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.battery"
    property var battery:Battery
    property var monitors:Brightness.monitors
    property var idle:Idle
    property var powerProfiles:PowerProfiles
    // null = auto-detect on the system D-Bus; tests may set true/false explicitly.
    property var powerProfilesAvailable:null
    property bool detectedPowerProfilesAvailable:false
    readonly property bool hasPowerProfiles:powerProfilesAvailable!==null?Boolean(powerProfilesAvailable):detectedPowerProfilesAvailable

    Process {
        id:ppdProbe
        running:root.powerProfilesAvailable===null
        command:["sh","-c","busctl --system status org.freedesktop.UPower.PowerProfiles >/dev/null 2>&1 || busctl --system status net.hadess.PowerProfiles >/dev/null 2>&1"]
        onExited:exitCode=>root.detectedPowerProfilesAvailable=(exitCode===0)
    }

    fullRepresentation: PlasmaExtras.Representation {
        header: PlasmaExtras.PlasmoidHeading {
            visible:!!root.idle
            RowLayout {
                anchors.fill:parent
                PC3.Switch {
                    id:inhibitSwitch
                    objectName:"plasma-power-inhibit"
                    Layout.fillWidth:true
                    text:root.i18n("Manually block sleep and screen locking")
                    checked:Boolean(root.idle?.inhibit)
                    enabled:!root.readOnly&&!!root.idle
                    onToggled:if(root.idle&&typeof root.idle.toggleInhibit==="function")root.idle.toggleInhibit(checked)
                }
            }
        }
        PC3.ScrollView {
            anchors.fill:parent
            ColumnLayout {
                width:parent.width
                spacing:Kirigami.Units.smallSpacing
                InhibitionHint {
                    objectName:"plasma-power-inhibit-hint"
                    Layout.fillWidth:true
                    Layout.margins:Kirigami.Units.smallSpacing
                    visible:Boolean(root.idle?.inhibit)
                    iconSource:"preferences-desktop-screensaver"
                    text:root.i18n("You have manually blocked sleep and screen locking.")
                }
                BatteryItem {
                    Layout.fillWidth:true;visible:root.battery.available
                    batteryPrettyName:root.i18n("Battery");batteryType:"Battery"
                    batteryPercent:Math.round(root.battery.percentage*100)
                    batteryCapacity:Math.round(root.battery.health)
                    batteryPluggedIn:root.battery.available;batteryIsPowerSupply:true
                    pluggedIn:root.battery.isPluggedIn;batteryChargeState:root.battery.chargeState
                    remainingTime:(root.battery.isCharging?root.battery.timeToFull:root.battery.timeToEmpty)*1000
                }
                PowerProfileItem {
                    Layout.fillWidth:true
                    Layout.margins:Kirigami.Units.smallSpacing
                    visible:root.hasPowerProfiles
                    backend:root.powerProfiles
                    translator:root
                    readOnly:root.readOnly
                }
                Repeater {
                    model:root.monitors.filter(m=>m.ready&&Number.isFinite(m.brightness))
                    BrightnessItem {
                        required property var modelData
                        Layout.fillWidth:true
                        type:BrightnessItem.Screen;text:modelData.screen.name;icon.name:"video-display"
                        minimumValue:1;maximumValue:100;stepSize:1;value:Math.round(modelData.brightness*100)
                        enabled:!root.readOnly;onMoved:modelData.setBrightness(slider.value/100)
                    }
                }

                PlasmaExtras.PlaceholderMessage {
                    visible:!root.idle&&!root.battery.available&&!root.hasPowerProfiles&&root.monitors.filter(m=>m.ready).length===0
                    text:root.i18n("No battery or brightness controls available")
                }
            }
        }
    }
}
