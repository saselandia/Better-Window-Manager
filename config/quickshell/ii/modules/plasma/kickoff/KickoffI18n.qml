/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
pragma Singleton

import QtQuick
import Quickshell
import org.kde.ki18n

/**
 * BWM: Plasma inyecta i18n()/i18nc() en el contexto de cada plasmoide con el dominio
 * plasma_applet_<id>. Aquí lo hace KI18nContext con el mismo dominio: los catálogos son los
 * originales de plasma-desktop 6.7.5 (po/), compilados por plasma-theme.py en
 * ~/.local/share/locale al entrar en Breeze. Kickoff.qml expone estas funciones a todo el QML.
 */
Singleton {
    KI18nContext {
        id: ctx
        translationDomain: "plasma_applet_org.kde.plasma.kickoff"
    }
    function i18n(...args) { return ctx.i18n(...args); }
    function i18nc(...args) { return ctx.i18nc(...args); }
}
