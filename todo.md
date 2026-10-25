## [x] 2. Paneles de la Barra Quickshell portados (COMPLETADO 2026-10-25)
- [x] **Panel de Monitor / Pantallas (`monitor/Panel.qml`):** Brillo por pantalla (`ddcutil` / backlight), Night light (Kelvin slider 3000K-6500K e interruptor), conmutador de resolución, Hz, orientación y escalado.
- [x] **Panel de Energía y Batería (`power/Panel.qml`):** Perfiles de rendimiento (`Performance`, `Balanced`, `Power Saver`), interruptor Stay Awake / Caffeine (`Idle.inhibit` + `omarchy-toggle-idle`), compatible con PC de escritorio y portátiles.
- [x] **Panel de Test de Velocidad (`speedtest/`, `disk-speedtest/` y `SpeedTestOverlay.qml`):** Ventana overlay interactiva para ping, bajada y subida (fast.com) y benchmark de lectura y escritura en disco MB/s.
- [x] **Panel Wi-Fi QR (`wifiqr/Panel.qml`):** Generador instantáneo de código QR para conectar móviles al Wi-Fi actual y botón para revelar contraseña.
- [x] **Panel de Tailscale (`tailscale/Panel.qml`):** Estado de VPN, nodos, Exit Nodes y Taildrop (`omarchy-tailscale-send`). Visibilidad automática según esté instalado.
- [x] **Panel de Agentes IA (`agents/Panel.qml`):** Límites de tokens, saldo de crédito, conmutación de cuentas Claude Code, Codex, Grok y starter prompts.
3. Paleta de Comandos y Menú Completo (omarchy-menu.jsonc)
Nuestro OmarchyMenu.qml actual tiene una lista simplificada y estática en el código.
En Omarchy real:
Es una paleta de comandos interactiva que parsea el archivo de catálogo jerárquico omarchy-menu.jsonc.
Soporta condiciones dinámicas (when), marcas de verificación en vivo (checked, p. ej. ver qué formato de reloj o qué esquinas están activas actualmente con un ✓) y atajos rápidos tipo omarchy menu summon <ruta>.
Agrupa aplicaciones, acciones del sistema, disparadores de estética, ajustes de hardware y ayuda.
4. Herramientas de Extracción de Texto, QR y Grabación
OCR en pantalla (omarchy-capture-text): Seleccionar un área con el ratón (slurp) y extraer el texto directamente al portapapeles mediante tesseract.
Escaneo de códigos QR (omarchy-capture-qr): Seleccionar un código QR de cualquier parte de la pantalla y copiar su enlace o clave de forma silenciosa al portapapeles con zbarimg.
Grabación de pantalla con Webcam (omarchy-capture-screenrecording): Grabación de monitor o región con gpu-screen-recorder / wf-recorder, captura simultánea de audio de sistema y micrófono, y opción de superponer la webcam en una esquina redonda (--with-webcam).
5. Portapapeles y Emojis gráficos en Quickshell
Historial de Portapapeles (shell/plugins/clipboard/Clipboard.qml): Omarchy no depende de un menú externo de Rofi para el portapapeles; tiene una ventana superpuesta en Quickshell con búsqueda en vivo, soporte completo de imágenes pegadas y navegación por teclado.
Buscador de Emojis (shell/plugins/emojis/Emojis.qml): Selector gráfico de emojis y símbolos Unicode (emojis.json) que pega o copia al pulsar Enter.
6. Biblioteca de Temas Estáticos Curados
Actualmente, Retro genera los colores dinámicamente según el fondo de pantalla actual.
Omarchy incluye 23+ temas oficiales calibrados a mano:
Tokyo Night, Catppuccin (Mocha y Latte), Nord, Gruvbox, Kanagawa, Rose Pine, Everforest, Osaka Jade, Solitude, Starship, Lumon, Miasma, Retro-82, etc.
Cada tema viene con su colors.toml, su selección de fondos, su estilo de bloqueo y sus acentos.
Falta un selector en Retro para elegir entre «Paleta dinámica desde el wallpaper» o «Tema estático oficial de Omarchy».
7. Ecosistema de Web Apps y TUIs
Instalador de Web Apps (omarchy-webapp-install): Crea lanzadores de escritorio .desktop para Discord, WhatsApp, GitHub, HEY, Basecamp, Claude, etc., encapsuladas en ventanas web independientes sin barras de navegador.
Lanzadores TUI (omarchy-tui-install): Empaquetado de utilidades de terminal (Lazygit, Herdr, etc.) lanzadas mediante bwm-terminal con geometrías y clases de ventana predeterminadas.
