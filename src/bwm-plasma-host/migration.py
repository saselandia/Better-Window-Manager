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


def native_placement_settings(legacy, edge, output_size):
    """Convert a captured logical output size, never pixels divided by a guessed scale."""
    if edge not in ('top', 'bottom', 'left', 'right'):
        raise ValueError('Borde de panel no reconocido')
    if not isinstance(output_size, (list, tuple)) or len(output_size) != 2 or any(
            type(n) is not int or not 64 <= n <= 8192 for n in output_size):
        raise ValueError('Se requiere tamaño lógico de salida [ancho, alto], 64–8192')
    alignment = legacy.get('alignment', 'center')
    if alignment not in ('start', 'center', 'end'):
        raise ValueError('Alineación de panel no reconocida')
    fraction = legacy.get('length', 1)
    gap = legacy.get('floatingGap', 8)
    for key, value in (('length', fraction), ('floatingGap', gap)):
        try: valid = type(value) in (int, float) and math.isfinite(value)
        except OverflowError: valid = False
        if not valid: raise ValueError(f'{key} debe ser un número finito')
    floating = native_view_settings(legacy)['floating']
    extent = output_size[1 if edge in ('left', 'right') else 0]
    # PanelLogic.geometry's shown/untouched rectangle. The native SVG, rather
    # than a BWM floatingGap key, still controls margins/painting after migration.
    fraction = max(.1, min(1, fraction))
    gap = max(0, min(32, gap)) if floating else 0
    length = math.floor(max(min(160, extent), (extent - 2 * gap) * fraction) + .5)
    return {'alignment': {'start': 1, 'center': 132, 'end': 2}[alignment],
            'panelLengthMode': 0 if fraction == 1 and not floating else 2,
            'minLength': length, 'maxLength': length, 'offset': 0}


def proposal(original_json, monitor_descriptions, output_sizes=None):
    if output_sizes is not None and not isinstance(output_sizes, dict):
        raise ValueError('Los tamaños lógicos deben estar asociados por descripción')
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
        panel = {'outputDescription': description, 'containmentPackage': 'org.kde.panel',
                 'edge': edge, 'nativeViewSettings': copy.deepcopy(view), 'widgets': widgets}
        if output_sizes is not None:
            if not isinstance(output_sizes, dict) or description not in output_sizes:
                raise ValueError('Falta el tamaño lógico de una salida propuesta')
            panel['nativePlacementSettings'] = native_placement_settings(legacy, edge, output_sizes[description])
            panel['outputSize'] = list(output_sizes[description])
        panels.append(panel)
    result = {'version': 1, 'status': 'proposal-only', 'sourceSha256': hashlib.sha256(original_json.encode()).hexdigest(),
              'legacyJson': original_json, 'panels': panels, 'commitAllowed': False}
    if output_sizes is not None:
        if set(output_sizes) != {p['outputDescription'] for p in panels}:
            raise ValueError('Los tamaños deben corresponder exactamente a las salidas propuestas')
        result['placementContractVersion'] = 1
    return result
