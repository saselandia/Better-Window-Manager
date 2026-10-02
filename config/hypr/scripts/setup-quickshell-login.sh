#!/usr/bin/env bash
# ==============================================================================
# Script: setup-quickshell-login.sh
# Descripción: Configura el inicio automático sin terminal TTY de texto,
#              para que el equipo arranque directamente en la pantalla de
#              login gráfico de Quickshell (Material You).
# ==============================================================================

set -euo pipefail

USER_NAME="${1:-sasel}"

echo "Configurando arranque gráfico con inicio de sesión Quickshell para el usuario: $USER_NAME"

# 1. Crear el override de systemd para agetty en tty1
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d

sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER_NAME --noclear %I \$TERM
Type=idle
EOF

echo "✓ Archivo /etc/systemd/system/getty@tty1.service.d/autologin.conf creado."

# 2. Recargar configuración de systemd
sudo systemctl daemon-reload
echo "✓ Systemd recargado."

# 3. Asegurar que Quickshell tiene activado 'launchOnStartup' en su configuración
python3 -c "
import json, os
cfg_path = os.path.expanduser('~/.config/illogical-impulse/config.json')
if os.path.exists(cfg_path):
    with open(cfg_path, 'r') as f:
        data = json.load(f)
    if 'lock' in data:
        data['lock']['launchOnStartup'] = True
        with open(cfg_path, 'w') as f:
            json.dump(data, f, indent=2)
        print('✓ Quickshell lock.launchOnStartup activado en config.json.')
"

echo ""
echo "================================================================="
echo " ¡LISTO! Al encender el equipo:"
echo " 1. Ya NO aparecerá el login de texto de la TTY."
echo " 2. El sistema iniciará directamente la pantalla de login gráfico"
echo "    de Quickshell con tu fondo, reloj, avatar y contraseña."
echo " 3. Introduces tu contraseña y entrarás directo a tu escritorio."
echo "================================================================="
