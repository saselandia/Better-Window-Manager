// BWM: settings for the supported containment widgets; external plasmoid hosting is deferred.
import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.modules.common
import qs.modules.plasma.theme
import org.kde.ki18n
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC3
PopupWindow {
    id:root
    property string edge:"bottom"
    readonly property var config:Config.options.bar.plasma
    readonly property bool vertical:(root.config.edge||root.edge)==="left"||(root.config.edge||root.edge)==="right"
    KI18nContext { id:i18nCtx; translationDomain:"plasma_shell_org.kde.plasma.desktop" }
    function tr(text) { return i18nCtx.i18n(text); }
    function widgetLabel(id) {
        const names = {
            kickoff: tr("Application Launcher"),
            pager: tr("Pager"),
            tasks: tr("Task Manager"),
            tray: tr("System Tray"),
            clock: tr("Digital Clock"),
            desktop: tr("Peek at Desktop")
        };
        return names[id] ?? id;
    }
    function closeEditor() {
        const scr = root.anchor.item?.QsWindow?.window?.screen?.name ?? "";
        if (scr) PanelState.setEditing(scr, false);
        root.visible = false;
    }
    function setTaskOption(key, value) {
        const next = Object.assign({}, root.config.taskManager ?? ({}));
        next[key] = value;
        root.config.taskManager = next;
    }
    function setClockOption(key, value) {
        const next = Object.assign({}, root.config.clock ?? ({}));
        next[key] = value;
        root.config.clock = next;
    }
    function holidaysEnabled() {
        const list = root.config.clock?.enabledCalendarPlugins;
        return Array.isArray(list) && list.includes("holidaysevents");
    }
    function toggleHolidayPlugin(enabled) {
        const current = Array.isArray(root.config.clock?.enabledCalendarPlugins)
            ? root.config.clock.enabledCalendarPlugins.slice() : [];
        const filtered = current.filter(p => p !== "holidaysevents");
        if (enabled) filtered.push("holidaysevents");
        setClockOption("enabledCalendarPlugins", filtered);
    }
    color:"transparent"; implicitWidth:380; implicitHeight:690
    anchor.edges:edge==="bottom"?Edges.Top:edge==="top"?Edges.Bottom:edge==="left"?Edges.Right:Edges.Left
    anchor.gravity:anchor.edges
    BlurPath { id:bgPath; path:"dialogs/background" }
    KSvg.FrameSvgItem { anchors.fill:parent; imagePath:bgPath.resolved }
    ColumnLayout {
        id:outer
        anchors.fill:parent; anchors.margins:16; spacing:8
        focus:root.visible
        Keys.onEscapePressed:event=>{ root.closeEditor(); event.accepted=true; }
        PC3.Label { objectName:"panel-editor-title"; text:root.tr("Panel Settings"); font.bold:true }
        PC3.ScrollView {
            Layout.fillWidth:true; Layout.fillHeight:true
            clip:true
            ColumnLayout {
                id:content
                width:parent.width
                spacing:8
                PC3.ComboBox {
                    Layout.fillWidth:true
                    Accessible.name:root.tr("Position")
                    model:[
                        ({label:root.tr("Bottom"),value:"bottom"}),
                        ({label:root.tr("Top"),value:"top"}),
                        ({label:root.tr("Left"),value:"left"}),
                        ({label:root.tr("Right"),value:"right"})
                    ]
                    textRole:"label"; valueRole:"value"
                    currentIndex:indexOfValue(root.config.edge||root.edge)
                    onActivated:root.config.edge=currentValue
                }
                PC3.ComboBox {
                    Layout.fillWidth:true
                    Accessible.name:root.tr("Visibility")
                    model:[
                        ({label:root.tr("Always Visible"),value:"always"}),
                        ({label:root.tr("Auto Hide"),value:"autoHide"}),
                        ({label:root.tr("Dodge Windows"),value:"dodge"}),
                        ({label:root.tr("Windows Go Below"),value:"windowsGoBelow"})
                    ]
                    textRole:"label"; valueRole:"value"
                    currentIndex:indexOfValue(root.config.visibility)
                    onActivated:root.config.visibility=currentValue
                }
                PC3.ComboBox {
                    Layout.fillWidth:true
                    Accessible.name:root.tr("Opacity")
                    model:[
                        ({label:root.tr("Adaptive"),value:"adaptive"}),
                        ({label:root.tr("Translucent"),value:"translucent"}),
                        ({label:root.tr("Opaque"),value:"opaque"})
                    ]
                    textRole:"label"; valueRole:"value"
                    currentIndex:indexOfValue(root.config.style==="floating"?"adaptive":root.config.style)
                    onActivated:root.config.style=currentValue
                }
                PC3.ComboBox {
                    Layout.fillWidth:true
                    Accessible.name:root.tr("Alignment")
                    model:[
                        ({label:root.vertical?root.tr("Top"):root.tr("Left"),value:"start"}),
                        ({label:root.tr("Center"),value:"center"}),
                        ({label:root.vertical?root.tr("Bottom"):root.tr("Right"),value:"end"})
                    ]
                    textRole:"label"; valueRole:"value"
                    currentIndex:indexOfValue(root.config.alignment)
                    onActivated:root.config.alignment=currentValue
                }
                PC3.CheckBox { text:root.tr("Floating"); checked:root.config.floating; onToggled:root.config.floating=checked }
                RowLayout {
                    PC3.Label { text:root.vertical?root.tr("Panel Width"):root.tr("Panel Height") }
                    PC3.Slider {
                        Layout.fillWidth:true
                        Accessible.name:root.vertical?root.tr("Panel Width"):root.tr("Panel Height")
                        from:24; to:96; stepSize:2; value:root.config.thickness||44
                        onMoved:root.config.thickness=value
                    }
                }
                RowLayout {
                    PC3.Label { text:root.tr("Length") }
                    PC3.Slider {
                        Layout.fillWidth:true
                        Accessible.name:root.tr("Length")
                        from:.25; to:1; stepSize:.05; value:root.config.length
                        onMoved:root.config.length=value
                    }
                }
                PC3.Label { text:root.tr("Widgets"); font.bold:true }
                Flow {
                    Layout.fillWidth:true; spacing:4
                    Repeater {
                        model:["kickoff","pager","tasks","tray","clock","desktop"]
                        PC3.CheckBox {
                            required property string modelData
                            text:root.widgetLabel(modelData); checked:(root.config.widgets??[]).includes(modelData)
                            onToggled: {
                                const current=root.config.widgets??[];
                                root.config.widgets=checked?current.concat([modelData]):current.filter(x=>x!==modelData);
                            }
                        }
                    }
                }
                Repeater {
                    model:root.config.widgets
                    RowLayout {
                        required property string modelData
                        required property int index
                        PC3.Label { Layout.fillWidth:true; text:root.widgetLabel(parent.modelData) }
                        PC3.ToolButton {
                            icon.name:"go-up"; enabled:parent.index>0
                            Accessible.name:root.tr("Move up") + " " + root.widgetLabel(parent.modelData)
                            onClicked: {
                                const values=root.config.widgets.slice();
                                const i=parent.index;
                                [values[i-1],values[i]]=[values[i],values[i-1]];
                                root.config.widgets=values;
                            }
                        }
                        PC3.ToolButton {
                            icon.name:"go-down"; enabled:parent.index<root.config.widgets.length-1
                            Accessible.name:root.tr("Move down") + " " + root.widgetLabel(parent.modelData)
                            onClicked: {
                                const values=root.config.widgets.slice();
                                const i=parent.index;
                                [values[i+1],values[i]]=[values[i],values[i+1]];
                                root.config.widgets=values;
                            }
                        }
                    }
                }
                PC3.Label {
                    visible:(root.config.widgets??[]).includes("tasks")
                    text:root.widgetLabel("tasks"); font.bold:true
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("tasks")
                    text:root.tr("Show only tasks from current screen")
                    checked:Boolean(root.config.taskManager?.showOnlyCurrentScreen)
                    onToggled:root.setTaskOption("showOnlyCurrentScreen", checked)
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("tasks")
                    text:root.tr("Show only tasks from current desktop")
                    checked:Boolean(root.config.taskManager?.showOnlyCurrentDesktop)
                    onToggled:root.setTaskOption("showOnlyCurrentDesktop", checked)
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("tasks")
                    text:root.tr("Show only minimized tasks")
                    checked:Boolean(root.config.taskManager?.showOnlyMinimized)
                    onToggled:root.setTaskOption("showOnlyMinimized", checked)
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("tasks")
                    text:root.tr("Group windows by program name")
                    checked:(root.config.taskManager?.groupingStrategy ?? 1) !== 0
                    onToggled:root.setTaskOption("groupingStrategy", checked ? 1 : 0)
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("tasks")
                    text:root.tr("Cycle through tasks with mouse wheel")
                    checked:root.config.taskManager?.wheelEnabled ?? true
                    onToggled:root.setTaskOption("wheelEnabled", checked)
                }
                PC3.Label {
                    visible:(root.config.widgets??[]).includes("clock")
                    text:root.widgetLabel("clock"); font.bold:true
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("clock")
                    text:root.tr("Show week numbers")
                    checked:root.config.clock?.showWeekNumbers ?? true
                    onToggled:root.setClockOption("showWeekNumbers", checked)
                }
                PC3.CheckBox {
                    visible:(root.config.widgets??[]).includes("clock")
                    text:root.tr("Show holidays")
                    checked:root.holidaysEnabled()
                    onToggled:root.toggleHolidayPlugin(checked)
                }
            }
        }
        PC3.Button {
            objectName:"panel-editor-done"
            text:root.tr("Done")
            Layout.alignment:Qt.AlignRight
            onClicked:root.closeEditor()
        }
    }
}
