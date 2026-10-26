import QtQuick
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import Quickshell
import Quickshell.Io

ContentPage {
    forceWidth: true

    // Retro only: the Omarchy bar plugins (preinstalled in quickshell/ii/omarchy-plugins plus any
    // added with bwm-plugin.sh), each one can be turned off. Stored in
    // ~/.config/bwm/omarchy-plugins.json, which the Retro bar watches. Read here through
    // `bwm-plugin.sh catalog`, so this app never loads the plugins themselves.
    readonly property string pluginScript: Quickshell.env("HOME") + "/.config/hypr/scripts/bwm-plugin.sh"
    property var omarchyPlugins: []
    property var omarchyLayout: ({ bar: [] })
    function pluginEnabled(p) {
        const placed = (omarchyLayout.bar ?? []).some(e => e.id === p.id);
        return placed || (p.builtin && !(omarchyLayout.disabled ?? []).includes(p.id));
    }
    Process {
        id: pluginCatalog
        running: Appearance.isRetro
        command: [pluginScript, "catalog"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    omarchyLayout = data.layout ?? { bar: [] };
                    omarchyPlugins = (data.plugins ?? []).filter(p => p.barWidget);
                } catch (e) {}
            }
        }
    }
    Process {
        id: pluginToggle
        onExited: pluginCatalog.running = true
    }

    // Retro: Omarchy's fixed widgets on the right of the bar, each one can be hidden
    readonly property var retroRightWidgets: [
        { id: "omarchy.media", name: "Multimedia (lo que suena, de Omarchy)", icon: "music_note", hiddenByDefault: true },
        { id: "omarchy.system-update", name: "Actualizaciones (Portage, Flatpak y BWM; sólo si hay)", icon: "system_update" },
        { id: "omarchy.tray", name: "Bandeja del sistema", icon: "apps" },
        { id: "omarchy.keyboard-layout", name: "Distribución de teclado (sólo con varias)", icon: "keyboard" },
        { id: "omarchy.agents", name: "Agentes de IA (uso de Claude, Codex…)", icon: "smart_toy" },
        { id: "omarchy.tailscale", name: "Tailscale (sólo si está instalado)", icon: "vpn_lock" },
        { id: "omarchy.bluetooth", name: "Bluetooth", icon: "bluetooth" },
        { id: "omarchy.network", name: "Red", icon: "wifi" },
        { id: "omarchy.audio", name: "Audio", icon: "volume_up" },
        { id: "omarchy.monitor", name: "Pantallas", icon: "monitor" },
        { id: "omarchy.power", name: "Energía", icon: "power_settings_new" }
    ]
    function rightWidgetShown(id) {
        if ((omarchyLayout.disabled ?? []).includes(id))
            return false;
        const w = retroRightWidgets.find(x => x.id === id);
        return !(w && w.hiddenByDefault) || (omarchyLayout.shown ?? []).includes(id);
    }

    // Retro: language of Omarchy's shell (~/.config/omarchy/language, watched by Commons/I18n.qml),
    // English or Omarchy's Spanish (es-MX); vendored in Commons/omarchy/default/i18n
    FileView {
        id: omarchyLanguageFile
        path: Quickshell.env("HOME") + "/.config/omarchy/language"
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
    }
    readonly property string omarchyLanguage: (omarchyLanguageFile.text() || "en").trim() || "en"

    ContentSection {
        visible: Appearance.isRetro
        icon: "translate"
        title: Translation.tr("Omarchy panels language")

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: Translation.tr("Language of Omarchy's bar panels, menu, dock, OSD, polkit dialog and reminders.")
        }

        ConfigSelectionArray {
            currentValue: omarchyLanguage
            onSelected: newValue => {
                omarchyLanguageFile.setText(newValue + "\n");
            }
            options: [
                { displayName: "English", icon: "language", value: "en" },
                { displayName: "Español (México)", icon: "language", value: "es-MX" }
            ]
        }
    }

    ContentSection {
        visible: Appearance.isRetro
        icon: "view_week"
        title: Translation.tr("Right side of the bar")

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: Translation.tr("Omarchy's widgets on the right of the Retro bar, in their order. Turn off the ones you do not want.")
        }

        Repeater {
            model: retroRightWidgets
            delegate: ConfigSwitch {
                required property var modelData
                buttonIcon: modelData.icon
                text: modelData.name
                checked: rightWidgetShown(modelData.id)
                onClicked: {
                    pluginToggle.command = [pluginScript, rightWidgetShown(modelData.id) ? "hide" : "show", modelData.id];
                    pluginToggle.running = true;
                }
            }
        }
    }

    ContentSection {
        visible: Appearance.isRetro
        icon: "extension"
        title: Translation.tr("Omarchy plugins")

        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Appearance.colors.colSubtext
            text: Translation.tr("Widgets from Omarchy's shell in the Retro bar. More: ~/.config/hypr/scripts/bwm-plugin.sh add <git-url>")
        }

        Repeater {
            model: omarchyPlugins
            delegate: ConfigSwitch {
                required property var modelData
                buttonIcon: "widgets"
                text: modelData.name + (modelData.builtin ? "" : "  ·  " + Translation.tr("installed"))
                checked: pluginEnabled(modelData)
                onClicked: {
                    pluginToggle.command = [pluginScript, pluginEnabled(modelData) ? "disable" : "enable", modelData.id];
                    pluginToggle.running = true;
                }
                StyledToolTip {
                    text: modelData.description ?? ""
                }
            }
        }
    }

    ContentSection {
        icon: "notifications"
        title: Translation.tr("Notifications")
        ConfigSwitch {
            buttonIcon: "counter_2"
            text: Translation.tr("Unread indicator: show count")
            checked: Config.options.bar.indicators.notifications.showUnreadCount
            onCheckedChanged: {
                Config.options.bar.indicators.notifications.showUnreadCount = checked;
            }
        }
    }
    
    ContentSection {
        icon: "spoke"
        title: Translation.tr("Positioning")

        ConfigRow {
            ContentSubsection {
                title: Translation.tr("Bar position")
                Layout.fillWidth: true

                ConfigSelectionArray {
                    currentValue: (Config.options.bar.bottom ? 1 : 0) | (Config.options.bar.vertical ? 2 : 0)
                    onSelected: newValue => {
                        Config.options.bar.bottom = (newValue & 1) !== 0;
                        Config.options.bar.vertical = (newValue & 2) !== 0;
                    }
                    options: [
                        {
                            displayName: Translation.tr("Top"),
                            icon: "arrow_upward",
                            value: 0 // bottom: false, vertical: false
                        },
                        {
                            displayName: Translation.tr("Left"),
                            icon: "arrow_back",
                            value: 2 // bottom: false, vertical: true
                        },
                        {
                            displayName: Translation.tr("Bottom"),
                            icon: "arrow_downward",
                            value: 1 // bottom: true, vertical: false
                        },
                        {
                            displayName: Translation.tr("Right"),
                            icon: "arrow_forward",
                            value: 3 // bottom: true, vertical: true
                        }
                    ]
                }
            }
            ContentSubsection {
                title: Translation.tr("Automatically hide")
                Layout.fillWidth: false

                ConfigSelectionArray {
                    currentValue: Config.options.bar.autoHide.enable
                    onSelected: newValue => {
                        Config.options.bar.autoHide.enable = newValue; // Update local copy
                    }
                    options: [
                        {
                            displayName: Translation.tr("No"),
                            icon: "close",
                            value: false
                        },
                        {
                            displayName: Translation.tr("Yes"),
                            icon: "check",
                            value: true
                        }
                    ]
                }
            }
        }

        ConfigRow {
            
            ContentSubsection {
                title: Translation.tr("Corner style")
                Layout.fillWidth: true

                ConfigSelectionArray {
                    currentValue: Config.options.bar.cornerStyle
                    onSelected: newValue => {
                        Config.options.bar.cornerStyle = newValue; // Update local copy
                    }
                    options: [
                        {
                            displayName: Translation.tr("Hug"),
                            icon: "line_curve",
                            value: 0
                        },
                        {
                            displayName: Translation.tr("Float"),
                            icon: "page_header",
                            value: 1
                        },
                        {
                            displayName: Translation.tr("Rect"),
                            icon: "toolbar",
                            value: 2
                        }
                    ]
                }
            }

            ContentSubsection {
                title: Translation.tr("Group style")
                Layout.fillWidth: false

                ConfigSelectionArray {
                    currentValue: Config.options.bar.borderless
                    onSelected: newValue => {
                        Config.options.bar.borderless = newValue; // Update local copy
                    }
                    options: [
                        {
                            displayName: Translation.tr("Pills"),
                            icon: "location_chip",
                            value: false
                        },
                        {
                            displayName: Translation.tr("Line-separated"),
                            icon: "split_scene",
                            value: true
                        }
                    ]
                }
            }
        }

        ConfigSpinBox {
            icon: "straighten"
            text: Config.options?.bar?.vertical ? Translation.tr("Bar thickness (pixels)") : Translation.tr("Bar height (pixels)")
            value: (Config.options?.bar?.height > 0) ? Config.options.bar.height : Appearance.sizes.baseBarHeight
            from: 16
            to: 96
            stepSize: 1
            onValueChanged: {
                Config.options.bar.height = value;
            }
        }
    }

    ContentSection {
        icon: "shelf_auto_hide"
        title: Translation.tr("Tray")

        ConfigSwitch {
            buttonIcon: "keep"
            text: Translation.tr('Make icons pinned by default')
            checked: Config.options.tray.invertPinnedItems
            onCheckedChanged: {
                Config.options.tray.invertPinnedItems = checked;
            }
        }
        
        ConfigSwitch {
            buttonIcon: "colors"
            text: Translation.tr('Tint icons')
            checked: Config.options.tray.monochromeIcons
            onCheckedChanged: {
                Config.options.tray.monochromeIcons = checked;
            }
        }
    }

    ContentSection {
        icon: "widgets"
        title: Translation.tr("Utility buttons")

        ConfigRow {
            uniform: true
            ConfigSwitch {
                buttonIcon: "content_cut"
                text: Translation.tr("Screen snip")
                checked: Config.options.bar.utilButtons.showScreenSnip
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showScreenSnip = checked;
                }
            }
            ConfigSwitch {
                buttonIcon: "colorize"
                text: Translation.tr("Color picker")
                checked: Config.options.bar.utilButtons.showColorPicker
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showColorPicker = checked;
                }
            }
        }
        ConfigRow {
            uniform: true
            ConfigSwitch {
                buttonIcon: "keyboard"
                text: Translation.tr("Keyboard toggle")
                checked: Config.options.bar.utilButtons.showKeyboardToggle
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showKeyboardToggle = checked;
                }
            }
            ConfigSwitch {
                buttonIcon: "mic"
                text: Translation.tr("Mic toggle")
                checked: Config.options.bar.utilButtons.showMicToggle
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showMicToggle = checked;
                }
            }
        }
        ConfigRow {
            uniform: true
            ConfigSwitch {
                buttonIcon: "dark_mode"
                text: Translation.tr("Dark/Light toggle")
                checked: Config.options.bar.utilButtons.showDarkModeToggle
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showDarkModeToggle = checked;
                }
            }
            ConfigSwitch {
                buttonIcon: "speed"
                text: Translation.tr("Performance Profile toggle")
                checked: Config.options.bar.utilButtons.showPerformanceProfileToggle
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showPerformanceProfileToggle = checked;
                }
            }
        }
        ConfigRow {
            uniform: true
            ConfigSwitch {
                buttonIcon: "videocam"
                text: Translation.tr("Record")
                checked: Config.options.bar.utilButtons.showScreenRecord
                onCheckedChanged: {
                    Config.options.bar.utilButtons.showScreenRecord = checked;
                }
            }
        }
    }

    ContentSection {
        icon: "cloud"
        title: Translation.tr("Weather")
        ConfigSwitch {
            buttonIcon: "check"
            text: Translation.tr("Enable")
            checked: Config.options.bar.weather.enable
            onCheckedChanged: {
                Config.options.bar.weather.enable = checked;
            }
        }
    }

    ContentSection {
        icon: "workspaces"
        title: Translation.tr("Workspaces")

        ConfigSwitch {
            buttonIcon: "counter_1"
            text: Translation.tr('Always show numbers')
            checked: Config.options.bar.workspaces.alwaysShowNumbers
            onCheckedChanged: {
                Config.options.bar.workspaces.alwaysShowNumbers = checked;
            }
        }

        ConfigSwitch {
            buttonIcon: "award_star"
            text: Translation.tr('Show app icons')
            checked: Config.options.bar.workspaces.showAppIcons
            onCheckedChanged: {
                Config.options.bar.workspaces.showAppIcons = checked;
            }
        }

        ConfigSwitch {
            buttonIcon: "colors"
            text: Translation.tr('Tint app icons')
            checked: Config.options.bar.workspaces.monochromeIcons
            onCheckedChanged: {
                Config.options.bar.workspaces.monochromeIcons = checked;
            }
        }

        ConfigSpinBox {
            icon: "view_column"
            text: Translation.tr("Workspaces shown")
            value: Config.options.bar.workspaces.shown
            from: 1
            to: 30
            stepSize: 1
            onValueChanged: {
                Config.options.bar.workspaces.shown = value;
            }
        }

        ConfigSpinBox {
            icon: "touch_long"
            text: Translation.tr("Number show delay when pressing Super (ms)")
            value: Config.options.bar.workspaces.showNumberDelay
            from: 0
            to: 1000
            stepSize: 50
            onValueChanged: {
                Config.options.bar.workspaces.showNumberDelay = value;
            }
        }

        ContentSubsection {
            title: Translation.tr("Number style")

            ConfigSelectionArray {
                currentValue: JSON.stringify(Config.options.bar.workspaces.numberMap)
                onSelected: newValue => {
                    Config.options.bar.workspaces.numberMap = JSON.parse(newValue)
                }
                options: [
                    {
                        displayName: Translation.tr("Normal"),
                        icon: "timer_10",
                        value: '[]'
                    },
                    {
                        displayName: Translation.tr("Han chars"),
                        icon: "square_dot",
                        value: '["一","二","三","四","五","六","七","八","九","十","十一","十二","十三","十四","十五","十六","十七","十八","十九","二十"]'
                    },
                    {
                        displayName: Translation.tr("Roman"),
                        icon: "account_balance",
                        value: '["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"]'
                    }
                ]
            }
        }
    }

    ContentSection {
        icon: "tooltip"
        title: Translation.tr("Tooltips")
        ConfigSwitch {
            buttonIcon: "ads_click"
            text: Translation.tr("Click to show")
            checked: Config.options.bar.tooltips.clickToShow
            onCheckedChanged: {
                Config.options.bar.tooltips.clickToShow = checked;
            }
        }
    }
}
