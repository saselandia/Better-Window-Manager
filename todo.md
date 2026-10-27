# BWM — funciones portadas y pendientes

Revisado el 2026-10-27. Estado actual y detalle técnico en `BWM_CONTEXT.md` §2;
las reglas para asistentes están en `AGENTS.md` y `CLAUDE.md`.

## Completado

- [x] Paneles Retro de pantallas, energía, audio, red, Bluetooth, pruebas de velocidad,
  Wi-Fi QR, Tailscale y agentes IA (`modules/ii/bar/omarchy/`).
- [x] Menú / paleta de comandos jerárquico (`bwm-menu.jsonc`): condiciones `when`,
  marcas `checked`, proveedores y extensiones del usuario (`BWM_CONTEXT.md` §3.24).
  Quedan acciones concretas sin portar, enumeradas abajo.
- [x] OCR, lectura de QR y grabación de pantalla con audio y webcam desde el menú
  Retro, con comprobación de dependencias de Gentoo (§3.24).
- [x] Portapapeles y emojis gráficos: búsqueda, imágenes, previsualización y pegado
  en Wayland con los dispatchers Lua de Hyprland (§3.26).
- [x] 23 temas Retro, paleta dinámica, carrusel 3D, Alt+R y selectores en menú/Ajustes
  (§3.28–30). Los temas estáticos conservan la paleta al cambiar el fondo.
- [x] Cuadrícula Apps (Super+Espacio), dock opcional apagado por defecto, OSD,
  polkit, recordatorios, widgets de actualizaciones y selector de idioma del shell
  (§3.38–39). Dock: ajustes mediante `omarchy-dock`/`dock.json`.
- [x] Plantillas de apps de Omarchy, GTK 3 en vivo, Qt/Flatpak con paleta y
  reinicios de apps conservando sus ventanas (§3.34–36).
- [x] Stremio Web con CSS en vivo opcional; Steam con Adwaita-for-Steam y barra
  Retro usando el fondo base (§3.40–42; alcance en `docs/STREMIO_THEMING.md`).

- [x] Ajustes → Temas y Plugins en páginas separadas: miniaturas/paletas, activación
  y posición, filtros, catálogos con paginación e instalación por Git (§3.45–46).
- [x] About propio de BWM, distro autodetectada y enlaces del proyecto; Advanced
  retirado de ambas apps de Ajustes (§3.46).

## Pendiente de Omarchy

- [ ] Completar el menú Estilo: barra opaca/transparente/glassy, ocultarla,
  reloj de 12/24 h y fecha, porcentaje de batería, esquinas, huecos,
  transparencia, animaciones y branding del salvapantallas. Varias piezas ya
  existen como ajustes o scripts; falta reunir las acciones y sus estados.
- [ ] Layout por workspace: dwindle, scrolling o flotante y ciclo con Super+L.
- [ ] Atajos de ventanas pendientes: Super+Ctrl+F, Super+Alt+F, Super+O,
  scratchpad Super+S, consola Quake Super+` y copiar/pegar universal.
- [ ] Integrar posición y autoocultar del dock en el menú Estilo; la configuración
  del dock por script ya existe.
- [ ] Install / Remove adaptado a emerge y Flatpak: navegadores, editores,
  juegos, IA, servicios, fuentes y terminales.
- [ ] Instalador de Web Apps y lanzadores TUI (`omarchy-webapp-install`,
  `omarchy-tui-install`) con terminal predeterminada de BWM.
- [ ] Compartir portapapeles, archivos o carpetas entre equipos con LocalSend.
- [ ] Setup: DNS, idioma, teclado, seguridad (huella/FIDO2) y apps de agentes.
- [ ] Firmware, hora/zona horaria, contraseña e interruptores rápidos de bloqueo,
  salvapantallas, notificaciones y captura de cuelgues desde los menús.

## Mantenimiento de BWM

- [ ] Completar el actualizador Gentoo: sincronización, noticias con sudo,
  configuraciones y bibliotecas preservadas. `omarchy-update` ya ejecuta
  Flatpak y `emerge @world`, pero no esos pasos. Sustituir el `apps.update`
  heredado con `pacman` en Default/Plasma (§2.7).
- [ ] Recarga de paleta Qt en apps abiertas: qt6ct no repinta de forma fiable.
- [ ] Tema Chromium: la plantilla se genera, falta aplicar su política root.
- [ ] Entorno de pruebas con Hyprland anidado, usuario separado y rama `dev`;
  sustituir antes las rutas fijas `/home/sasel` por rutas configurables.

Prioridad propuesta: menú Estilo, layouts y atajos de ventanas; después,
Install/Remove y mantenimiento del actualizador. Actualizar esta lista cuando
se complete una pieza para que no vuelva a aparecer como pendiente.
