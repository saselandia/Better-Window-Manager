# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded startup checks for explicitly requested native preview backends."""
import time


def wait_initial_ack(control,child,*,timeout=5,clock=time.monotonic,pause=time.sleep):
    """Never register a dead child or report its expected missing ack as a file error."""
    deadline=clock()+timeout
    while clock()<deadline:
        code=child.poll()
        if code is not None:raise ValueError(f'El auxiliar terminó antes de confirmar el arranque (código {code}); consulta el motivo mostrado arriba')
        if (control/'ack.json').is_file():return
        pause(min(.01,max(0,deadline-clock())))
    raise TimeoutError('El auxiliar no confirmó el arranque a tiempo')


def task_source_summary(runtime):
    source=runtime.get('taskSource',{}) if isinstance(runtime,dict) else {}
    if not isinstance(source,dict):return None
    count=source.get('windowCount');bound=source.get('boundModels')
    views=source.get('viewModels');filtering=source.get('currentDesktopFilteringViews')
    visible=source.get('visibleWindowRows');launchers=source.get('launcherRows')
    control=runtime.get('nativeDesktopControl',{}) if isinstance(runtime,dict) else {}
    launch=source.get('applicationLauncher',{})
    # Pinned launchers/.desktop Actions would otherwise start inside the host
    # with its temporary roots: require KDE's KIOSK denial before announcing.
    if not isinstance(launch,dict) or launch.get('inProcessLaunchDenied') is not True:return None
    if (source.get('enabled') is True and source.get('snapshotAvailable') is True and
        source.get('suspended') is False and type(count) is int and count>=0 and
        type(bound) is int and bound>0 and type(source.get('taskViewDiagnosticsVersion')) is int and source['taskViewDiagnosticsVersion']==1 and
        type(views) is int and views>0 and type(filtering) is int and filtering>=0 and
        type(visible) is int and visible>=0 and type(launchers) is int and launchers>=0 and
        (filtering==0 or (isinstance(control,dict) and control.get('resumed') is True))):
        return {'windowCount':count,'boundModels':bound,'visibleWindowRows':visible,'launcherRows':launchers}
    return None


def wait_task_source(session,registration,child,*,require_thumbnails=False,timeout=5,clock=time.monotonic,pause=time.sleep):
    """Require a fresh control reply and a valid task snapshot, never just a PID.

    Only aggregate counts leave the preview. A ready source is not a certificate
    of correct icons, physical input, desktop protocols or panel replacement.
    """
    deadline=clock()+timeout;reason='No hay modelos de tareas conectados'
    while clock()<deadline:
        if child.poll() is not None:raise ValueError('El auxiliar terminó antes de conectar las tareas')
        try:
            reply=session.command(registration,'status',timeout=min(1.5,deadline-clock()))
            runtime=reply.get('runtime') if isinstance(reply,dict) else None
            summary=task_source_summary(runtime)
            source=runtime.get('taskSource',{}) if isinstance(runtime,dict) else {}
            thumbnails=source.get('thumbnails',{}) if isinstance(source,dict) else {}
            if summary is not None:
                if not require_thumbnails:return summary
                if isinstance(thumbnails,dict) and thumbnails.get('enabled') is True and thumbnails.get('protocolsReady') is True:return summary
                reason='No están disponibles los protocolos de captura de ventanas de Hyprland'
            if isinstance(source,dict) and source.get('currentDesktopFilteringViews',0):
                reason='Filtro de escritorio activo sin backend nativo; usa --all-desktops'
            launch=source.get('applicationLauncher',{}) if isinstance(source,dict) else {}
            if isinstance(launch,dict) and launch.get('inProcessLaunchDenied') is False:
                reason='El auxiliar podría lanzar aplicaciones con su entorno temporal (política KIOSK ausente)'
            if isinstance(source,dict) and isinstance(source.get('lastError'),str) and source['lastError']:
                reason=source['lastError'][:160]
        except TimeoutError:
            reason='No hay respuesta fresca del auxiliar'
        pause(min(.1,max(0,deadline-clock())))
    raise TimeoutError('No se pudo conectar el modelo de ventanas: '+reason)
