# bwm-decorator

Auxiliar de decoraciones de Breeze (fase 6a de `docs/BREEZE_PLAN.md`). Todavía no existe:
aquí sólo está la prueba de concepto de la fase 0.

`poc-fase0.cpp` carga una decoración de KDecoration3 real (Breeze, Aurorae…) fuera de KWin y la
pinta en un PNG, con hover, clic e inactiva. Resultados en `docs/BREEZE_ARCH.md` §2 (prueba d).

```bash
g++ -std=c++20 -O2 -fPIC poc-fase0.cpp -o /tmp/deco-poc $(pkg-config --cflags --libs Qt6Gui) \
  -I/usr/include/KDecoration3 -I/usr/include/KF6/KCoreAddons -I/usr/include/KF6/KConfig \
  -I/usr/include/KF6/KConfigCore -lkdecorations3 -lkdecorations3private -lKF6CoreAddons -lKF6ConfigCore
POC_SCHEME=/usr/share/color-schemes/BreezeDark.colors QT_QPA_PLATFORM=offscreen /tmp/deco-poc org.kde.breeze "" /tmp/breeze.png
QT_QPA_PLATFORM=offscreen /tmp/deco-poc org.kde.kwin.aurorae __aurorae__svg__<tema> /tmp/aurorae.png
```

Código propio de BWM; la estructura sigue la del `PreviewBridge` de KWin
(`kwin/src/kcms/decoration/declarative-plugin`, v6.7.5) sin copiar su código.
