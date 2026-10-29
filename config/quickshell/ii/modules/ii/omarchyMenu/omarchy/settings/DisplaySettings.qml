import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import "display/Layout.js" as Geometry

// Retro's display editor owns keyboard navigation; edits are a draft until Apply.
FocusScope {
    id: root
    required property var controller
    readonly property bool handlesKeyboardNavigation: true
    property string managerScript: Quickshell.env("HOME") + "/.config/hypr/scripts/monitor-manager.py"
    property var monitors: []
    property var original: []
    property var appliedDraft: []
    property int selectedIndex: 0
    property int rowIndex: 0
    property bool editingLayout: false
    property bool keyboardLayout: false
    readonly property bool keyboardHintsVisible: editingLayout && keyboardLayout
    property var editingFrame: null
    property string message: ""
    property bool messageIsError: false
    readonly property var currentMonitor: monitors[selectedIndex] ?? null
    readonly property bool dirty: JSON.stringify(monitors) !== JSON.stringify(original)
    readonly property bool busy: listProcess.running || applyProcess.running
    readonly property var rows: [
        {key:"monitor", label:"Pantalla"}, {key:"resolution", label:"Resolución"},
        {key:"rate", label:"Frecuencia"}, {key:"scale", label:"Escala"},
        {key:"rotation", label:"Giro"}, {key:"enabled", label:"Pantalla activa"},
        {key:"primary", label:"Pantalla principal"}, {key:"workspaces", label:"Espacios de trabajo"},
        {key:"x", label:"Posición horizontal"}, {key:"y", label:"Posición vertical"},
        {key:"apply", label:"Aplicar cambios"}, {key:"reload", label:"Restablecer / detectar pantallas"}
    ]
    readonly property var frame: editingLayout && editingFrame ? editingFrame : Geometry.bounds(monitors, 100)
    activeFocusOnTab: true
    focus: true

    function name(m) { return m ? (m.model || m.description || "Pantalla") : "Sin pantallas"; }
    function load(data) {
        const selected = currentMonitor?.description;
        monitors = Geometry.copy(data);
        original = Geometry.copy(data);
        let index = data.findIndex(m => m.description === selected);
        if (index < 0) index = data.findIndex(m => m.focused);
        selectedIndex = Math.max(0, index);
        editingLayout = false;
        editingFrame = null;
    }
    function refreshMonitors() {
        if (busy) return;
        message = "";
        listProcess.running = true;
    }
    function chooseMonitor(delta) {
        if (!monitors.length) return;
        selectedIndex = (selectedIndex + delta + monitors.length) % monitors.length;
    }
    function extendFrame() {
        if (!editingLayout) return;
        const b = Geometry.bounds(monitors, 100), previous = editingFrame ?? b;
        const x = Math.min(b.x, previous.x), y = Math.min(b.y, previous.y);
        editingFrame = {x:x,y:y,width:Math.max(b.x+b.width,previous.x+previous.width)-x,height:Math.max(b.y+b.height,previous.y+previous.height)-y};
    }
    function beginLayout(index, keyboard = true) {
        if (busy) return;
        if (index !== undefined) selectedIndex = index;
        if (!currentMonitor || currentMonitor.disabled) { message = "Activa la pantalla antes de moverla"; return; }
        rowIndex = 0;
        if (!editingLayout) editingFrame = Geometry.bounds(monitors, 100);
        editingLayout = true;
        keyboardLayout = keyboard;
        scroll.contentY = 0;
        message = "";
        forceActiveFocus();
    }
    function finishLayout() {
        monitors = Geometry.normalize(Geometry.snap(monitors, selectedIndex, 16));
        editingLayout = false;
        editingFrame = null;
        rowIndex = 0;
        forceActiveFocus();
    }
    function moveMonitor(dx, dy) {
        if (busy) return;
        monitors = Geometry.move(monitors, selectedIndex, dx, dy);
        extendFrame();
    }
    function resizeMonitor(axis, direction) {
        monitors = Geometry.resize(monitors, selectedIndex, axis, direction);
        extendFrame();
    }
    function setValue(key, value) {
        const list = Geometry.copy(monitors);
        if (!list[selectedIndex]) return;
        list[selectedIndex][key] = value;
        monitors = list;
    }
    function adjust(key, delta) {
        const m = currentMonitor;
        if (!m || busy) return;
        message = "";
        if (key === "monitor") chooseMonitor(delta);
        else if (key === "resolution") monitors = Geometry.setResolution(monitors, selectedIndex, Geometry.cycle(Geometry.resolutions(m), m.width+"x"+m.height, delta));
        else if (key === "rate") setValue("refreshRate", Geometry.cycle(Geometry.rates(m), m.refreshRate, delta));
        else if (key === "scale") setValue("scale", Geometry.cycle([0.75,1,1.25,1.5,1.75,2,2.5,3], m.scale, delta));
        else if (key === "rotation") setValue("transform", Geometry.cycle([0,1,2,3], m.transform || 0, delta));
        else if (key === "enabled") {
            if (delta < 0 && monitors.filter(m => !m.disabled).length <= 1 && !m.disabled) { message = "Debe quedar al menos una pantalla activa"; messageIsError = true; return; }
            setValue("disabled", delta < 0);
        } else if (key === "primary" || key === "workspaces") {
            const list = Geometry.copy(monitors);
            const workspaces = key === "primary" ? (delta > 0 ? "1-9" : "10") : Geometry.cycle(["1-9","10","1-5","6-10"], m.workspaces || (m.is_primary ? "1-9" : "10"), delta);
            list[selectedIndex].workspaces = workspaces;
            list[selectedIndex].is_primary = workspaces === "1-9";
            if (workspaces === "1-9") for (let i=0; i<list.length; i++) {
                if (i === selectedIndex) continue;
                list[i].is_primary = false;
                if (list[i].workspaces === "1-9") list[i].workspaces = "10";
            }
            monitors = list;
        } else if (key === "x" || key === "y") moveMonitor(key === "x" ? delta*40 : 0, key === "y" ? delta*40 : 0);
    }
    function value(key) {
        const m = currentMonitor;
        if (key === "apply") return applyProcess.running ? "Aplicando…" : dirty ? "Guardar en Hyprland" : "Sin cambios";
        if (key === "reload") return listProcess.running ? "Detectando…" : "";
        if (!m) return "";
        if (key === "monitor") return (selectedIndex+1) + " / " + monitors.length + " · " + name(m);
        if (key === "resolution") return m.width + " × " + m.height;
        if (key === "rate") return m.refreshRate + " Hz";
        if (key === "scale") return Math.round(m.scale*100) + " %";
        if (key === "rotation") return ["Normal", "90°", "180°", "270°"][m.transform || 0];
        if (key === "primary") return m.is_primary ? "Sí · espacios 1–9" : "No";
        if (key === "workspaces") return m.workspaces || (m.is_primary ? "1-9" : "10");
        if (key === "enabled") return m.disabled ? "Desactivada" : "Activada";
        return String(m[key]);
    }
    function applyConfiguration() {
        if (!dirty || busy) return;
        const error = Geometry.validate(monitors);
        if (error) { message = error; messageIsError = true; return; }
        const data = Geometry.normalize(monitors);
        appliedDraft = Geometry.copy(data);
        applyProcess.command = ["python3", managerScript, "apply", JSON.stringify(data)];
        applyProcess.running = true;
    }
    function activate() {
        if (busy) return;
        if (rowIndex === 0 || rows[rowIndex-1]?.key === "monitor") beginLayout();
        else {
            const key = rows[rowIndex-1]?.key;
            if (key === "apply") applyConfiguration();
            else if (key === "reload") refreshMonitors();
            else if (key === "enabled") adjust(key, currentMonitor?.disabled ? 1 : -1);
            else adjust(key, 1);
        }
    }
    function selectRow(index) {
        rowIndex = Math.max(0, Math.min(rows.length,index));
        forceActiveFocus();
        Qt.callLater(function() {
            const item = rowIndex === 0 ? diagram : options.itemAt(rowIndex-1);
            if (!item) return;
            const y = item.mapToItem(scroll.contentItem,0,0).y;
            if (y < scroll.contentY) scroll.contentY = y;
            else if (y+item.height > scroll.contentY+scroll.height) scroll.contentY = y+item.height-scroll.height;
        });
    }
    Keys.priority: Keys.BeforeItem
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape || event.key === Qt.Key_Backspace) {
            if (editingLayout) finishLayout();
            else controller.back();
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
            if (editingLayout) finishLayout(); else activate();
        } else if (editingLayout && (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab)) {
            chooseMonitor(event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier) ? -1 : 1);
        } else if ([Qt.Key_Up,Qt.Key_Down,Qt.Key_Left,Qt.Key_Right].includes(event.key)) {
            if (editingLayout) {
                keyboardLayout = true;
                const dx = event.key === Qt.Key_Left ? -1 : event.key === Qt.Key_Right ? 1 : 0;
                const dy = event.key === Qt.Key_Up ? -1 : event.key === Qt.Key_Down ? 1 : 0;
                if (event.modifiers & Qt.ControlModifier) resizeMonitor(dx ? "x" : "y", dx || dy);
                else { const step = event.modifiers & Qt.ShiftModifier ? 10 : 40; moveMonitor(dx*step,dy*step); }
            } else if (event.key === Qt.Key_Up || event.key === Qt.Key_Down) selectRow(rowIndex + (event.key === Qt.Key_Up ? -1 : 1));
            else if (rowIndex === 0) chooseMonitor(event.key === Qt.Key_Left ? -1 : 1);
            else adjust(rows[rowIndex-1].key, event.key === Qt.Key_Left ? -1 : 1);
        } else if (!editingLayout && (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab)) selectRow(rowIndex + (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier) ? -1 : 1));
        else if (!editingLayout && event.key === Qt.Key_Home) selectRow(0);
        else if (!editingLayout && event.key === Qt.Key_End) selectRow(rows.length);
        else return;
        event.accepted = true;
    }
    Process {
        id: listProcess
        running: true
        command: ["python3", root.managerScript, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { const data = JSON.parse(text); if (!Array.isArray(data)) throw new Error("Formato no válido"); root.load(data); }
                catch (error) { root.message = "No se pudieron leer las pantallas"; root.messageIsError = true; }
            }
        }
        onExited: code => { if (code !== 0) { root.message = "No se pudieron detectar las pantallas"; root.messageIsError = true; } }
    }
    Process {
        id: applyProcess
        property string result: ""
        onStarted: result = ""
        stdout: StdioCollector { onStreamFinished: applyProcess.result = text }
        onExited: code => {
            let data = {};
            try { data = JSON.parse(result); } catch (error) { }
            root.messageIsError = code !== 0 || data.status !== "success";
            root.message = root.messageIsError ? "No se pudieron aplicar las pantallas" : "Cambios aplicados y guardados";
            if (!root.messageIsError) { root.monitors = Geometry.copy(root.appliedDraft); root.original = Geometry.copy(root.appliedDraft); }
        }
    }
    Flickable {
        id: scroll
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: actions.top; bottomMargin: Style.spacing.sm }
        clip: true
        contentWidth: width
        contentHeight: content.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: content
            width: scroll.width
            spacing: Style.spacing.sm
            Rectangle {
                id: diagram
                Layout.fillWidth: true
                Layout.preferredHeight: Style.space(184)
                color: Util.alpha(Commons.Color.menu.text,0.035)
                border.width: 1
                border.color: root.rowIndex === 0 ? Commons.Color.accent : Util.alpha(Commons.Color.menu.text,0.18)
                Text {
                    x: Style.spacing.sm; y: Style.spacing.sm
                    text: root.editingLayout ? "Editando · " + root.name(root.currentMonitor) : "Distribución de las pantallas"
                    color: root.editingLayout ? Commons.Color.accent : Commons.Color.menu.text
                    font.family: Style.font.menuFamily
                    font.pixelSize: Style.font.bodySmall
                }
                Item {
                    id: viewport
                    anchors.fill: parent
                    anchors.margins: Style.spacing.lg
                    anchors.topMargin: Style.space(30)
                    readonly property real ratio: Math.max(0.001,Math.min(width/root.frame.width,height/root.frame.height))
                    readonly property real offsetX: (width-root.frame.width*ratio)/2
                    readonly property real offsetY: (height-root.frame.height*ratio)/2
                    clip: true
                    Repeater {
                        model: root.monitors.length
                        delegate: Rectangle {
                            id: screenRect
                            required property int index
                            readonly property var modelData: root.monitors[index]
                            readonly property var logicalSize: Geometry.size(modelData)
                            readonly property bool selected: index === root.selectedIndex
                            x: viewport.offsetX+(modelData.x-root.frame.x)*viewport.ratio
                            y: viewport.offsetY+(modelData.y-root.frame.y)*viewport.ratio
                            width: logicalSize.width*viewport.ratio
                            height: logicalSize.height*viewport.ratio
                            color: selected ? Util.alpha(Commons.Color.accent,root.editingLayout ? 0.25 : 0.12) : Util.alpha(Commons.Color.menu.text,0.07)
                            border.width: selected ? 2 : 1
                            border.color: selected ? Commons.Color.accent : Util.alpha(Commons.Color.menu.text,0.4)
                            opacity: modelData.disabled ? 0.35 : 1
                            Column {
                                anchors.centerIn: parent
                                width: parent.width-8
                                Text { width: parent.width; text: (screenRect.index+1)+" · "+root.name(screenRect.modelData); horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; color: Commons.Color.menu.text; font.family: Style.font.menuFamily; font.pixelSize: Style.font.caption }
                                Text { width: parent.width; text: screenRect.modelData.width+"×"+screenRect.modelData.height; horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight; color: Commons.Color.menu.text; opacity:0.7; font.family: Style.font.menuFamily; font.pixelSize: Style.font.caption }
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                                property point origin
                                property var snapshot
                                property real ratio: 1
                                property bool moved: false
                                preventStealing: true
                                onPressed: mouse => { root.beginLayout(screenRect.index, false); origin = mapToItem(viewport,mouse.x,mouse.y); snapshot = Geometry.copy(root.monitors); ratio = viewport.ratio; moved = false; }
                                onPositionChanged: mouse => {
                                    if (!pressed || !root.editingLayout) return;
                                    const now = mapToItem(viewport,mouse.x,mouse.y);
                                    if (!moved && Math.hypot(now.x-origin.x,now.y-origin.y) < 4) return;
                                    moved = true;
                                    root.monitors = Geometry.move(snapshot,screenRect.index,Math.round((now.x-origin.x)/ratio),Math.round((now.y-origin.y)/ratio));
                                }
                                onReleased: { if (moved) root.monitors = Geometry.snap(root.monitors,screenRect.index,12/ratio); root.extendFrame(); }
                            }
                        }
                    }
                    Text { anchors.centerIn: parent; visible: !root.monitors.length; text: listProcess.running ? "Detectando pantallas…" : "No se detectaron pantallas"; color: Commons.Color.menu.text; font.family: Style.font.menuFamily; font.pixelSize: Style.font.body }
                }
            }
            Rectangle {
                id: keyboardHelp
                visible: root.keyboardHintsVisible
                Layout.fillWidth: true
                implicitHeight: helpText.implicitHeight+Style.spacing.sm*2
                color: Util.alpha(Commons.Color.accent,0.08)
                Text {
                    id: helpText
                    anchors.fill: parent
                    anchors.margins: Style.spacing.sm
                    text: "Flechas: mover · Ctrl+flechas: resolución\nMayús: movimiento fino · Tab: otra pantalla · Intro / Esc / Borrar: terminar"
                    wrapMode: Text.Wrap
                    color: Commons.Color.menu.text
                    font.family: Style.font.menuFamily
                    font.pixelSize: Style.font.bodySmall
                }
            }
            Repeater {
                id: options
                model: root.rows.slice(0,-2)
                delegate: Rectangle {
                    id: row
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    implicitHeight: Style.space(31)
                    readonly property bool selected: root.rowIndex === index+1 && !root.editingLayout
                    color: selected ? Commons.Color.menu.selectedBackground : rowMouse.containsMouse ? Util.alpha(Commons.Color.menu.text,0.04) : "transparent"
                    Text { anchors.left: parent.left; anchors.leftMargin: Style.spacing.md; anchors.verticalCenter: parent.verticalCenter; width: parent.width*0.43; elide: Text.ElideRight; text: row.modelData.label; color: row.selected ? Commons.Color.menu.selectedText : Commons.Color.menu.text; font.family: Style.font.menuFamily; font.pixelSize: Style.font.body }
                    Text { anchors.right: parent.right; anchors.rightMargin: Style.spacing.md; anchors.verticalCenter: parent.verticalCenter; width: parent.width*0.55; horizontalAlignment: Text.AlignRight; text: root.value(row.modelData.key); color: row.selected ? Commons.Color.menu.selectedText : Commons.Color.menu.text; opacity: row.selected ? 1 : 0.65; elide: Text.ElideRight; font.family: Style.font.menuFamily; font.pixelSize: Style.font.bodySmall }
                    MouseArea { id: rowMouse; anchors.fill: parent; hoverEnabled:true; cursorShape:Qt.PointingHandCursor; onClicked: { if (root.editingLayout) root.finishLayout(); root.selectRow(row.index+1); root.activate(); } }
                }
            }
        }
    }
    ColumnLayout {
        id: actions
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        spacing: Style.spacing.xs
        Repeater {
            model: root.rows.slice(-2)
            delegate: Rectangle {
                required property var modelData
                required property int index
                readonly property int rowNumber: root.rows.length-1+index
                readonly property bool selected: root.rowIndex === rowNumber && !root.editingLayout
                Layout.fillWidth: true
                implicitHeight: Style.space(31)
                color: selected ? Commons.Color.menu.selectedBackground : Util.alpha(Commons.Color.menu.text,0.04)
                Text { anchors.left: parent.left; anchors.leftMargin: Style.spacing.md; anchors.verticalCenter: parent.verticalCenter; text: modelData.label; color: selected ? Commons.Color.menu.selectedText : Commons.Color.menu.text; font.family: Style.font.menuFamily; font.pixelSize: Style.font.body }
                Text { anchors.right: parent.right; anchors.rightMargin: Style.spacing.md; anchors.verticalCenter: parent.verticalCenter; text: root.value(modelData.key); color: selected ? Commons.Color.menu.selectedText : Commons.Color.menu.text; opacity: selected ? 1 : 0.65; font.family: Style.font.menuFamily; font.pixelSize: Style.font.bodySmall }
                MouseArea { anchors.fill: parent; cursorShape:Qt.PointingHandCursor; onClicked: { if (root.editingLayout) root.finishLayout(); root.selectRow(parent.rowNumber); root.activate(); } }
            }
        }
            Text {
                Layout.fillWidth: true
                visible: !!root.message || root.dirty
                text: root.message || "Cambios sin aplicar"
                color: root.messageIsError && root.message ? Commons.Color.urgent : Commons.Color.menu.text
                opacity: root.messageIsError ? 1 : 0.65
                wrapMode: Text.Wrap
                font.family: Style.font.menuFamily
                font.pixelSize: Style.font.caption
            }
    }
}
