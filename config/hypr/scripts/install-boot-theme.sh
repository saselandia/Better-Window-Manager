#!/usr/bin/env bash
# ==============================================================================
# Script: install-boot-theme.sh   (ejecutar con sudo)
# Descripción: Instala en el sistema el tema de arranque (Plymouth) y/o el de inicio de
# sesión (SDDM) que bwm_boot.py genera con los colores del tema BWM activo, o deshace
# la instalación de Plymouth. Port de omarchy-plymouth-set / omarchy-refresh-sddm
# (Omarchy, MIT).
#
# Uso:
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert     # arranque como antes
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth   # pantalla de arranque
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm [--enable-sddm]
#                                                                  # tema de SDDM (+ usarlo)
# Requisitos (Gentoo): sys-boot/plymouth (--plymouth), x11-misc/sddm (--sddm)
#
# Lo que cambia --plymouth en el sistema:
#   /usr/share/plymouth/themes/bwm y el tema por defecto de Plymouth;
#   initramfs rehecho con dracut con los MISMOS argumentos con que se generó, + plymouth
#   (copia en /boot/initramfs-<kver>.img.bwm-backup);
#   "splash" añadido a las líneas "linux" del grub.cfg actual, sin regenerarlo
#   (copia en /boot/grub/grub.cfg.bwm-backup): aquí la línea de arranque (rd.luks..., root=)
#   no está en /etc/default/grub, así que grub-mkconfig la perdería y no arrancaría.
#
# Por qué es opcional y va con comprobaciones (pasó el 2026-10-23): el módulo plymouth de
# dracut mete en el initramfs los drivers DRM de TODAS las GPU. Con la iGPU AMD (amdgpu)
# dentro, ésta arrancaba antes que la NVIDIA, se quedaba los primeros nombres de conector
# (DP-1...) y las reglas de monitor por nombre caían en el monitor equivocado (monitores
# superpuestos, resolución mala). Además el initramfs pasó de 182 MB a 526 MB y GRUB, que lo
# lee del disco cifrado, tardaba mucho más. Ahora el initramfs nuevo conserva exactamente los
# drivers de GPU del anterior y se descarta si crece demasiado; y no se añade "quiet", así
# que siguen viéndose los mensajes de arranque al pulsar Esc.
# ==============================================================================
set -euo pipefail

PLYMOUTH=false
REVERT=false
SDDM=false
ENABLE_SDDM=false
for arg in "$@"; do
  case "$arg" in
    --plymouth) PLYMOUTH=true ;;
    --revert) REVERT=true ;;
    --sddm) SDDM=true ;;
    --enable-sddm) SDDM=true; ENABLE_SDDM=true ;;
    *) echo "Opción desconocida: $arg" >&2; exit 1 ;;
  esac
done
if ! $PLYMOUTH && ! $REVERT && ! $SDDM; then
  sed -n '10,15p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi
if $PLYMOUTH && $REVERT; then
  echo "--plymouth y --revert no van juntos." >&2
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "Ejecuta este script con sudo." >&2
  exit 1
fi
USER_NAME="${SUDO_USER:?Ejecútalo con sudo desde tu usuario}"
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)
SRC="$USER_HOME/.local/state/bwm/boot"
GRUB_CFG=/boot/grub/grub.cfg
GPU_DRIVERS='amdgpu|radeon|i915|xe|nouveau|nvidia|nvidia_drm|nvidia_modeset|nvidia_uvm|simpledrm'

# Drivers de GPU que lleva un initramfs (uno por línea, ordenados)
gpu_drivers() {
  lsinitrd "$1" 2>/dev/null | grep -oE "/($GPU_DRIVERS)\.ko(\.[a-z]+)?$" \
    | sed -E 's#^/##; s#\.ko.*##' | sort -u
}

# ------------------------------------------------------------------------------
# --revert: initramfs y grub.cfg como antes de --plymouth
# ------------------------------------------------------------------------------
if $REVERT; then
  for backup in /boot/initramfs-*.img.bwm-backup; do
    [[ -f $backup ]] || continue
    img="${backup%.bwm-backup}"
    cp "$backup" "$img.bwm-new" && mv "$img.bwm-new" "$img" && rm -f "$backup"
    echo "Restaurado $img ($(du -h "$img" | cut -f1))"
  done
  if [[ -f $GRUB_CFG ]]; then
    # Sólo se quita lo que añadió este script (al final de las líneas linux)
    sed -i -E '/^[[:space:]]*linux[[:space:]]/{s/ quiet splash$//; s/ splash$//}' "$GRUB_CFG"
    rm -f "$GRUB_CFG.bwm-backup"
    echo "Quitado \"splash\" de $GRUB_CFG ($(grep -cE '^[[:space:]]*linux[[:space:]].*splash' "$GRUB_CFG" || true) entradas lo siguen teniendo)"
  fi
  echo "Arranque restaurado. Reinicia para comprobarlo."
fi

# ------------------------------------------------------------------------------
# --plymouth
# ------------------------------------------------------------------------------
if $PLYMOUTH; then
  if ! command -v plymouth-set-default-theme >/dev/null; then
    echo "Falta Plymouth: emerge --ask sys-boot/plymouth" >&2
    exit 1
  fi
  if ! command -v dracut >/dev/null || ! command -v lsinitrd >/dev/null; then
    echo "Hace falta dracut para incluir Plymouth en el initramfs." >&2
    exit 1
  fi
  sudo -u "$USER_NAME" python3 "$USER_HOME/.config/hypr/scripts/bwm_boot.py" render
  install -d -m 0755 /usr/share/plymouth/themes/bwm
  install -m 0644 "$SRC"/plymouth/* /usr/share/plymouth/themes/bwm/
  plymouth-set-default-theme bwm
  echo "Tema de Plymouth: $(plymouth-set-default-theme)"

  for kver in $(ls /lib/modules); do
    img="/boot/initramfs-$kver.img"
    [[ -f $img ]] || continue
    orig="$img"
    [[ -f $img.bwm-backup ]] && orig="$img.bwm-backup"   # comparar siempre con el original
    info=$(lsinitrd "$orig" 2>/dev/null | sed -n '1,/^dracut modules:/p')
    if ! lsinitrd "$orig" 2>/dev/null | sed -n '/^dracut modules:/,/^=====/p' | grep -qvE '^(dracut modules:|=+)$'; then
      echo "AVISO: $img no parece generado por dracut: no lo toco." >&2
      continue
    fi
    args=$(printf '%s\n' "$info" | sed -n 's/^Arguments: //p')
    before=$(gpu_drivers "$orig")
    tmp="$img.bwm-tmp"

    # Los drivers de GPU que no llevaba el original se dejan fuera (el orden de arranque
    # de las GPU, y con él los nombres de los conectores, no cambia)
    omit=""
    for pass in 1 2; do
      echo "Generando initramfs para $kver (dracut $args --add plymouth${omit:+ --omit-drivers \"$omit\"})"
      # shellcheck disable=SC2086 # los argumentos originales van tal cual
      eval dracut --force --quiet $args --add plymouth ${omit:+--omit-drivers \"\$omit\"} "$tmp" "$kver"
      extra=$(comm -13 <(printf '%s\n' "$before") <(gpu_drivers "$tmp") | tr '\n' ' ')
      [[ -z ${extra// } ]] && break
      omit="$omit $extra"
    done
    if [[ -n ${extra// } ]]; then
      echo "ERROR: el initramfs nuevo seguía añadiendo drivers de GPU ($extra): descartado." >&2
      rm -f "$tmp"; continue
    fi
    old_size=$(stat -c %s "$orig"); new_size=$(stat -c %s "$tmp")
    if (( new_size > old_size * 3 / 2 )); then
      echo "ERROR: el initramfs nuevo ocupa $((new_size >> 20)) MB frente a $((old_size >> 20)) MB (GRUB tardaría mucho más en leerlo del disco cifrado): descartado." >&2
      rm -f "$tmp"; continue
    fi
    cp -n "$img" "$img.bwm-backup"
    mv "$tmp" "$img"
    echo "Initramfs $img: $((old_size >> 20)) MB -> $((new_size >> 20)) MB, mismos drivers de GPU"
    PLYMOUTH_OK=true
  done

  # "splash" en el grub.cfg actual (sin grub-mkconfig, ver la cabecera). Sin "quiet".
  if [[ ${PLYMOUTH_OK:-false} == true && -f $GRUB_CFG ]] && grep -qE '^[[:space:]]*linux[[:space:]]' "$GRUB_CFG"; then
    cp -n "$GRUB_CFG" "$GRUB_CFG.bwm-backup"
    sed -i -E '/^[[:space:]]*linux[[:space:]]/{/[[:space:]]splash([[:space:]]|$)/!s/$/ splash/}' "$GRUB_CFG"
    echo "Añadido \"splash\" a $(grep -cE '^[[:space:]]*linux[[:space:]].*splash' "$GRUB_CFG") entradas de $GRUB_CFG"
    echo "  Para deshacerlo: sudo $0 --revert"
  fi
fi

# ------------------------------------------------------------------------------
# --sddm
# ------------------------------------------------------------------------------
if $SDDM; then
  if ! command -v sddm >/dev/null; then
    echo "Falta SDDM: emerge --ask x11-misc/sddm" >&2
    exit 1
  fi
  sudo -u "$USER_NAME" python3 "$USER_HOME/.config/hypr/scripts/bwm_boot.py" render
  install -d -m 0755 /usr/share/sddm/themes/bwm /etc/sddm.conf.d
  install -m 0644 "$SRC"/sddm/* /usr/share/sddm/themes/bwm/
  printf '[Theme]\nCurrent=bwm\n' >/etc/sddm.conf.d/10-bwm.conf
  echo "Tema de SDDM instalado."
  if $ENABLE_SDDM; then
    systemctl enable sddm.service
    echo "SDDM se usará en el próximo arranque (desactiva el autologin de tty1 si lo tienes)."
  fi
fi

echo "Listo."
