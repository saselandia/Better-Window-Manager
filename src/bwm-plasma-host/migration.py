# SPDX-License-Identifier: GPL-2.0-or-later
"""Non-mutating R4 migration proposal, NOT an appletsrc writer.

Only Corona/Applet may serialize the destination. Unknown legacy values remain archived.
No guessed key translation is committed until the destination applet's schema validates it.
"""
import hashlib
import json
import copy
import math

LEGACY_PACKAGES = {
    'kickoff': 'org.kde.plasma.kickoff', 'pager': 'org.kde.plasma.pager',
    'tasks': 'org.kde.plasma.icontasks', 'tray': 'org.kde.plasma.systemtray',
    'clock': 'org.kde.plasma.digitalclock', 'desktop': 'org.kde.plasma.showdesktop',
}
CONFIG_SECTIONS = {'kickoff': 'kickoff', 'tasks': 'taskManager',
                   'tray': 'systemTray', 'clock': 'clock'}


def native_view_settings(legacy):
    """Only native values with an established contract; never guess screen geometry."""
    thickness = legacy.get('thickness', 44)
    try:
        valid = type(thickness) in (int, float) and math.isfinite(thickness) and thickness == int(thickness)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError('thickness debe ser un número entero finito')
    floating = legacy.get('floating', False)
    if type(floating) is not bool: raise ValueError('floating debe ser booleano')
    style = legacy.get('style', 'translucent')
    if not isinstance(style, str) or style not in ('adaptive', 'opaque', 'translucent', 'floating'):
        raise ValueError('Estilo de opacidad no reconocido')
    # PanelLogic.geometry uses thickness || 44 and clamps to 24..128. The old
    # "floating" style means adaptive opacity plus floating, not another enum.
    return {'thickness': max(24, min(128, thickness or 44)),
            'floating': int(floating or style == 'floating'),
            'panelOpacity': {'adaptive': 0, 'opaque': 1, 'translucent': 2, 'floating': 0}[style]}


def proposal(original_json, monitor_descriptions):
    original = json.loads(original_json)
    if not isinstance(original, dict): raise ValueError('La configuración debe ser un objeto')
    bar = original.get('bar', {})
    if not isinstance(bar, dict): raise ValueError('bar debe ser un objeto')
    legacy = bar.get('plasma', {})
    if not isinstance(legacy, dict): raise ValueError('bar.plasma debe ser un objeto')
    view = native_view_settings(legacy)
    edge = legacy.get('edge', '')
    if edge not in ('', 'top', 'bottom', 'left', 'right'):
        raise ValueError('Borde de panel no reconocido')
    if not edge:
        bottom = bar.get('bottom', False)  # Config.qml/PanelLogic.edge default.
        if type(bottom) is not bool: raise ValueError('bar.bottom debe ser booleano')
        edge = 'bottom' if bottom else 'top'
    panels = []
    for description in dict.fromkeys(monitor_descriptions):
        if not description or description.startswith(('DP-', 'HDMI-')):
            raise ValueError('Se requiere descripción persistente del monitor')
        widgets = []
        for index, name in enumerate(legacy.get('widgets', [])):
            # These sections already store KDE schema names. Pass them through to
            # native validation instead of maintaining a second list of plugin keys.
            section = CONFIG_SECTIONS.get(name)
            config = legacy.get(section, {}) if section else {}
            if not isinstance(config, dict):
                raise ValueError(f'{section} debe ser un objeto de configuración')
            settings = copy.deepcopy(config)
            deferred = []
            if name == 'kickoff' and 'favorites' in settings:
                # New native IDs imply a new KAStats client. The legacy true flag
                # describes BWM's client, not this native instance's client.
                settings['favoritesPortedToKAstats'] = False
                deferred.append('Kickoff must import favorites into its new KAStats client on first render; runtime import not verified')
            if name == 'clock':
                if 'showDate' in legacy:
                    if type(legacy['showDate']) is not bool: raise ValueError('showDate debe ser booleano')
                    settings['showDate'] = legacy['showDate']
                if 'showSeconds' in legacy:
                    if type(legacy['showSeconds']) is not bool: raise ValueError('showSeconds debe ser booleano')
                    # The existing DigitalClock adapter maps false to ToolTip=1, true to Always=2.
                    settings['showSeconds'] = 2 if legacy['showSeconds'] else 1
            widgets.append({'legacyIndex': index, 'legacyName': name, 'nativeSettings': settings,
                            'deferredRuntime': deferred,
                            'package': LEGACY_PACKAGES.get(name),
                            'status': 'resolve-package-and-validate-schema' if name in LEGACY_PACKAGES else 'unmapped-preserve'})
        panels.append({'outputDescription': description, 'containmentPackage': 'org.kde.panel',
                       'edge': edge, 'nativeViewSettings': copy.deepcopy(view), 'widgets': widgets})
    return {'version': 1, 'status': 'proposal-only', 'sourceSha256': hashlib.sha256(original_json.encode()).hexdigest(),
            'legacyJson': original_json, 'panels': panels, 'commitAllowed': False}
