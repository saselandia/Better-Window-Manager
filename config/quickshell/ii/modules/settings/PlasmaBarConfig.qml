import QtQuick
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.widgets

// "Barra de tareas" page of the KDE Plasma settings app (Plasma panel only)
ContentPage {
    id: page
    forceWidth: true

    readonly property var plasma: Config.options.bar.plasma
    // Legacy "floating" style is read as translucent + floating
    readonly property string currentStyle: plasma.style === "opaque" ? "opaque" : "translucent"
    readonly property bool currentFloating: plasma.floating || plasma.style === "floating"

    // Breeze / Plasma colour presets for the panel background
    readonly property var colorPresets: [
        { name: "Breeze oscuro", color: "#24292e" },
        { name: "Breeze ventana", color: "#202326" },
        { name: "Grafito", color: "#31363b" },
        { name: "Negro", color: "#000000" },
        { name: "Azul noche", color: "#1a2633" },
        { name: "Azul Breeze", color: "#1d4f6e" },
        { name: "Violeta", color: "#2e2440" },
        { name: "Verde bosque", color: "#1c2e26" },
        { name: "Burdeos", color: "#3a1f24" }
    ]

    ContentSection {
        icon: "toast"
        title: "Panel"

        ContentSubsection {
            title: "Estilo"
            tooltip: "Traslúcido: deja ver el fondo de pantalla.\nOpaco: color sólido."

            ConfigSelectionArray {
                currentValue: page.currentStyle
                onSelected: newValue => {
                    if (page.plasma.style === "floating")
                        page.plasma.floating = true;
                    page.plasma.style = newValue;
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
                    }
                ]
            }
        }

        ConfigSlider {
            visible: page.currentStyle === "translucent"
            buttonIcon: "opacity"
            text: "Opacidad"
            from: 0.3
            to: 1
            value: page.plasma.opacity
            onValueChanged: {
                page.plasma.opacity = value;
            }
        }

        ConfigSwitch {
            buttonIcon: "branding_watermark"
            text: "Flotante"
            checked: page.currentFloating
            onCheckedChanged: {
                if (page.plasma.style === "floating")
                    page.plasma.style = "translucent";
                page.plasma.floating = checked;
            }
            StyledToolTip {
                text: "Separa el panel de los bordes de la pantalla con esquinas redondeadas.\nComo en Plasma, deja de flotar mientras haya una ventana maximizada en esa pantalla."
            }
        }

        ConfigSpinBox {
            visible: page.currentFloating
            icon: "padding"
            text: "Separación del panel flotante (píxeles)"
            value: page.plasma.floatingGap
            from: 2
            to: 32
            stepSize: 1
            onValueChanged: {
                page.plasma.floatingGap = value;
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
        icon: "palette"
        title: "Color del panel"

        Flow {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: page.colorPresets
                delegate: MouseArea {
                    id: swatch
                    required property var modelData
                    readonly property bool selected: page.plasma.color.toLowerCase() === modelData.color
                    width: 40
                    height: 40
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: page.plasma.color = modelData.color

                    Rectangle {
                        anchors.fill: parent
                        radius: Appearance.rounding.small
                        color: swatch.modelData.color
                        border.width: swatch.selected ? 2 : 1
                        border.color: swatch.selected ? Appearance.colors.colPrimary
                            : (swatch.containsMouse ? Appearance.colors.colOnLayer1 : Appearance.colors.colOutlineVariant)
                    }
                    MaterialSymbol {
                        visible: swatch.selected
                        anchors.centerIn: parent
                        text: "check"
                        iconSize: 20
                        color: "#fcfcfc"
                    }
                    StyledToolTip {
                        // MouseArea has no `hovered`: show only while the pointer is over it
                        extraVisibleCondition: swatch.containsMouse
                        text: `${swatch.modelData.name} (${swatch.modelData.color})`
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                radius: Appearance.rounding.small
                color: page.plasma.color
                border.width: 1
                border.color: Appearance.colors.colOutlineVariant
            }
            MaterialTextField {
                id: hexField
                Layout.fillWidth: true
                placeholderText: "Color personalizado (#rrggbb)"
                text: page.plasma.color
                onEditingFinished: {
                    const value = text.trim();
                    if (/^#?[0-9a-fA-F]{6}$/.test(value))
                        page.plasma.color = value.startsWith("#") ? value : "#" + value;
                    else
                        text = page.plasma.color;
                }
            }
            RippleButtonWithIcon {
                materialIcon: "restart_alt"
                mainText: "Restablecer"
                onClicked: page.plasma.color = "#24292e"
            }
        }
    }

    ContentSection {
        icon: "apps"
        title: "Gestor de tareas"

        ConfigSwitch {
            buttonIcon: "format_align_center"
            text: "Iconos centrados"
            checked: page.plasma.centerTasks
            onCheckedChanged: {
                page.plasma.centerTasks = checked;
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
            StyledToolTip {
                text: "La campana de la bandeja muestra cuántas notificaciones sin leer hay.\nDesactivado: sólo un punto azul. Clic: ver notificaciones. Clic central: No molestar."
            }
        }
    }
}
