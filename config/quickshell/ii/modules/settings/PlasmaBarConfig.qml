import QtQuick
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.widgets
ContentPage {
    id:page
    forceWidth:true
    readonly property var plasma:Config.options.bar.plasma
    ContentSection {
        title:"Panel de Plasma"; icon:"toast"
        ContentSubsection {
            title:"Borde"
            ConfigSelectionArray {
                currentValue:page.plasma.edge || (Config.options.bar.bottom?"bottom":"top")
                onSelected:value=>page.plasma.edge=value
                options:[
                    {displayName:"Abajo",value:"bottom",icon:"align_vertical_bottom"},
                    {displayName:"Arriba",value:"top",icon:"align_vertical_top"},
                    {displayName:"Izquierda",value:"left",icon:"align_horizontal_left"},
                    {displayName:"Derecha",value:"right",icon:"align_horizontal_right"}
                ]
            }
        }
        ContentSubsection {
            title:"Visibilidad"
            ConfigSelectionArray {
                currentValue:page.plasma.visibility
                onSelected:value=>page.plasma.visibility=value
                options:[
                    {displayName:"Siempre",value:"always",icon:"visibility"},
                    {displayName:"Ocultar automáticamente",value:"autoHide",icon:"visibility_off"},
                    {displayName:"Esquivar ventanas",value:"dodge",icon:"flip_to_back"},
                    {displayName:"Ventanas por debajo",value:"windowsGoBelow",icon:"layers"}
                ]
            }
        }
        ContentSubsection {
            title:"Opacidad del tema"
            ConfigSelectionArray {
                currentValue:page.plasma.style==="floating"?"adaptive":page.plasma.style
                onSelected:value=>page.plasma.style=value
                options:[
                    {displayName:"Adaptable",value:"adaptive",icon:"contrast"},
                    {displayName:"Traslúcido",value:"translucent",icon:"blur_on"},
                    {displayName:"Opaco",value:"opaque",icon:"rectangle"}
                ]
            }
        }
        ConfigSwitch { text:"Flotante"; checked:page.plasma.floating; onCheckedChanged:page.plasma.floating=checked }
        ConfigSlider { text:"Grosor"; buttonIcon:"height"; from:24; to:96; stepSize:2; value:page.plasma.thickness; onMoved:page.plasma.thickness=value }
        ConfigSlider { text:"Longitud"; buttonIcon:"width"; from:.25; to:1; stepSize:.05; value:page.plasma.length; onMoved:page.plasma.length=value }
        ContentSubsection {
            title:"Alineación"
            ConfigSelectionArray {
                currentValue:page.plasma.alignment
                onSelected:value=>page.plasma.alignment=value
                options:[
                    {displayName:"Inicio",value:"start",icon:"align_horizontal_left"},
                    {displayName:"Centro",value:"center",icon:"align_horizontal_center"},
                    {displayName:"Final",value:"end",icon:"align_horizontal_right"}
                ]
            }
        }
        StyledText { Layout.fillWidth:true; wrapMode:Text.WordWrap; text:"El fondo, los márgenes y las sombras los proporciona el estilo de Plasma. Clic derecho sobre un espacio del panel activa la edición de sus widgets." }
    }
}
