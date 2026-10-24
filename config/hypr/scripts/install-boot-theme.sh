#!/usr/bin/env bash
# ==============================================================================
# Script: install-boot-theme.sh   (ejecutar con sudo)
# Descripción: Instala en el sistema el tema de arranque (Plymouth) y/o el de inicio de
# sesión (SDDM) que bwm_boot.py genera con los colores del tema BWM activo, los mantiene
# al día solo, o deshace Plymouth. Port de omarchy-plymouth-set / omarchy-refresh-sddm
# (Omarchy, MIT).
#
# Uso:
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --all        # SDDM + actualizar solo
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --plymouth   # pantalla de arranque
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --sddm [--enable-sddm] [--autologin]
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --auto       # actualizar solo
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --revert     # arranque sin Plymouth
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --disable-sddm  # volver al autologin
#   sudo ~/.config/hypr/scripts/install-boot-theme.sh --no-auto    # quitar el servicio
# Requisitos: plymouth + dracut (--plymouth), sddm con Qt 6 (--sddm)
#
# SDDM como en Omarchy (etc/sddm.conf.d y default/sddm/hyprland.lua de Omarchy): el tema
# "omarchy" (aquí "bwm", mismo Main.qml) dentro de un Hyprland mínimo (DisplayServer=wayland,
# sin logo ni animaciones, con la distribución de teclado y los monitores del usuario),
# recordando último usuario y sesión (sesión por defecto hyprland.desktop).
# Inicio de sesión según el tema BWM activo: en Retro se entra con contraseña en SDDM (como
# Omarchy) y Quickshell no vuelve a bloquear; en Default y Plasma SDDM entra solo y el
# bloqueo del propio tema (Quickshell, lock.launchOnStartup) hace de inicio de sesión. Al
# cambiar de tema el servicio de --auto cambia el autologin de SDDM para el próximo arranque.
# --enable-sddm lo activa al arrancar y aparca el autologin de getty en tty1 (si lo había);
# --autologin: SDDM entra siempre solo, sea cual sea el tema (sin --autologin vuelve al modo
# por tema). --disable-sddm lo desactiva y devuelve el autologin de getty.
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
GREETER_LUA=/usr/share/sddm/bwm-hyprland.lua
SDDM_CONF_D=/etc/sddm.conf.d
GETTY_AUTOLOGIN=/etc/systemd/system/getty@tty1.service.d/autologin.conf
GPU_DRIVERS='amdgpu|radeon|i915|xe|nouveau|nvidia|nvidia_drm|nvidia_modeset|nvidia_uvm|simpledrm'

usage() { sed -n '9,18p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

PLYMOUTH=false REVERT=false SDDM=false ENABLE_SDDM=false AUTOLOGIN=false DISABLE_SDDM=false
AUTO=false NO_AUTO=false SYNC_USER=""
while (($#)); do
  case "$1" in
    --plymouth) PLYMOUTH=true ;;
    --revert) REVERT=true ;;
    --sddm) SDDM=true ;;
    --enable-sddm) SDDM=true; ENABLE_SDDM=true ;;
    --autologin) SDDM=true; AUTOLOGIN=true ;;
    --disable-sddm) DISABLE_SDDM=true ;;
    --all) SDDM=true; ENABLE_SDDM=true; AUTO=true ;;
    --auto) AUTO=true ;;
    --no-auto) NO_AUTO=true ;;
    --sync) SYNC_USER="${2:?--sync necesita el usuario}"; shift ;;  # lo usa el servicio
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
  shift
done
$PLYMOUTH || $REVERT || $SDDM || $DISABLE_SDDM || $AUTO || $NO_AUTO || [[ -n $SYNC_USER ]] || usage
if $SDDM && $DISABLE_SDDM; then
  echo "--sddm y --disable-sddm no van juntos." >&2
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

# Escribe un archivo de root de forma atómica (contenido por stdin)
write_root_file() {
  local dest=$1 mode=${2:-0644} tmp
  install -d -m 0755 "${dest%/*}"
  tmp=$(mktemp "${dest%/*}/.${dest##*/}.bwm-new.XXXXXX")
  cat >"$tmp"
  chmod "$mode" "$tmp"
  mv -fT "$tmp" "$dest"
}

# Config de Hyprland del saludo de SDDM (como default/sddm/hyprland.lua de Omarchy) con el
# teclado y los monitores del usuario. greeter.conf viene de $HOME: cada campo se valida y
# el Lua lo escribe este script, nunca se copia (lo ejecuta Hyprland como usuario sddm).
write_greeter_config() {
  local conf="$SRC/sddm/greeter.conf" key value kb_layout=us kb_variant="" kb_options=""
  local monitors="" out mode pos scale
  if [[ -f $conf && ! -L $conf ]]; then
    while IFS='=' read -r key value; do
      case "$key" in
        kb_layout|kb_variant|kb_options)
          [[ $value =~ ^[A-Za-z0-9_,:()+-]*$ ]] || continue
          printf -v "$key" '%s' "$value" ;;
        monitor)
          IFS='|' read -r out mode pos scale <<<"$value"
          [[ $out =~ ^desc:[A-Za-z0-9\ ._,()+-]+$ && $mode =~ ^[0-9]+x[0-9]+(@[0-9.]+)?$ &&
             $pos =~ ^-?[0-9]+x-?[0-9]+$ && $scale =~ ^[0-9]+(\.[0-9]+)?$ ]] || continue
          monitors+="hl.monitor({ output = \"$out\", mode = \"$mode\", position = \"$pos\", scale = \"$scale\" })"$'\n' ;;
      esac
    done <"$conf"
  fi
  write_root_file "$GREETER_LUA" <<EOF
-- Generado por install-boot-theme.sh (BWM). Hyprland mínimo para el saludo de SDDM, como
-- default/sddm/hyprland.lua de Omarchy (MIT). SDDM arranca el saludo cuando está listo.
${monitors}hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "1" })

hl.config({
  input = {
    kb_layout = "$kb_layout",
    kb_variant = "$kb_variant",
    kb_options = "$kb_options",
  },
  misc = {
    disable_hyprland_logo = true,
    disable_splash_rendering = true,
    background_color = "rgb(000000)",
    force_default_wallpaper = 0,
  },
  animations = {
    enabled = false,
  },
})
EOF
}

# Autologin de SDDM según el tema (ver la cabecera). El tema viene de greeter.conf.
apply_login_mode() {
  local theme
  theme=$(sed -n 's/^theme=\([a-z]*\)$/\1/p' "$SRC/sddm/greeter.conf" 2>/dev/null | head -n1)
  if [[ -f $STATE_DIR/autologin-always ]] || [[ $theme == default || $theme == plasma ]]; then
    write_root_file "$SDDM_CONF_D/autologin.conf" <<<$'[Autologin]\nUser='"$USER_NAME"$'\nSession=hyprland.desktop'
  elif [[ $theme == retro ]]; then
    rm -f "$SDDM_CONF_D/autologin.conf"
  fi
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
  if [[ -f $STATE_DIR/sddm ]]; then
    if copy_theme "$SRC/sddm" "$SDDM_DIR"; then echo "Tema de SDDM actualizado."; fi
    write_greeter_config
    apply_login_mode
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
    echo "Falta SDDM: emerge --ask x11-misc/sddm  |  pacman -S sddm  |  dnf install sddm" >&2
    exit 1
  fi
  if ! command -v start-hyprland >/dev/null; then
    echo "Falta start-hyprland (viene con Hyprland): el saludo de SDDM corre en Hyprland." >&2
    exit 1
  fi
  render
  copy_theme "$SRC/sddm" "$SDDM_DIR" || true
  write_greeter_config
  # Lo mismo que etc/sddm.conf.d de Omarchy (10-theme, 10-wayland, 99-omarchy-login)
  write_root_file "$SDDM_CONF_D/10-bwm-theme.conf" <<<$'[Theme]\nCurrent=bwm'
  write_root_file "$SDDM_CONF_D/10-bwm-wayland.conf" <<EOF
[General]
DisplayServer=wayland

[Wayland]
CompositorCommand=start-hyprland -- --config $GREETER_LUA
EOF
  write_root_file "$SDDM_CONF_D/99-bwm-login.conf" <<<$'[Users]\nRememberLastUser=true\nRememberLastSession=true'
  rm -f "$SDDM_CONF_D/10-bwm.conf"   # nombre anterior
  # Último usuario y sesión: el tema entra con ellos (el Main.qml de Omarchy no tiene selector)
  if [[ -f /usr/share/wayland-sessions/hyprland.desktop ]]; then
    install -d -m 0755 /var/lib/sddm
    write_root_file /var/lib/sddm/state.conf <<<$'[Last]\nSession=/usr/share/wayland-sessions/hyprland.desktop\nUser='"$USER_NAME"
    chown sddm:sddm /var/lib/sddm /var/lib/sddm/state.conf 2>/dev/null || true
  fi
  if $AUTOLOGIN; then
    touch "$STATE_DIR/autologin-always"
  else
    rm -f "$STATE_DIR/autologin-always"
  fi
  apply_login_mode
  touch "$STATE_DIR/sddm"
  echo "Tema de SDDM instalado (saludo en Hyprland, con tu teclado y tus monitores)."
  if $ENABLE_SDDM; then
    if [[ -f $GETTY_AUTOLOGIN ]]; then
      mv "$GETTY_AUTOLOGIN" "$STATE_DIR/getty-autologin.conf"
      echo "Autologin de getty en tty1 aparcado en $STATE_DIR (--disable-sddm lo devuelve)."
    fi
    systemctl daemon-reload
    systemctl enable -f sddm.service
    echo "SDDM se usará en el próximo arranque."
    echo "  Si algo falla: Ctrl+Alt+F2, entra con tu usuario y ejecuta"
    echo "  sudo ~/.config/hypr/scripts/install-boot-theme.sh --disable-sddm"
  fi
fi

if $DISABLE_SDDM; then
  systemctl disable sddm.service 2>/dev/null || true
  if [[ -f $STATE_DIR/getty-autologin.conf ]]; then
    install -d -m 0755 "${GETTY_AUTOLOGIN%/*}"
    mv "$STATE_DIR/getty-autologin.conf" "$GETTY_AUTOLOGIN"
    echo "Autologin de getty en tty1 restaurado."
  fi
  systemctl daemon-reload
  echo "SDDM desactivado (el tema sigue instalado). Reinicia para comprobarlo."
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
