// POC fase 0 (BWM, ver README.md): cargar una decoración KDecoration3 real (Breeze/Aurorae) fuera de KWin
// y pintarla en un QImage. Basado en la idea de kwin/src/kcms/decoration (previewbridge).
#include <KDecoration3/Decoration>
#include <KDecoration3/DecoratedWindow>
#include <KDecoration3/DecorationSettings>
#include <KDecoration3/DecorationButton>
#include <KDecoration3/DecorationShadow>
#include <KDecoration3/Private/DecorationBridge>
#include <KDecoration3/Private/DecoratedWindowPrivate>
#include <KDecoration3/Private/DecorationSettingsPrivate>
#include <KPluginFactory>
#include <KPluginMetaData>
#include <QGuiApplication>
#include <QHoverEvent>
#include <QIcon>
#include <QImage>
#include <QPainter>
#include <QElapsedTimer>
#include <KConfig>
#include <KConfigGroup>
#include <cstdio>

using namespace KDecoration3;

class Win : public DecoratedWindowPrivateV4 {
public:
    Win(DecoratedWindow *c, Decoration *d) : DecoratedWindowPrivateV4(c, d) {}
    bool active = true; QSizeF sz{900, 500};
    bool isActive() const override { return active; }
    QString caption() const override { return QStringLiteral("kitty — ~/Projects/hyprland-de"); }
    bool isOnAllDesktops() const override { return false; }
    bool isShaded() const override { return false; }
    QIcon icon() const override { return QIcon::fromTheme(QStringLiteral("utilities-terminal")); }
    bool isMaximized() const override { return false; }
    bool isMaximizedHorizontally() const override { return false; }
    bool isMaximizedVertically() const override { return false; }
    bool isKeepAbove() const override { return false; }
    bool isKeepBelow() const override { return false; }
    bool isCloseable() const override { return true; }
    bool isMaximizeable() const override { return true; }
    bool isMinimizeable() const override { return true; }
    bool providesContextHelp() const override { return false; }
    bool isModal() const override { return false; }
    bool isShadeable() const override { return true; }
    bool isMoveable() const override { return true; }
    bool isResizeable() const override { return true; }
    qreal width() const override { return sz.width(); }
    qreal height() const override { return sz.height(); }
    QSizeF size() const override { return sz; }
    QPalette palette() const override { return QGuiApplication::palette(); }
    Qt::Edges adjacentScreenEdges() const override { return {}; }
    qreal scale() const override { return 1.0; }
    qreal nextScale() const override { return 1.0; }
    void requestShowToolTip(const QString &t) override { fprintf(stderr, "REQ tooltip %s\n", qPrintable(t)); }
    void requestHideToolTip() override {}
    void requestClose() override { fprintf(stderr, "REQ close\n"); }
    void requestToggleMaximization(Qt::MouseButtons) override { fprintf(stderr, "REQ maximize\n"); }
    void requestMinimize() override { fprintf(stderr, "REQ minimize\n"); }
    void requestContextHelp() override {}
    void requestToggleOnAllDesktops() override {}
    void requestToggleShade() override {}
    void requestToggleKeepAbove() override {}
    void requestToggleKeepBelow() override {}
    void requestShowWindowMenu(const QRect &) override { fprintf(stderr, "REQ menu\n"); }
    QColor color(ColorGroup g, ColorRole r) const override {
        const QByteArray path = qgetenv("POC_SCHEME");
        KConfig cfg(path.isEmpty() ? QStringLiteral("kdeglobals") : QString::fromLocal8Bit(path), path.isEmpty() ? KConfig::FullConfig : KConfig::SimpleConfig);
        KConfigGroup wm(&cfg, QStringLiteral("WM"));
        const bool a = g == ColorGroup::Active;
        switch (r) {
        case ColorRole::Frame: return wm.readEntry(a ? "frame" : "inactiveFrame", wm.readEntry("activeBackground", QColor(Qt::gray)));
        case ColorRole::TitleBar: return wm.readEntry(a ? "activeBackground" : "inactiveBackground", QColor(Qt::gray));
        case ColorRole::Foreground: return wm.readEntry(a ? "activeForeground" : "inactiveForeground", QColor(Qt::white));
        default: return QColor();
        }
    }
    QString windowClass() const override { return QStringLiteral("kitty"); }
    bool hasApplicationMenu() const override { return false; }
    bool isApplicationMenuActive() const override { return false; }
    void showApplicationMenu(int) override {}
    void requestShowApplicationMenu(const QRect &, int) override {}
    QString applicationMenuServiceName() const override { return {}; }
    QString applicationMenuObjectPath() const override { return {}; }
    void popup(const Positioner &, QMenu *) override {}
    bool isExcludedFromCapture() const override { return false; }
    void requestToggleExcludeFromCapture() override {}
};

class Settings : public DecorationSettingsPrivateV2 {
public:
    explicit Settings(DecorationSettings *p) : DecorationSettingsPrivateV2(p) {}
    bool isOnAllDesktopsAvailable() const override { return true; }
    bool isAlphaChannelSupported() const override { return true; }
    bool isCloseOnDoubleClickOnMenu() const override { return false; }
    QList<DecorationButtonType> decorationButtonsLeft() const override { return {DecorationButtonType::Menu, DecorationButtonType::OnAllDesktops}; }
    QList<DecorationButtonType> decorationButtonsRight() const override { return {DecorationButtonType::ContextHelp, DecorationButtonType::Minimize, DecorationButtonType::Maximize, DecorationButtonType::Close}; }
    BorderSize borderSize() const override { return BorderSize::Normal; }
    bool isAlwaysShowExcludeFromCapture() const override { return false; }
};

Win *g_win = nullptr;
class Bridge : public DecorationBridge {
public:
    std::unique_ptr<DecoratedWindowPrivate> createClient(DecoratedWindow *c, Decoration *d) override { auto w = std::make_unique<Win>(c, d); g_win = w.get(); return w; }
    std::unique_ptr<DecorationSettingsPrivate> settings(DecorationSettings *p) override { return std::make_unique<Settings>(p); }
};

static void render(Decoration *d, const QString &out) {
    d->apply(d->nextState()->clone());
    const QRectF r = d->rect();
    QImage img(r.size().toSize(), QImage::Format_ARGB32_Premultiplied);
    img.fill(Qt::transparent);
    QPainter p(&img);
    d->paint(&p, r);
    p.fillRect(QRectF(d->borderLeft(), d->borderTop(), r.width() - d->borderLeft() - d->borderRight(), r.height() - d->borderTop() - d->borderBottom()), QColor(30, 30, 30));
    p.end();
    img.copy(0, 0, img.width(), std::min<int>(img.height(), int(d->borderTop()) + 12)).save(out);
}

int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    const QString pluginId = argc > 1 ? QString::fromLocal8Bit(argv[1]) : QStringLiteral("org.kde.breeze");
    const QString theme = argc > 2 ? QString::fromLocal8Bit(argv[2]) : QString();
    const QString out = argc > 3 ? QString::fromLocal8Bit(argv[3]) : QStringLiteral("deco.png");
    const auto plugins = KPluginMetaData::findPlugins(QStringLiteral("org.kde.kdecoration3"));
    KPluginMetaData md;
    for (const auto &m : plugins) if (m.pluginId() == pluginId) md = m;
    if (!md.isValid()) { fprintf(stderr, "no plugin %s\n", qPrintable(pluginId)); return 2; }
    auto factory = KPluginFactory::loadFactory(md).plugin;
    Bridge bridge;
    QVariantMap args{{QStringLiteral("bridge"), QVariant::fromValue(&bridge)}};
    if (!theme.isEmpty()) args.insert(QStringLiteral("theme"), theme);
    QElapsedTimer t; t.start();
    auto *deco = factory->create<Decoration>(nullptr, QVariantList{args});
    if (!deco) { fprintf(stderr, "create failed\n"); return 3; }
    auto settings = std::make_shared<DecorationSettings>(&bridge);
    deco->setSettings(settings);
    deco->create();
    if (!deco->init()) { fprintf(stderr, "init failed\n"); }
    deco->apply(deco->nextState()->clone());
    fprintf(stderr, "INIT %lld ms borders L%g T%g R%g B%g shadow %d buttons\n", (long long)t.elapsed(), deco->borderLeft(), deco->borderTop(), deco->borderRight(), deco->borderBottom(), deco->shadow() ? 1 : 0);
    // Deja que el decorador procese timers/animaciones iniciales
    QElapsedTimer w; w.start(); while (w.elapsed() < 400) app.processEvents();
    fprintf(stderr, "AFTER borders L%g T%g R%g B%g titlebar %g,%g %gx%g rect %gx%g\n", deco->borderLeft(), deco->borderTop(), deco->borderRight(), deco->borderBottom(), deco->titleBar().x(), deco->titleBar().y(), deco->titleBar().width(), deco->titleBar().height(), deco->rect().width(), deco->rect().height());
    t.restart(); for (int i = 0; i < 100; ++i) render(deco, out); fprintf(stderr, "PAINT avg %.3f ms\n", t.elapsed() / 100.0);
    render(deco, out);
    // Hover sobre el botón de cerrar: buscar por geometría (último botón de la derecha)
    QPointF closePos(deco->rect().width() - deco->borderRight() - 14, deco->borderTop() / 2.0);
    QHoverEvent hover(QEvent::HoverMove, closePos, closePos, QPointF(-1, -1));
    QCoreApplication::sendEvent(deco, &hover);
    w.restart(); while (w.elapsed() < 600) app.processEvents();
    QString hov = out; hov.replace(QStringLiteral(".png"), QStringLiteral("-hover.png"));
    render(deco, hov);
    QMouseEvent press(QEvent::MouseButtonPress, closePos, closePos, Qt::LeftButton, Qt::LeftButton, Qt::NoModifier);
    QCoreApplication::sendEvent(deco, &press);
    QMouseEvent rel(QEvent::MouseButtonRelease, closePos, closePos, Qt::LeftButton, Qt::NoButton, Qt::NoModifier);
    QCoreApplication::sendEvent(deco, &rel);
    w.restart(); while (w.elapsed() < 200) app.processEvents();
    if (g_win) { g_win->active = false; Q_EMIT deco->window()->activeChanged(false); }
    w.restart(); while (w.elapsed() < 400) app.processEvents();
    QString ina = out; ina.replace(QStringLiteral(".png"), QStringLiteral("-inactive.png"));
    render(deco, ina);
    return 0;
}
