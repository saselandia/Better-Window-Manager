// SPDX-License-Identifier: GPL-2.0-or-later
// Page shape seen in store widgets: a saveConfig() hook that derives one setting from
// another, and a cfg_ helper that the schema does not declare (never filled or saved).
import QtQuick
import QtQuick.Controls as QQC2
Column {
    property alias cfg_flag: toggle.checked
    property string cfg_derived
    property string cfg_lastSeenVersion: "page-only"
    function saveConfig() { cfg_derived = toggle.checked ? "flag-on" : "flag-off" }
    QQC2.CheckBox { id: toggle; text: "Flag" }
}
