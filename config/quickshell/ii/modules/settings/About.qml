import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import Qt5Compat.GraphicalEffects
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets

ContentPage {
    id: page
    forceWidth: true
    bottomContentPadding: 30

    readonly property string github: "https://github.com/saselandia/Better-Window-Manager"
    readonly property string gitlab: "https://gitlab.com/saselandia/bwm"
    readonly property string documentation: page.gitlab + "/-/blob/main/README.es.md"
    readonly property string issues: page.github + "/issues"

    ContentSection {
        icon: "computer"
        title: Translation.tr("Distro")

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: distroContent.implicitHeight + 48
            radius: Appearance.rounding.large
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            RowLayout {
                id: distroContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.margins: 24
                spacing: 24

                Item {
                    Layout.preferredWidth: 76
                    Layout.preferredHeight: 76
                    StyledImage {
                        id: distroImage
                        anchors.fill: parent
                        source: !SystemInfo.distroReady || SystemInfo.logo === SystemInfo.distroIcon
                            ? Qt.resolvedUrl("../../assets/icons/" + SystemInfo.distroIcon + ".svg")
                            : Quickshell.iconPath(SystemInfo.logo)
                        fallbacks: [Qt.resolvedUrl("../../assets/icons/" + SystemInfo.distroIcon + ".svg"),
                                    Qt.resolvedUrl("../../assets/icons/linux-symbolic.svg")]
                        fillMode: Image.PreserveAspectFit
                    }
                    ColorOverlay {
                        anchors.fill: distroImage
                        source: distroImage
                        color: Appearance.colors.colPrimary
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    StyledText {
                        Layout.fillWidth: true
                        text: SystemInfo.distroName
                        textFormat: Text.PlainText
                        font.pixelSize: Appearance.font.pixelSize.title
                        font.weight: Font.DemiBold
                        wrapMode: Text.Wrap
                        color: Appearance.colors.colOnLayer2
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: [SystemInfo.distroVersion, SystemInfo.desktopEnvironment,
                               SystemInfo.windowingSystem].filter(Boolean).join(" · ")
                        font.pixelSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colSubtext
                        wrapMode: Text.Wrap
                    }
                    StyledText {
                        visible: SystemInfo.homeUrl !== ""
                        Layout.fillWidth: true
                        textFormat: Text.PlainText
                        text: SystemInfo.homeUrl
                        color: Appearance.colors.colPrimary
                        font.pixelSize: Appearance.font.pixelSize.small
                        wrapMode: Text.WrapAnywhere
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally(SystemInfo.homeUrl)
                        }
                    }
                }
            }
        }
    }

    ContentSection {
        icon: "desktop_windows"
        title: "WM"

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: projectContent.implicitHeight + 40
            radius: Appearance.rounding.large
            color: Appearance.colors.colLayer2
            border.width: 1
            border.color: Appearance.colors.colOutlineVariant

            ColumnLayout {
                id: projectContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 20
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 24
                    Image {
                        Layout.preferredWidth: 160
                        Layout.preferredHeight: 58
                        source: Quickshell.env("HOME") + "/.config/hypr/omarchy/boot/logo.png"
                        fillMode: Image.PreserveAspectFit
                        layer.enabled: true
                        layer.effect: MultiEffect {
                            colorization: 1
                            colorizationColor: Appearance.colors.colPrimary
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        StyledText {
                            text: "BWM"
                            font.pixelSize: Appearance.font.pixelSize.title
                            font.weight: Font.DemiBold
                            color: Appearance.colors.colOnLayer2
                        }
                        StyledText {
                            text: "Better Window Manager"
                            color: Appearance.colors.colSubtext
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }
                StyledText {
                    Layout.fillWidth: true
                    text: "Tu escritorio sobre Hyprland y Quickshell. Tres estilos, tus temas y tus plugins."
                    color: Appearance.colors.colSubtext
                    wrapMode: Text.Wrap
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 8
                    RippleButtonWithIcon {
                        materialIcon: "code"
                        mainText: "GitLab · saselandia/bwm"
                        onClicked: Qt.openUrlExternally(page.gitlab)
                    }
                    RippleButtonWithIcon {
                        materialIcon: "code_blocks"
                        mainText: "GitHub · Better-Window-Manager"
                        onClicked: Qt.openUrlExternally(page.github)
                    }
                }
            }
        }

        Flow {
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 8
            RippleButtonWithIcon {
                materialIcon: "auto_stories"
                mainText: Translation.tr("Documentation")
                onClicked: Qt.openUrlExternally(page.documentation)
            }
            RippleButtonWithIcon {
                materialIcon: "bug_report"
                mainText: Translation.tr("Issues")
                onClicked: Qt.openUrlExternally(page.issues)
            }
            RippleButton {
                implicitWidth: starContent.implicitWidth + 24
                implicitHeight: 40
                buttonRadius: Appearance.rounding.small
                colBackground: Appearance.colors.colLayer2
                onClicked: Qt.openUrlExternally(page.github)
                contentItem: RowLayout {
                    id: starContent
                    spacing: 4
                    AnimatedImage {
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        source: Qt.resolvedUrl("../../assets/bwm-star.gif")
                        playing: page.visible
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                    }
                    StyledText {
                        text: "Star en GitHub"
                        color: Appearance.colors.colOnLayer2
                        font.pixelSize: Appearance.font.pixelSize.small
                    }
                }
            }
        }
    }
}
