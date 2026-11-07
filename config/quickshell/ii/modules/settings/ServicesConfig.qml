import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.functions
import qs.modules.common.widgets

ContentPage {
    id: page
    forceWidth: true

    // BWM: each skin only shows what it uses. The AI sidebar, the overview search (prefixes, web
    // search) and the bar's resource monitor are default (end-4)'s; Retro's Omarchy bar and launcher
    // read only the weather city/units and the save paths; Breeze has no quick toggles (music).
    readonly property bool isDefault: !Appearance.isRetro && !Appearance.isPlasma
    // Folders really in use when the fields are empty: record.sh uses ~/Videos and Retro's recorder the
    // XDG videos folder; screenshots are only copied, except in Retro (~/Pictures/Screenshots)
    readonly property string home: FileUtils.trimFileProtocol(Directories.home).replace(/\/$/, "")
    readonly property string recordingDir: {
        const custom = (Config.options.screenRecord.savePath ?? "").trim();
        if (custom) return custom.replace(/^~/, page.home);
        return Appearance.isRetro ? FileUtils.trimFileProtocol(Directories.videos) : `${page.home}/Videos`;
    }
    readonly property string screenshotDir: {
        const custom = (Config.options.screenSnip.savePath ?? "").trim();
        if (custom) return custom.replace(/^~/, page.home);
        return Appearance.isRetro ? `${FileUtils.trimFileProtocol(Directories.pictures)}/Screenshots` : "";
    }
    property bool promptExpanded: false
    readonly property string promptPreview: {
        // First line of real text, skipping Markdown headings
        const lines = (Config.options.ai.systemPrompt ?? "").split("\n").filter(l => !/^\s*#/.test(l));
        return lines.map(l => l.replace(/^[\-*\s]+/, "").trim()).find(l => l.length > 0) ?? "";
    }

    ContentSection {
        visible: !Appearance.isPlasma
        icon: "music_cast"
        title: Translation.tr("Music Recognition")

        ConfigSpinBox {
            icon: "timer_off"
            text: Translation.tr("Total duration timeout (s)")
            value: Config.options.musicRecognition.timeout
            from: 10
            to: 100
            stepSize: 2
            onValueChanged: {
                Config.options.musicRecognition.timeout = value;
            }
        }
        ConfigSpinBox {
            icon: "av_timer"
            text: Translation.tr("Polling interval (s)")
            value: Config.options.musicRecognition.interval
            from: 2
            to: 10
            stepSize: 1
            onValueChanged: {
                Config.options.musicRecognition.interval = value;
            }
        }
    }

    ContentSection {
        visible: !Appearance.isRetro
        icon: "memory"
        title: Translation.tr("Resources")

        ConfigSpinBox {
            icon: "av_timer"
            text: Translation.tr("Polling interval (ms)")
            value: Config.options.resources.updateInterval
            from: 100
            to: 10000
            stepSize: 100
            onValueChanged: {
                Config.options.resources.updateInterval = value;
            }
        }

    }

    ContentSection {
        icon: "file_open"
        title: Translation.tr("Save paths")

        MaterialTextArea {
            Layout.fillWidth: true
            placeholderText: Translation.tr("Video Recording Path")
            text: Config.options.screenRecord.savePath
            wrapMode: TextEdit.Wrap
            onTextChanged: {
                Config.options.screenRecord.savePath = text;
            }
        }
        StyledText {
            Layout.leftMargin: 12
            text: Translation.tr("In use: %1").arg(page.recordingDir)
            font.pixelSize: Appearance.font.pixelSize.smaller
            color: Appearance.colors.colSubtext
            elide: Text.ElideMiddle
            Layout.fillWidth: true
        }

        MaterialTextArea {
            Layout.fillWidth: true
            placeholderText: Translation.tr("Screenshot Path (leave empty to just copy)")
            text: Config.options.screenSnip.savePath
            wrapMode: TextEdit.Wrap
            onTextChanged: {
                Config.options.screenSnip.savePath = text;
            }
        }
        StyledText {
            Layout.leftMargin: 12
            text: page.screenshotDir ? Translation.tr("In use: %1").arg(page.screenshotDir)
                                     : Translation.tr("In use: only copied to the clipboard")
            font.pixelSize: Appearance.font.pixelSize.smaller
            color: Appearance.colors.colSubtext
            elide: Text.ElideMiddle
            Layout.fillWidth: true
        }
    }

    ContentSection {
        visible: !Appearance.isRetro
        icon: "search"
        title: Translation.tr("Search")

        ConfigSwitch {
            text: Translation.tr("Use Levenshtein distance-based algorithm instead of fuzzy")
            checked: Config.options.search.sloppy
            onCheckedChanged: {
                Config.options.search.sloppy = checked;
            }
            StyledToolTip {
                text: Translation.tr("Could be better if you make a ton of typos,\nbut results can be weird and might not work with acronyms\n(e.g. \"GIMP\" might not give you the paint program)")
            }
        }

        ContentSubsection {
            visible: page.isDefault
            title: Translation.tr("Prefixes")
            ConfigRow {
                uniform: true
                MaterialTextArea {
                    Layout.fillWidth: true
                    placeholderText: Translation.tr("Action")
                    text: Config.options.search.prefix.action
                    wrapMode: TextEdit.Wrap
                    onTextChanged: {
                        Config.options.search.prefix.action = text;
                    }
                }
                MaterialTextArea {
                    Layout.fillWidth: true
                    placeholderText: Translation.tr("Clipboard")
                    text: Config.options.search.prefix.clipboard
                    wrapMode: TextEdit.Wrap
                    onTextChanged: {
                        Config.options.search.prefix.clipboard = text;
                    }
                }
                MaterialTextArea {
                    Layout.fillWidth: true
                    placeholderText: Translation.tr("Emojis")
                    text: Config.options.search.prefix.emojis
                    wrapMode: TextEdit.Wrap
                    onTextChanged: {
                        Config.options.search.prefix.emojis = text;
                    }
                }
            }

            ConfigRow {
                uniform: true
                MaterialTextArea {
                    Layout.fillWidth: true
                    placeholderText: Translation.tr("Math")
                    text: Config.options.search.prefix.math
                    wrapMode: TextEdit.Wrap
                    onTextChanged: {
                        Config.options.search.prefix.math = text;
                    }
                }
                MaterialTextArea {
                    Layout.fillWidth: true
                    placeholderText: Translation.tr("Shell command")
                    text: Config.options.search.prefix.shellCommand
                    wrapMode: TextEdit.Wrap
                    onTextChanged: {
                        Config.options.search.prefix.shellCommand = text;
                    }
                }
                MaterialTextArea {
                    Layout.fillWidth: true
                    placeholderText: Translation.tr("Web search")
                    text: Config.options.search.prefix.webSearch
                    wrapMode: TextEdit.Wrap
                    onTextChanged: {
                        Config.options.search.prefix.webSearch = text;
                    }
                }
            }
        }
        ContentSubsection {
            visible: page.isDefault
            title: Translation.tr("Web search")
            MaterialTextArea {
                Layout.fillWidth: true
                placeholderText: Translation.tr("Base URL")
                text: Config.options.search.engineBaseUrl
                wrapMode: TextEdit.Wrap
                onTextChanged: {
                    Config.options.search.engineBaseUrl = text;
                }
            }
        }
    }

    // There's no update indicator in ii for now so we shouldn't show this yet
    // ContentSection {
    //     icon: "deployed_code_update"
    //     title: Translation.tr("System updates (Arch only)")

    //     ConfigSwitch {
    //         text: Translation.tr("Enable update checks")
    //         checked: Config.options.updates.enableCheck
    //         onCheckedChanged: {
    //             Config.options.updates.enableCheck = checked;
    //         }
    //     }

    //     ConfigSpinBox {
    //         icon: "av_timer"
    //         text: Translation.tr("Check interval (mins)")
    //         value: Config.options.updates.checkInterval
    //         from: 60
    //         to: 1440
    //         stepSize: 60
    //         onValueChanged: {
    //             Config.options.updates.checkInterval = value;
    //         }
    //     }
    // }

    ContentSection {
        icon: "weather_mix"
        title: Translation.tr("Weather")
        // BWM: no GPS switch. It needs geoclue, which a desktop without Wi-Fi can't locate, and an
        // empty city already falls back to the IP location (wttr.in), in every skin
        ConfigSwitch {
            buttonIcon: "thermometer"
            text: Translation.tr("Fahrenheit unit")
            checked: Config.options.bar.weather.useUSCS
            onCheckedChanged: {
                Config.options.bar.weather.useUSCS = checked;
            }
            StyledToolTip {
                text: Translation.tr("It may take a few seconds to update")
            }
        }

        MaterialTextArea {
            Layout.fillWidth: true
            placeholderText: Translation.tr("City name (empty: detected from your IP)")
            text: Config.options.bar.weather.city
            wrapMode: TextEdit.Wrap
            onTextChanged: {
                Config.options.bar.weather.city = text;
            }
        }
        ConfigSpinBox {
            visible: !Appearance.isRetro
            icon: "av_timer"
            text: Translation.tr("Polling interval (m)")
            value: Config.options.bar.weather.fetchInterval
            from: 5
            to: 50
            stepSize: 5
            onValueChanged: {
                Config.options.bar.weather.fetchInterval = value;
            }
        }
    }

    ContentSection {
        visible: page.isDefault && Config.options.policies.ai !== 0
        icon: "neurology"
        title: Translation.tr("AI")

        // Folded by default: a one-line summary that opens a small, scrollable editor
        RippleButton {
            Layout.fillWidth: true
            implicitHeight: 40
            buttonRadius: Appearance.rounding.small
            onClicked: page.promptExpanded = !page.promptExpanded
            contentItem: RowLayout {
                spacing: 10
                MaterialSymbol {
                    Layout.leftMargin: 8
                    text: "edit_note"
                    iconSize: Appearance.font.pixelSize.larger
                    color: Appearance.colors.colOnSecondaryContainer
                }
                StyledText {
                    text: Translation.tr("System prompt")
                    color: Appearance.colors.colOnSecondaryContainer
                }
                StyledText {
                    Layout.fillWidth: true
                    visible: !page.promptExpanded
                    text: page.promptPreview
                    elide: Text.ElideRight
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colSubtext
                }
                Item {
                    Layout.fillWidth: true
                    visible: page.promptExpanded
                }
                MaterialSymbol {
                    Layout.rightMargin: 8
                    text: page.promptExpanded ? "expand_less" : "expand_more"
                    iconSize: Appearance.font.pixelSize.larger
                    color: Appearance.colors.colOnSecondaryContainer
                }
            }
        }

        ScrollView {
            visible: page.promptExpanded
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            clip: true

            MaterialTextArea {
                placeholderText: Translation.tr("System prompt")
                text: Config.options.ai.systemPrompt
                wrapMode: TextEdit.Wrap
                font.pixelSize: Appearance.font.pixelSize.smaller
                onTextChanged: {
                    Qt.callLater(() => {
                        Config.options.ai.systemPrompt = text;
                    });
                }
            }
        }
    }
}
