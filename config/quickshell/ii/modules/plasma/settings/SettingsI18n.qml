// SPDX-License-Identifier: GPL-2.0-or-later
pragma Singleton

import QtQuick
import Quickshell
import org.kde.ki18n

// BWM: systemsettings' i18n() in QML, with its own installed catalogue (domain "systemsettings").
Singleton {
    KI18nContext {
        id: ctx
        translationDomain: "systemsettings"
    }
    function i18n(...args) { return ctx.i18n(...args); }
    function i18nc(...args) { return ctx.i18nc(...args); }
}
