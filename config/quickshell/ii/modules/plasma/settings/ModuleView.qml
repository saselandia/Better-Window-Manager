// SPDX-License-Identifier: GPL-2.0-or-later
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import Quickshell
import org.kde.kirigami as Kirigami

/**
 * BWM F11: the module area of systemsettings 6.7.5 (app/ModuleView.cpp, C++ there): header with the
 * module title, the module, and for KCMs the Help / Defaults / Reset / Apply bar driven by the
 * KCM's buttons, needsSave and representsDefaults, and the «unsaved changes» question when leaving.
 */
Item {
    id: view
    required property real headerHeight
    readonly property var entry: SettingsState.current ? SettingsState.current.entry : null
    readonly property var kcm: entry && entry.kind === "kcm" && contentLoader.item ? contentLoader.item.kcm : null
    readonly property int buttons: kcm ? kcm.buttons : 0

    Kirigami.Theme.colorSet: Kirigami.Theme.Window
    Kirigami.Theme.inherit: false

    // Leaving a KCM with changes asks first, as ModuleView::resolveChanges()
    Binding {
        target: SettingsState
        property: "unsavedChanges"
        value: !!(view.kcm && view.kcm.needsSave)
    }
    property var afterResolve: null
    function askBeforeLeaving(next) { view.afterResolve = next; unsavedDialog.open(); }
    Component.onCompleted: SettingsState.askBeforeLeaving = view.askBeforeLeaving

    Binding {
        when: view.kcm !== null
        target: view.kcm
        property: "defaultsIndicatorsVisible"
        value: SettingsState.defaultsIndicatorsVisible
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header aligned with the sidebar's search header. A KCM brings its own (the title and
        // actions toolbar of its page row, as in systemsettings), so it is not repeated there.
        Rectangle {
            visible: !view.entry || view.entry.kind !== "kcm"
            Layout.fillWidth: true
            Layout.preferredHeight: view.headerHeight
            Kirigami.Theme.colorSet: Kirigami.Theme.Header
            Kirigami.Theme.inherit: false
            color: Kirigami.Theme.backgroundColor
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Kirigami.Units.largeSpacing
                anchors.rightMargin: Kirigami.Units.smallSpacing
                Kirigami.Heading {
                    Layout.fillWidth: true
                    level: 3
                    text: view.entry ? SettingsState.label(view.entry) : ""
                    elide: Text.ElideRight
                }
            }
            Kirigami.Separator { anchors.bottom: parent.bottom; width: parent.width }
        }

        Loader {
            id: contentLoader
            Layout.fillWidth: true
            Layout.fillHeight: true
            asynchronous: false
            property var shownEntry: view.entry
            source: {
                const e = view.entry;
                if (!e) return "";
                if (e.kind === "kcm") return Qt.resolvedUrl("KcmPage.qml");
                if (e.kind === "launch") return Qt.resolvedUrl("pages/LaunchPage.qml");
                return Quickshell.shellPath(e.component);
            }
            onLoaded: if (item && "entry" in item) item.entry = view.entry
            onStatusChanged: if (status === Loader.Error) console.warn("BWM settings: page failed to load", source)
        }

        // Errors from the KCM loader (module missing, QML error)
        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.gridUnit * 2
            visible: contentLoader.status === Loader.Error || (view.entry?.kind === "kcm" && (contentLoader.item?.error ?? "") !== "")
            icon.name: "dialog-error"
            text: contentLoader.status === Loader.Error
                ? (SettingsState.spanish ? "No se pudo cargar esta página" : "This page could not be loaded")
                : (contentLoader.item?.error ?? "")
            explanation: SettingsState.kcmApi ? "" : (SettingsState.spanish
                ? "Falta el módulo org.bwm.kcm: ejecuta «make install» en src/bwm-kcmhost."
                : "The org.bwm.kcm module is missing: run «make install» in src/bwm-kcmhost.")
        }

        // KCM buttons bar (KCMultiDialog/ModuleView layout: Help left, Defaults/Reset/Apply right)
        Kirigami.Separator { Layout.fillWidth: true; visible: buttonBar.visible }
        QQC2.ToolBar {
            id: buttonBar
            Layout.fillWidth: true
            visible: view.kcm !== null && ((view.buttons & 2) || (view.buttons & 4) || (view.buttons & 1))
            position: QQC2.ToolBar.Footer
            RowLayout {
                anchors.fill: parent
                QQC2.Button {
                    visible: (view.buttons & 1) !== 0
                    icon.name: "help-contents"
                    text: SettingsState.spanish ? "Ayuda" : "Help"
                    onClicked: Qt.openUrlExternally("https://docs.kde.org/")
                }
                QQC2.Button {
                    visible: (view.buttons & 2) !== 0
                    enabled: view.kcm && !view.kcm.representsDefaults
                    icon.name: "kt-restore-defaults"
                    text: SettingsState.spanish ? "Predeterminados" : "Defaults"
                    onClicked: view.kcm.defaults()
                }
                Item { Layout.fillWidth: true }
                QQC2.Button {
                    visible: (view.buttons & 4) !== 0
                    enabled: view.kcm && view.kcm.needsSave
                    icon.name: "edit-undo"
                    text: SettingsState.spanish ? "Restablecer" : "Reset"
                    QQC2.ToolTip.text: SettingsI18n.i18n("Reset all current changes to previous values")
                    QQC2.ToolTip.visible: hovered
                    onClicked: view.kcm.load()
                }
                QQC2.Button {
                    visible: (view.buttons & 4) !== 0
                    enabled: view.kcm && view.kcm.needsSave
                    icon.name: "dialog-ok-apply"
                    text: SettingsState.spanish ? "Aplicar" : "Apply"
                    onClicked: view.kcm.save()
                }
            }
        }
    }

    Kirigami.PromptDialog {
        id: unsavedDialog
        title: SettingsI18n.i18n("Apply Settings")
        subtitle: SettingsI18n.i18n("The current page has unsaved changes.\nApply the changes or discard them?")
        standardButtons: Kirigami.Dialog.Apply | Kirigami.Dialog.Discard | Kirigami.Dialog.Cancel
        onApplied: { view.kcm.save(); close(); const n = view.afterResolve; view.afterResolve = null; if (n) n(); }
        onDiscarded: { view.kcm.load(); close(); const n = view.afterResolve; view.afterResolve = null; if (n) n(); }
        onRejected: view.afterResolve = null
    }
}
