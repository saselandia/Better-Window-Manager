> **Incidente posterior:** ver [BREEZE_RECOVERY.md](BREEZE_RECOVERY.md). La habilitación de sombras se revirtió y las miniaturas Breeze están temporalmente desactivadas.

# R6 — corrección adelantada del veto de sombras (parcial)

2026-11-12. R0 identificó una causa independiente del anfitrión/editor: `breeze-float-all`
impone no_shadow=true a todas las ventanas, y `CBreezeShadow::draw` omite el render si la
regla noShadow() es verdadera. Esto cancela la sombra original enviada por KDecoration.

Retirado **sólo ese veto global**. Las sombras genéricas de Hyprland siguen apagadas mediante
appearance.lua; la sombra KDE conserva sus datos originales y los overrides explícitos del
usuario. La regla de Sin marco mantiene no_shadow=true y decorate=false. No se cambia CSD,
protocolo, C++ ni ABI; no requiere recompilar plugin. No se forzó reload en la sesión.

Regresión `tests/test_plasma_shadow_policy.py`: ejecuta el Lua de reglas con un colector,
verifica que los defaults permiten sombra y Sin marco sigue sin ella. Pasa.

Esta corrección no certifica sombras idénticas: quedan DPR, alpha, foco, animación, orden,
CSD, bordes, fullscreen, comparación contra Plasma y prueba con el binario realmente cargado.
R6 continúa abierta; se adelantó sólo este fallo P1 porque no depende de R2–R5. La prueba
visual se deja para mañana. Rollback: reponer el hunk no_shadow en la regla default, sin
alterar el renderizador ni reemplazar el .so cargado.
