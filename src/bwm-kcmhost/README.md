# bwm-kcmhost — módulo QML `org.bwm.kcm`

Fase 11 de `docs/BREEZE_PLAN.md`. Un elemento `KcmHost` que carga un KCM real de Plasma
(`plasma/kcms/systemsettings/<id>`) con `KQuickConfigModuleLoader::loadModule` en el **mismo motor
QML** de la ventana, como hace systemsettings, y coloca su página (y sus subpáginas) dentro.

```qml
import org.bwm.kcm
KcmHost { module: "kcm_colors" }   // kcm, error, name, description, iconName, depth, pop()
```

`KcmHost.info(id)` da nombre, descripción e icono traducidos sin cargar el módulo.

- `make && make install` → `~/.local/share/bwm/qml/org/bwm/kcm/` (copia temporal + `mv`).
- Sólo lo importa la ventana de Preferencias de Breeze (`qs -p plasmaSettings.qml`, con
  `QML_IMPORT_PATH` puesto por `open-settings.sh`); nunca la barra (`qs -c ii`), así un fallo de un
  KCM no tumba el escritorio.
- `mainUi()` antes de `load()`: `KQuickConfigModule::engine()` sólo existe después, y `kcm_fonts`
  (que añade su proveedor de imágenes en `load()`) tumbaba el proceso en el orden inverso.
- Sólo KCM de QML (`KQuickConfigModule`); los de QWidget no se pueden incrustar en Qt Quick.

Código propio de BWM, GPL-2.0-or-later. Requiere Qt 6 (Quick, Qml) y KF6 KCMUtils.
