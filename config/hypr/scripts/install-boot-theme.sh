#!/usr/bin/env bash
# ==============================================================================
# Script: install-boot-theme.sh   (ejecutar con sudo)
# Descripción: Instala en el sistema el tema de arranque (Plymouth) y, opcionalmente,
# el de inicio de sesión (SDDM) que bwm_boot.py genera con los colores del tema BWM
# activo. Port de omarchy-plymouth-set / omarchy-refresh-sddm (Omarchy, MIT).
#
# Uso:
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh            # Plymouth
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm     # + tema de SDDM
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm --enable-sddm
#                                                                # + usar SDDM al iniciar
# Requisitos (Gentoo): sys-boot/plymouth (y x11-misc/sddm para --sddm)
# Lo que cambia en el sistema:
#   /usr/share/plymouth/themes/bwm, tema por defecto de Plymouth, initramfs (dracut),
#   "quiet splash" en GRUB_CMDLINE_LINUX_DEFAULT (copia en /etc/default/grub.bwm-backup)
#   y grub.cfg; con --sddm /usr/share/sddm/themes/bwm y /etc/sddm.conf.d/10-bwm.conf
# ==============================================================================
set -euo pipefail

SDDM=false
ENABLE_SDDM=false
for arg in "$@"; do
  case "$arg" in
    --sddm) SDDM=true ;;
    --enable-sddm) SDDM=true; ENABLE_SDDM=true ;;
    *) echo "Opción desconocida: $arg" >&2; exit 1 ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Ejecuta este script con sudo." >&2
  exit 1
fi
USER_NAME="${SUDO_USER:?Ejecútalo con sudo desde tu usuario}"
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)
SRC="$USER_HOME/.local/state/bwm/boot"

# 1. Generar el tema con los colores actuales (como el usuario, no como root)
sudo -u "$USER_NAME" python3 "$USER_HOME/.config/hypr/scripts/bwm_boot.py" render

# 2. Plymouth
if ! command -v plymouth-set-default-theme >/dev/null; then
  echo "Falta Plymouth: emerge --ask sys-boot/plymouth" >&2
  exit 1
fi
install -d -m 0755 /usr/share/plymouth/themes/bwm
install -m 0644 "$SRC"/plymouth/* /usr/share/plymouth/themes/bwm/
plymouth-set-default-theme bwm
echo "Tema de Plymouth: $(plymouth-set-default-theme)"

# initramfs con Plymouth (dracut añade el módulo si Plymouth está instalado)
if command -v dracut >/dev/null; then
  for kver in $(ls /lib/modules); do
    [[ -f /boot/initramfs-$kver.img ]] && dracut --force "/boot/initramfs-$kver.img" "$kver"
  done
fi

# Línea de comandos del kernel: "quiet splash" para ver el tema en lugar del texto
if [[ -f /etc/default/grub ]] && ! grep -qE '^GRUB_CMDLINE_LINUX_DEFAULT=.*\bsplash\b' /etc/default/grub; then
  cp -n /etc/default/grub /etc/default/grub.bwm-backup
  if grep -q '^GRUB_CMDLINE_LINUX_DEFAULT=' /etc/default/grub; then
    sed -i -E 's/^GRUB_CMDLINE_LINUX_DEFAULT="([^"]*)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 quiet splash"/' /etc/default/grub
  else
    echo 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"' >>/etc/default/grub
  fi
  grub-mkconfig -o /boot/grub/grub.cfg
fi

# 3. SDDM (opcional)
if $SDDM; then
  if ! command -v sddm >/dev/null; then
    echo "Falta SDDM: emerge --ask x11-misc/sddm" >&2
    exit 1
  fi
  install -d -m 0755 /usr/share/sddm/themes/bwm /etc/sddm.conf.d
  install -m 0644 "$SRC"/sddm/* /usr/share/sddm/themes/bwm/
  printf '[Theme]\nCurrent=bwm\n' >/etc/sddm.conf.d/10-bwm.conf
  echo "Tema de SDDM instalado."
  if $ENABLE_SDDM; then
    systemctl enable sddm.service
    echo "SDDM se usará en el próximo arranque."
  fi
fi

echo "Listo. Reinicia para ver el nuevo arranque."
