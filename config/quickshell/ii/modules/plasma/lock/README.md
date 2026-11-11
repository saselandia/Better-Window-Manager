# Bloqueo de Plasma (F12)

En las fuentes 6.7.5 comprobadas, el paquete Breeze de plasma-workspace ya no contiene
contents/lockscreen. `Greeter.qml` porta `kscreenlocker v6.7.5/greeter/fallbacktheme/Greeter.qml`
(GPL-2.0-or-later; Martin Gräßlin y Nate Graham). `LockSurface.qml` usa los componentes reales
Breeze Clock, SessionManagementScreen, UserList/avatar y ActionButton instalados con Plasma.
El wallpaper y la autenticación siguen en BWM; no se utiliza kscreenlocker_greet para bloquear.

Cambios BWM en Greeter: PasswordSync se conecta a currentText de LockContext, autenticación y
mensajes mediante Authenticator, sin cambiar de usuario ni Qt.quit() al terminar. El anfitrión
Breeze proporciona avatar/usuario y su botón de desbloqueo, por lo que oculta las versiones del
formulario de reserva. El foco no se fuerza en cada letra. PAM, huella, limpieza de contraseña,
inhibidores y desbloqueo de las superficies siguen en el LockContext/LockScreen comunes.

El tema global puede proporcionar contents/lockscreen/LockScreenUi.qml o main.qml. LockTheme
lo carga con ThemeHost en un motor QML separado, con el contexto de KScreenLocker:
authenticator, nombre/imagen de usuario y versión del interfaz. El adaptador admite tryUnlock(text)
y startAuthenticating()/respond(text), estado busy, fallos y huella; no expone un método que
permita desbloquear sin PAM. No se entrega el LockContext completo al tema. Qt.quit() queda
interceptado y no termina el shell ni desbloquea la sesión. Un error de carga conserva el
formulario nativo de reserva. Las APIs privadas adicionales de KScreenLocker pueden no existir.

Pruebas: sólo contextos simulados, ninguna WlSessionLock/PamContext real. No se certifica PAM,
huella ni recuperación de un bloqueo real por haber cargado la vista en una ventana de prueba.

Fuentes: https://invent.kde.org/plasma/kscreenlocker/-/tree/v6.7.5/greeter/fallbacktheme
Componentes: plasma-workspace v6.7.5/lookandfeel/components (licencias de sus paquetes instalados).
