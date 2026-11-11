// BWM: Plasma battery/brightness presentation backed by the common UPower and brightness services.
import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import org.kde.plasma.components as PC3
import org.kde.plasma.extras as PlasmaExtras
import "power"
AppletHost {
    id:root
    translationDomain:"plasma_applet_org.kde.plasma.battery"
    property var battery:Battery
    property var monitors:Brightness.monitors
    fullRepresentation: PlasmaExtras.Representation {
        PC3.ScrollView {
            anchors.fill:parent
            ColumnLayout {
                width:parent.width
                BatteryItem {
                    Layout.fillWidth:true;visible:root.battery.available
                    batteryPrettyName:qsTr("Battery");batteryType:"Battery"
                    batteryPercent:Math.round(root.battery.percentage*100)
                    batteryCapacity:Math.round(root.battery.health)
                    batteryPluggedIn:root.battery.available;batteryIsPowerSupply:true
                    pluggedIn:root.battery.isPluggedIn;batteryChargeState:root.battery.chargeState
                    remainingTime:(root.battery.isCharging?root.battery.timeToFull:root.battery.timeToEmpty)*1000
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

                PlasmaExtras.PlaceholderMessage { visible:!root.battery.available&&root.monitors.filter(m=>m.ready).length===0; text:qsTr("No battery or brightness controls available") }
            }
        }
    }
}
