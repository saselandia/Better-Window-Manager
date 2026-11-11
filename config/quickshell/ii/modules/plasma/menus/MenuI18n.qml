/*
    SPDX-FileCopyrightText: 2026 BWM
    SPDX-License-Identifier: GPL-2.0-or-later
*/
// BWM: traducciones de los menús portados (F9). Un solo catálogo propio, bwm_plasma_menus, con las
// cadenas originales (y sus contextos) sacadas de kwin, plasma-desktop, plasma-workspace y libplasma
// 6.7.5 (po/, ver README.md). No reutiliza los dominios de KDE: un catálogo recortado con su nombre
// taparía al completo si estuviera instalado.
pragma Singleton

import QtQuick
import Quickshell
import org.kde.ki18n

Singleton {
    KI18nContext {
        id: ctx
        translationDomain: "bwm_plasma_menus"
    }
    function i18n(...args) { return ctx.i18n(...args); }
    function i18nc(...args) { return ctx.i18nc(...args); }
}
