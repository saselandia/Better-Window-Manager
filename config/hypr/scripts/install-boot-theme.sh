#!/usr/bin/env bash
# ==============================================================================
# Script: install-boot-theme.sh   (ejecutar con sudo)
# Descripción: Instala en el sistema el tema de arranque (Plymouth) y/o el de inicio de
# sesión (SDDM) que bwm_boot.py genera con los colores del tema BWM activo, los mantiene
# al día solo, o deshace Plymouth. Port de omarchy-plymouth-set / omarchy-refresh-sddm
# (Omarchy, MIT).
#
# Uso:
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --auto       # actualizar solo
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth   # pantalla de arranque
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm [--enable-sddm]
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert     # arranque como antes
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --no-auto    # quitar el servicio
# Requisitos (Gentoo): sys-boot/plymouth (--plymouth), x11-misc/sddm (--sddm)
#
# --auto: copia este script a /usr/local/sbin/bwm-boot-theme (de root: el del repo lo puede
#   editar el usuario) y crea bwm-boot-theme.path/.service. bwm_boot.py render se ejecuta
#   tras cada cambio de fondo o de tema y, si el resultado cambia, reescribe
#   ~/.local/state/bwm/boot/.stamp; el servicio (prioridad mínima de CPU y disco) copia los
#   temas que ya estén instalados y, si Plymouth lo está, rehace el initramfs con las mismas
#   comprobaciones que --plymouth. Tras actualizar el script del repo, repite --auto.
#
# Lo que cambia --plymouth en el sistema:
#   /usr/share/plymouth/themes/bwm y el tema por defecto de Plymouth;
#   initramfs rehecho con dracut con los MISMOS argumentos con que se generó, + plymouth
#   (copia en /boot/initramfs-<kver>.img.bwm-backup);
#   "splash" añadido a las líneas "linux" del grub.cfg actual, sin regenerarlo
#   (copia en /boot/grub/grub.cfg.bwm-backup): aquí la línea de arranque (rd.luks..., root=)
#   no está en /etc/default/grub, así que grub-mkconfig la perdería y no arrancaría.
#
# Por qué Plymouth va con comprobaciones (pasó el 2026-10-23): el módulo plymouth de dracut
# mete en el initramfs los drivers DRM de TODAS las GPU. Con la iGPU AMD (amdgpu) dentro,
# ésta arrancaba antes que la NVIDIA, se quedaba los primeros nombres de conector (DP-1...)
# y las reglas de monitor por nombre caían en el monitor equivocado. Además el initramfs pasó
# de 182 MB a 526 MB y GRUB, que lo lee del disco cifrado, tardaba mucho más. Ahora el
# initramfs nuevo conserva exactamente los drivers de GPU del anterior y se descarta si crece
# más de un 50 %; y no se añade "quiet", así que siguen viéndose los mensajes de arranque.
# ==============================================================================
set -euo pipefail

STATE_DIR=/var/lib/bwm-boot-theme      # marcas de lo que instaló este script
SBIN=/usr/local/sbin/bwm-boot-theme
UNIT_DIR=/etc/systemd/system
GRUB_CFG=/boot/grub/grub.cfg
PLY_DIR=/usr/share/plymouth/themes/bwm
SDDM_DIR=/usr/share/sddm/themes/bwm
GPU_DRIVERS='amdgpu|radeon|i915|xe|nouveau|nvidia|nvidia_drm|nvidia_modeset|nvidia_uvm|simpledrm'

usage() { sed -n '9,16p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

PLYMOUTH=false REVERT=false SDDM=false ENABLE_SDDM=false AUTO=false NO_AUTO=false SYNC_USER=""
while (($#)); do
  case "$1" in
    --plymouth) PLYMOUTH=true ;;
    --revert) REVERT=true ;;
    --sddm) SDDM=true ;;
    --enable-sddm) SDDM=true; ENABLE_SDDM=true ;;
    --auto) AUTO=true ;;
    --no-auto) NO_AUTO=true ;;
    --sync) SYNC_USER="${2:?--sync necesita el usuario}"; shift ;;  # lo usa el servicio
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
  shift
done
$PLYMOUTH || $REVERT || $SDDM || $AUTO || $NO_AUTO || [[ -n $SYNC_USER ]] || usage
if $PLYMOUTH && $REVERT; then
  echo "--plymouth y --revert no van juntos." >&2
  exit 1
fi
if [[ $EUID -ne 0 ]]; then
  echo "Ejecuta este script con sudo." >&2
  exit 1
fi

USER_NAME="${SYNC_USER:-${SUDO_USER:-}}"
[[ -n $USER_NAME ]] || { echo "Ejecútalo con sudo desde tu usuario." >&2; exit 1; }
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)
[[ -n $USER_HOME ]] || { echo "No existe el usuario $USER_NAME" >&2; exit 1; }
SRC="$USER_HOME/.local/state/bwm/boot"
mkdir -p "$STATE_DIR"

render() {
  [[ -n $SYNC_USER ]] && return 0   # el servicio usa lo que ya generó el usuario
  sudo -u "$USER_NAME" python3 "$USER_HOME/.config/hypr/scripts/bwm_boot.py" render
}

# Copia los archivos generados por el usuario a un tema del sistema. Sólo archivos normales
# (no enlaces) con nombres y extensiones de tema: lo que viene de $HOME no es de confianza.
# Devuelve 0 si algo cambió.
copy_theme() {
  local from=$1 to=$2 changed=1 f name
  install -d -m 0755 "$to"
  for f in "$from"/*; do
    name=${f##*/}
    [[ -f $f && ! -L $f && $name =~ ^[A-Za-z0-9_.-]+\.(png|script|plymouth|qml|conf|desktop)$ ]] || continue
    (( $(stat -c %s "$f") < 8388608 )) || continue
    if ! cmp -s "$f" "$to/$name"; then
      install -m 0644 "$f" "$to/$name"
      changed=0
    fi
  done
  return $changed
}

# Drivers de GPU que lleva un initramfs (uno por línea, ordenados)
gpu_drivers() {
  lsinitrd "$1" 2>/dev/null | grep -oE "/($GPU_DRIVERS)\.ko(\.[a-z]+)?$" \
    | sed -E 's#^/##; s#\.ko.*##' | sort -u
}

# Rehace el initramfs con Plymouth sin cambiar sus drivers de GPU ni dispararle el tamaño.
# Devuelve 0 si al menos uno quedó instalado.
build_initramfs() {
  local ok=1 kver img orig info args before tmp omit extra pass old_size new_size
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
    extra=""
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
    ok=0
  done
  return $ok
}

# ------------------------------------------------------------------------------
# --sync (servicio): actualizar lo que esté instalado con los colores nuevos
# ------------------------------------------------------------------------------
if [[ -n $SYNC_USER ]]; then
  # Esperar a que dejen de llegar cambios (varios fondos seguidos = un solo initramfs)
  last=""
  while [[ $(cat "$SRC/.stamp" 2>/dev/null) != "$last" ]]; do
    last=$(cat "$SRC/.stamp" 2>/dev/null)
    sleep 20
  done
  if [[ -f $STATE_DIR/sddm ]] && copy_theme "$SRC/sddm" "$SDDM_DIR"; then
    echo "Tema de SDDM actualizado."
  fi
  if [[ -f $STATE_DIR/plymouth ]] && copy_theme "$SRC/plymouth" "$PLY_DIR"; then
    echo "Tema de Plymouth actualizado; rehaciendo el initramfs."
    build_initramfs || echo "El initramfs no se actualizó (ver arriba)." >&2
  fi
  exit 0
fi

# ------------------------------------------------------------------------------
# --revert: initramfs y grub.cfg como antes de --plymouth
# ------------------------------------------------------------------------------
if $REVERT; then
  rm -f "$STATE_DIR/plymouth"
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
  render
  copy_theme "$SRC/plymouth" "$PLY_DIR" || true
  plymouth-set-default-theme bwm
  echo "Tema de Plymouth: $(plymouth-set-default-theme)"
  if build_initramfs; then
    touch "$STATE_DIR/plymouth"
    # "splash" en el grub.cfg actual (sin grub-mkconfig, ver la cabecera). Sin "quiet".
    if [[ -f $GRUB_CFG ]] && grep -qE '^[[:space:]]*linux[[:space:]]' "$GRUB_CFG"; then
      cp -n "$GRUB_CFG" "$GRUB_CFG.bwm-backup"
      sed -i -E '/^[[:space:]]*linux[[:space:]]/{/[[:space:]]splash([[:space:]]|$)/!s/$/ splash/}' "$GRUB_CFG"
      echo "Añadido \"splash\" a $(grep -cE '^[[:space:]]*linux[[:space:]].*splash' "$GRUB_CFG") entradas de $GRUB_CFG"
      echo "  Para deshacerlo: sudo $0 --revert"
    fi
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
  render
  copy_theme "$SRC/sddm" "$SDDM_DIR" || true
  install -d -m 0755 /etc/sddm.conf.d
  printf '[Theme]\nCurrent=bwm\n' >/etc/sddm.conf.d/10-bwm.conf
  touch "$STATE_DIR/sddm"
  echo "Tema de SDDM instalado."
  if $ENABLE_SDDM; then
    systemctl enable sddm.service
    echo "SDDM se usará en el próximo arranque (desactiva el autologin de tty1 si lo tienes)."
  fi
fi

# ------------------------------------------------------------------------------
# --auto / --no-auto
# ------------------------------------------------------------------------------
if $NO_AUTO; then
  systemctl disable --now bwm-boot-theme.path 2>/dev/null || true
  rm -f "$UNIT_DIR/bwm-boot-theme.path" "$UNIT_DIR/bwm-boot-theme.service" "$SBIN"
  systemctl daemon-reload
  echo "Actualización automática desactivada."
fi
if $AUTO; then
  install -m 0755 -o root -g root "$0" "$SBIN"
  render
  cat >"$UNIT_DIR/bwm-boot-theme.path" <<EOF
[Unit]
Description=BWM: tema de arranque e inicio de sesión al cambiar de fondo o de tema

[Path]
PathChanged=$SRC/.stamp
Unit=bwm-boot-theme.service

[Install]
WantedBy=multi-user.target
EOF
  cat >"$UNIT_DIR/bwm-boot-theme.service" <<EOF
[Unit]
Description=BWM: actualizar los temas de Plymouth y SDDM instalados

[Service]
Type=oneshot
ExecStart=$SBIN --sync $USER_NAME
Nice=19
IOSchedulingClass=idle
EOF
  systemctl daemon-reload
  systemctl enable --now bwm-boot-theme.path
  echo "Actualización automática activada: Plymouth y SDDM (los que estén instalados) seguirán"
  echo "los colores del tema y del fondo. Instalados ahora:" \
    "$( [[ -f $STATE_DIR/plymouth ]] && echo Plymouth )" "$( [[ -f $STATE_DIR/sddm ]] && echo SDDM )"
fi

echo "Listo."
