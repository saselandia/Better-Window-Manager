import QtQuick
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// "Barra de tareas" page of the KDE Plasma settings app (Plasma panel only)
ContentPage {
    forceWidth: true

    ContentSection {
        icon: "toast"
        title: "Panel"

        ContentSubsection {
            title: "Estilo"
            tooltip: "Traslúcido: como ahora, deja ver el fondo.\nOpaco: color sólido.\nFlotante: separado de los bordes de la pantalla y con esquinas redondeadas."

            ConfigSelectionArray {
                currentValue: Config.options.bar.plasma.style
                onSelected: newValue => {
                    Config.options.bar.plasma.style = newValue;
                }
                options: [
                    {
                        displayName: "Traslúcido",
                        icon: "blur_on",
                        value: "translucent"
                    },
                    {
                        displayName: "Opaco",
                        icon: "rectangle",
                        value: "opaque"
                    },
                    {
                        displayName: "Flotante",
                        icon: "branding_watermark",
                        value: "floating"
                    }
                ]
            }
        }

        ConfigSpinBox {
            visible: Config.options.bar.plasma.style === "floating"
            icon: "padding"
            text: "Separación del panel flotante (píxeles)"
            value: Config.options.bar.plasma.floatingGap
            from: 2
            to: 32
            stepSize: 1
            onValueChanged: {
                Config.options.bar.plasma.floatingGap = value;
            }
        }

        ConfigSpinBox {
            icon: "straighten"
            text: "Altura del panel (píxeles)"
            value: (Config.options?.bar?.height > 0) ? Config.options.bar.height : 44
            from: 32
            to: 96
            stepSize: 1
            onValueChanged: {
                Config.options.bar.height = value;
            }
        }
    }

    ContentSection {
        icon: "apps"
        title: "Gestor de tareas"

        ConfigSwitch {
            buttonIcon: "format_align_center"
            text: "Iconos centrados"
            checked: Config.options.bar.plasma.centerTasks
            onCheckedChanged: {
                Config.options.bar.plasma.centerTasks = checked;
            }
            StyledToolTip {
                text: "Coloca los iconos de las aplicaciones en el centro del panel en lugar de junto al lanzador"
            }
        }
    }

    ContentSection {
        icon: "notifications"
        title: "Notificaciones"
        ConfigSwitch {
            buttonIcon: "counter_2"
            text: "Indicador de no leídas: mostrar número"
            checked: Config.options.bar.indicators.notifications.showUnreadCount
            onCheckedChanged: {
                Config.options.bar.indicators.notifications.showUnreadCount = checked;
            }
        }
    }
}
