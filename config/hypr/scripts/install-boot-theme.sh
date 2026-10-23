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
#   /usr/share/plymouth/themes/bwm y el tema por defecto de Plymouth;
#   initramfs rehecho con dracut con los MISMOS argumentos con que se generó
#   (copia en /boot/initramfs-<kver>.img.bwm-backup);
#   "quiet splash" añadido a las líneas "linux" del grub.cfg actual, sin regenerarlo
#   (copia en /boot/grub/grub.cfg.bwm-backup): aquí la línea de arranque (rd.luks..., root=)
#   no está en /etc/default/grub, así que grub-mkconfig la perdería y no arrancaría;
#   con --sddm /usr/share/sddm/themes/bwm y /etc/sddm.conf.d/10-bwm.conf
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

# initramfs con Plymouth: rehacerlo con los mismos argumentos de dracut que el actual
# (lsinitrd los guarda), y sólo si el actual lo generó dracut
if command -v dracut >/dev/null && command -v lsinitrd >/dev/null; then
  for kver in $(ls /lib/modules); do
    img="/boot/initramfs-$kver.img"
    [[ -f $img ]] || continue
    info=$(lsinitrd "$img" 2>/dev/null | sed -n '1,/^dracut modules:/p')
    if ! lsinitrd "$img" 2>/dev/null | sed -n '/^dracut modules:/,/^=====/p' | grep -qvE '^(dracut modules:|=+)$'; then
      echo "AVISO: $img no parece generado por dracut: no lo toco. Plymouth no se verá hasta incluirlo." >&2
      continue
    fi
    args=$(printf '%s\n' "$info" | sed -n 's/^Arguments: //p')
    cp -n "$img" "$img.bwm-backup"
    echo "Rehaciendo $img (dracut $args)"
    # shellcheck disable=SC2086 # los argumentos originales van tal cual
    eval dracut --force $args "$img" "$kver"
  done
fi

# "quiet splash" en el grub.cfg actual (sin grub-mkconfig, ver la cabecera)
GRUB_CFG=/boot/grub/grub.cfg
if [[ -f $GRUB_CFG ]] && grep -qE '^[[:space:]]*linux[[:space:]]' "$GRUB_CFG"; then
  cp -n "$GRUB_CFG" "$GRUB_CFG.bwm-backup"
  sed -i -E '/^[[:space:]]*linux[[:space:]]/{/[[:space:]]splash([[:space:]]|$)/!s/$/ quiet splash/}' "$GRUB_CFG"
  echo "Añadido \"quiet splash\" a $(grep -cE '^[[:space:]]*linux[[:space:]].*splash' "$GRUB_CFG") entradas de $GRUB_CFG"
  echo "  (si algún día regeneras grub.cfg con grub-mkconfig, añade también \"quiet splash\" a GRUB_CMDLINE_LINUX_DEFAULT)"
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
