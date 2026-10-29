import QtQuick
import QtQuick.Layouts
import qs.Commons
import qs.Commons as Commons
import qs.Ui as Ui

Item {
    id: root
    required property var controller
    property alias inputItem: input
    readonly property var field: controller.editing
    readonly property var validation: controller.validation(input.text)
    implicitHeight: column.implicitHeight
    function begin() {
        input.text = String(controller.value(field) ?? "");
        Qt.callLater(function() { input.forceActiveFocus(); input.selectAll(); });
    }
    function step(direction) {
        if (field.type !== "number") return;
        const parsed = Number(input.text);
        const value = isFinite(parsed) && input.text.trim() ? parsed : Number(controller.value(field));
        input.text = String(Math.max(field.min, Math.min(field.max, value + direction * field.step)));
        input.forceActiveFocus();
        input.selectAll();
    }
    Component.onCompleted: begin()
    Keys.priority: Keys.AfterItem
    Keys.onEscapePressed: event => { controller.back(); event.accepted = true; }
    ColumnLayout {
        id: column
        width: parent.width
        spacing: Style.spacing.md
        Text {
            Layout.fillWidth: true
            text: root.field?.label ?? ""
            color: Commons.Color.menu.text
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.heading
            wrapMode: Text.Wrap
        }
        Text {
            Layout.fillWidth: true
            visible: !!text
            text: root.field?.hint || (root.field?.type === "number" ? "Entre " + root.field.min + " y " + root.field.max + (root.field.unit ? " " + root.field.unit : "") : "Los cambios se aplican al guardar.")
            color: Commons.Color.menu.text
            opacity: 0.65
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.bodySmall
            wrapMode: Text.Wrap
        }
        RowLayout {
            Layout.fillWidth: true
            Ui.Button { visible: root.field?.type === "number"; text: "−"; focusable: true; bordered: true; onClicked: root.step(-1) }
            Ui.TextField {
                id: input
                Layout.fillWidth: true
                foreground: Commons.Color.menu.text
                accent: Commons.Color.accent
                font.family: Style.font.menuFamily
                selectByMouse: true
                inputMethodHints: root.field?.type === "number" ? Qt.ImhFormattedNumbersOnly : Qt.ImhNone
                onAccepted: if (!inputMethodComposing && root.validation.ok) root.controller.commit(text)
                Keys.onUpPressed: event => { if (root.field.type === "number" && !inputMethodComposing) root.step(1); else event.accepted = false; }
                Keys.onDownPressed: event => { if (root.field.type === "number" && !inputMethodComposing) root.step(-1); else event.accepted = false; }
            }
            Ui.Button { visible: root.field?.type === "number"; text: "+"; focusable: true; bordered: true; onClicked: root.step(1) }
        }
        Text {
            Layout.fillWidth: true
            visible: !root.validation.ok
            text: root.validation.error ?? ""
            color: root.validation.ok ? Commons.Color.menu.text : Commons.Color.urgent
            opacity: root.validation.ok ? 0.55 : 1
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.caption
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Ui.Button { text: "Cancelar"; focusable: true; onClicked: root.controller.back() }
            Ui.Button { text: "Guardar"; focusable: true; bordered: true; enabled: root.validation.ok; onClicked: root.controller.commit(input.text) }
        }
    }
}
