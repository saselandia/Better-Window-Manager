// SPDX-License-Identifier: GPL-2.0-or-later
// R5 session check: drives the original PanelConfiguration.qml of a disposable
// layer-shell panel in the running Hyprland and measures where the compositor
// placed each surface (hyprctl layers). No pointer input except the autohide case, which warps
// the cursor to the panel's own edge strip and restores it; no daily panel changes.
// Run through check-edit-mode-session.py, which isolates every XDG root.
#include "outputidentity.h"
#include "panelconfigview.h"
#include "panelruntime.h"
#include "panelviewhost.h"
#include "viewcorona.h"
#include "surfaces.h"
#include "widgetexplorerview.h"
#include <KConfig>
#include <KConfigGroup>
#include <KPackage/PackageLoader>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/Dialog>
#include <QCoreApplication>
#include <QAction>
#include <QDir>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcess>
#include <QQmlContext>
#include <QQmlExpression>
#include <QQuickItem>
#include <QScreen>
#include <QTest>
#include <QtPlugin>

Q_IMPORT_PLUGIN(BwmWindowSystemPlugin)

namespace {
QList<QRect> layers(const QString &ns, const QString &connector = {})
{
    QProcess process;
    auto environment = QProcessEnvironment::systemEnvironment();
    environment.insert(QStringLiteral("XDG_RUNTIME_DIR"), qEnvironmentVariable("BWM_R5_HYPR_RUNTIME"));
    process.setProcessEnvironment(environment);
    process.start(QStringLiteral("hyprctl"), {QStringLiteral("-j"), QStringLiteral("layers")});
    if (!process.waitForFinished(3000)) return {};
    QList<QRect> result;
    const auto monitors = QJsonDocument::fromJson(process.readAllStandardOutput()).object();
    for (auto it = monitors.begin(); it != monitors.end(); ++it) {
        if (!connector.isEmpty() && it.key() != connector) continue;
        const auto monitor = it.value();
        const auto levels = monitor.toObject().value(QStringLiteral("levels")).toObject();
        for (const auto &level : levels)
            for (const auto &layer : level.toArray()) {
                const auto o = layer.toObject();
                if (o.value(QStringLiteral("namespace")).toString() == ns)
                    result.append(QRect(o.value(QStringLiteral("x")).toInt(), o.value(QStringLiteral("y")).toInt(),
                                        o.value(QStringLiteral("w")).toInt(), o.value(QStringLiteral("h")).toInt()));
            }
    }
    return result;
}
// Reserved zones of a monitor [left, top, right, bottom], matched by the connector Qt reports
// for this run only (never stored).
QMargins reserved(const QString &connector)
{
    QProcess process;
    auto environment = QProcessEnvironment::systemEnvironment();
    environment.insert(QStringLiteral("XDG_RUNTIME_DIR"), qEnvironmentVariable("BWM_R5_HYPR_RUNTIME"));
    process.setProcessEnvironment(environment);
    process.start(QStringLiteral("hyprctl"), {QStringLiteral("-j"), QStringLiteral("monitors")});
    if (!process.waitForFinished(3000)) return {};
    for (const auto &m : QJsonDocument::fromJson(process.readAllStandardOutput()).array()) {
        const auto o = m.toObject();
        if (o.value(QStringLiteral("name")).toString() != connector) continue;
        const auto r = o.value(QStringLiteral("reserved")).toArray();
        if (r.size() == 4) return QMargins(r[0].toInt(), r[1].toInt(), r[2].toInt(), r[3].toInt());
    }
    return {};
}
// Ordinary toplevels (xdg_toplevel) mapped by this process: a popup that lost its layer role
// shows up here and Breeze would place it in the middle of the screen.
int ownClients()
{
    QProcess process;
    auto environment = QProcessEnvironment::systemEnvironment();
    environment.insert(QStringLiteral("XDG_RUNTIME_DIR"), qEnvironmentVariable("BWM_R5_HYPR_RUNTIME"));
    process.setProcessEnvironment(environment);
    process.start(QStringLiteral("hyprctl"), {QStringLiteral("-j"), QStringLiteral("clients")});
    if (!process.waitForFinished(3000)) return -1;
    int count = 0;
    for (const auto &c : QJsonDocument::fromJson(process.readAllStandardOutput()).array())
        if (c.toObject().value(QStringLiteral("pid")).toInteger() == QCoreApplication::applicationPid()) ++count;
    return count;
}
QJsonDocument hyprJson(const QStringList &arguments)
{
    QProcess process;
    auto environment = QProcessEnvironment::systemEnvironment();
    environment.insert(QStringLiteral("XDG_RUNTIME_DIR"), qEnvironmentVariable("BWM_R5_HYPR_RUNTIME"));
    process.setProcessEnvironment(environment);
    process.start(QStringLiteral("hyprctl"), arguments);
    if (!process.waitForFinished(3000)) return {};
    return QJsonDocument::fromJson(process.readAllStandardOutput());
}
QPoint cursorPos()
{
    const auto o = hyprJson({QStringLiteral("-j"), QStringLiteral("cursorpos")}).object();
    return QPoint(o.value(QStringLiteral("x")).toInt(), o.value(QStringLiteral("y")).toInt());
}
void warpCursor(const QPoint &p)
{
    hyprJson({QStringLiteral("dispatch"), QStringLiteral("hl.dsp.cursor.move({x=%1,y=%2})").arg(p.x()).arg(p.y())});
}
QString activeWindow()
{
    return hyprJson({QStringLiteral("-j"), QStringLiteral("activewindow")}).object().value(QStringLiteral("address")).toString();
}
struct EnterCounter : QObject {
    int enters = 0;
    bool eventFilter(QObject *, QEvent *event) override {if (event->type() == QEvent::Enter) ++enters;return false;}
};
QJsonObject rect(const QRect &r) { return {{"x", r.x()}, {"y", r.y()}, {"w", r.width()}, {"h", r.height()}}; }
PanelConfigView *openDialog()
{
    for (auto *window : QGuiApplication::allWindows())
        if (auto *dialog = qobject_cast<PanelConfigView *>(window))
            if (dialog->isVisible()) return dialog;
    return nullptr;
}
}

class EditModeSessionTest : public QObject
{
    Q_OBJECT
    QJsonArray m_steps;
    void record(const QString &name, const QRect &expected, const QRect &observed)
    {
        m_steps.append(QJsonObject{{"step", name}, {"expected", rect(expected)}, {"observed", rect(observed)}, {"passed", expected == observed}});
    }
    // Waits until hyprctl reports the expected rectangle (or times out and records it).
    void expectPanel(const QString &name, const std::function<QRect()> &expected)
    {
        QRect observed;
        const bool matched = QTest::qWaitFor([&] {
            const auto all = layers(QStringLiteral("bwm-r4-preview"));
            observed = all.size() == 1 ? all.first() : QRect();
            return observed == expected();
        }, 4000);
        record(name, expected(), observed);
        QVERIFY2(matched, qPrintable(QStringLiteral("%1: expected %2,%3 %4x%5, Hyprland %6,%7 %8x%9").arg(name)
            .arg(expected().x()).arg(expected().y()).arg(expected().width()).arg(expected().height())
            .arg(observed.x()).arg(observed.y()).arg(observed.width()).arg(observed.height())));
    }

private Q_SLOTS:
    void initTestCase() { BwmSurface::registerTypes();PanelViewHost::registerTypes(); }
    void nativeMultiplePanelReservationsInHyprland()
    {
        m_steps={};const auto output=qEnvironmentVariable("BWM_R5_OUTPUT");auto *screen=BwmOutput::resolveScreen(output);QVERIFY(screen);
        const auto before=reserved(screen->name());const auto cursor=cursorPos();const auto focused=hyprJson({"-j","activewindow"}).object();
        const auto restore=[&] {
            if(cursorPos()!=cursor)warpCursor(cursor);
            for(const auto &row:hyprJson({"-j","clients"}).array()) {const auto c=row.toObject();
                if(!focused.value("address").toString().isEmpty() && c.value("address")==focused.value("address") && c.value("pid")==focused.value("pid")) {
                    hyprJson({"dispatch",QString("hl.dsp.focus({window=\"address:%1\"})").arg(c.value("address").toString())});break;}}
        };
        struct Restore{std::function<void()> fn;~Restore(){fn();}} restoreOnReturn{restore};
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout("bwm-r5-native-multiple-layout");
        const auto panel=[&] {auto *c=corona.createContainment("org.kde.panel");if(c){c->setLocation(Plasma::Types::TopEdge);c->setFormFactor(Plasma::Types::Horizontal);c->createApplet("org.kde.plasma.analogclock");}return c;};
        auto *a=panel(),*b=panel();QVERIFY(a && b);const auto aId=a->id(),bId=b->id();
        PanelRuntime runtime(&corona,"bwm-r5-native-multiple-plasmashellrc",true,nullptr,true);
        QVERIFY(runtime.setAssignments({{aId,output},{bId,output}}));QVERIFY(runtime.setSkin("plasma"));
        for(auto id:{aId,bId}) {QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
            QVERIFY(runtime.view(id)->applyViewSettings({{"panelVisibility",0},{"floating",false},{"panelLengthMode",2},{"alignment",132},{"minLength",640},{"maxLength",640},{"thickness",id==aId?40:56}}));}
        const QString ns="bwm-r4-native-policy";
        const auto expectReserve=[&](const QString &step,int top) {
            QMargins wanted=before;wanted.setTop(before.top()+top);
            const bool matched=QTest::qWaitFor([&]{return reserved(screen->name())==wanted;},5000);
            if(!matched) {
                const auto current=reserved(screen->name());
                puts(QJsonDocument(QJsonObject{{"reservationDebug",step},{"expectedTop",wanted.top()},{"observedTop",current.top()},
                    {"expectedBottom",wanted.bottom()},{"observedBottom",current.bottom()},{"editMode",corona.isEditMode()},
                    {"runtime",QJsonObject::fromVariantMap(runtime.readiness())}}).toJson(QJsonDocument::Compact).constData());
            }
            m_steps.append(QJsonObject{{"step",step},{"topDelta",top},{"passed",matched}});return matched;
        };
        QVERIFY(expectReserve("same-edge-max-not-sum",56));QTRY_COMPARE(layers(ns,screen->name()).size(),2);QCOMPARE(ownClients(),0);
        QVERIFY(!runtime.view(aId)->capabilities().value("reservationOwner").toBool());QVERIFY(runtime.view(bId)->capabilities().value("reservationOwner").toBool());
        auto all=layers(ns,screen->name());const auto S=screen->geometry();const int x=S.x()+(S.width()-640)/2;
        // Non-owner stays at the edge and can overlap, as in Plasma. It is not stacked.
        QVERIFY(all.contains(QRect(x,S.top()+before.top(),640,56)));QVERIFY(all.contains(QRect(x,S.top(),640,40)));
        QVERIFY(runtime.view(aId)->applyViewSettings({{"thickness",64}}));QVERIFY(expectReserve("thickness-handoff",64));
        QVERIFY(runtime.view(aId)->applyViewSettings({{"panelVisibility",1}}));QVERIFY(expectReserve("autohide-hands-reservation-back",56));
        QVERIFY(runtime.view(bId)->applyViewSettings({{"panelVisibility",3}}));QVERIFY(expectReserve("no-normal-panels-no-reservation",0));
        QVERIFY(runtime.view(aId)->applyViewSettings({{"panelVisibility",0}}));QVERIFY(runtime.view(bId)->applyViewSettings({{"panelVisibility",0}}));
        QVERIFY(expectReserve("normal-modes-restored",64));
        // In edit mode Plasma temporarily reserves all frames so both are reachable.
        corona.setEditMode(true);QVERIFY(expectReserve("edit-mode-temporary-sum",120));
        corona.setEditMode(false);QVERIFY(expectReserve("exit-edit-mode-restores-max",64));
        a->destroy();QTRY_VERIFY(!runtime.view(aId));QVERIFY(expectReserve("remove-owner-promotes-next",56));QTRY_COMPARE(layers(ns,screen->name()).size(),1);
        // Opposite edge also reserves, independently of the old edge and the daily panel.
        b->setLocation(Plasma::Types::BottomEdge);QTRY_VERIFY(runtime.view(bId) && runtime.view(bId)->containment()->location()==Plasma::Types::BottomEdge);
        QMargins opposite=before;opposite.setBottom(before.bottom()+56);
        QTRY_COMPARE(reserved(screen->name()),opposite);
        m_steps.append(QJsonObject{{"step","move-between-opposite-edges"},{"passed",true}});
        QVERIFY(runtime.setSkin("default"));QTRY_VERIFY(layers(ns,screen->name()).isEmpty());QTRY_COMPARE(reserved(screen->name()),before);
        restore();QTRY_COMPARE(cursorPos(),cursor);if(!focused.value("address").toString().isEmpty())QTRY_COMPARE(activeWindow(),focused.value("address").toString());
        m_steps.append(QJsonObject{{"step","multiple-panel-cleanup"},{"passed",true}});
        puts(QJsonDocument(QJsonObject{{"steps",m_steps}}).toJson(QJsonDocument::Compact).constData());
    }
    void originalClonePanelInHyprland()
    {
        m_steps={};
        const auto output=qEnvironmentVariable("BWM_R5_OUTPUT");auto *screen=BwmOutput::resolveScreen(output);QVERIFY(screen);
        const auto before=reserved(screen->name());const auto S=screen->geometry();const auto cursor=cursorPos();
        const auto focused=hyprJson({"-j","activewindow"}).object();
        const auto restore=[&] {
            if(cursorPos()!=cursor)warpCursor(cursor);
            for(const auto &row:hyprJson({"-j","clients"}).array()) {
                const auto c=row.toObject();
                if(c.value("address")==focused.value("address") && c.value("pid")==focused.value("pid") && !focused.value("address").toString().isEmpty()) {
                    hyprJson({"dispatch",QString("hl.dsp.focus({window=\"address:%1\"})").arg(c.value("address").toString())});break;
                }
            }
        };
        struct Restore{std::function<void()> action;~Restore(){action();}} restoreOnReturn{restore};
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout("bwm-r5-clone-layout");auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);
        QVERIFY(c->createApplet("org.kde.plasma.analogclock"));const auto id=c->id();
        PanelRuntime runtime(&corona,"bwm-r5-clone-plasmashellrc",true);runtime.setPanelCloningAllowed(true);
        QVERIFY(runtime.setAssignments({{id,output}}));QVERIFY(runtime.setSkin("plasma"));QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
        auto *view=runtime.view(id);QVERIFY(view->applyViewSettings({{"panelLengthMode",2},{"minLength",640},{"maxLength",640},{"alignment",132}}));
        c->internalAction("configure")->trigger();QPointer<PanelConfigView> dialog;QTRY_VERIFY(dialog=openDialog());
        QQmlExpression choose(qmlContext(dialog->mainItem()),dialog->mainItem(),"clonePanelButton.checked=true");choose.evaluate();QVERIFY(!choose.hasError());
        PlasmaQuick::Dialog *indicator=nullptr;
        QTRY_VERIFY_WITH_TIMEOUT([&] {
            for(auto *w:QGuiApplication::allWindows())if(auto *d=qobject_cast<PlasmaQuick::Dialog*>(w);d && d->isVisible() &&
                d->property("bwmIndicatorScreen").value<QScreen*>()==screen && d->property("onClickedLocation").toInt()==Plasma::Types::TopEdge) {indicator=d;return true;}
            return false;
        }(),5000);
        // The original indicator's clicked signal invokes its own QML handler.
        QVERIFY(indicator->mainItem());QVERIFY(QMetaObject::invokeMethod(indicator->mainItem(),"clicked"));
        QTRY_COMPARE(corona.containments().size(),2);auto *copy=corona.containments().last();QVERIFY(copy!=c);
        QTRY_VERIFY(runtime.view(copy->id()) && runtime.view(copy->id())->isExposed());
        QTRY_COMPARE(layers("bwm-r4-preview",screen->name()).size(),2);
        const auto panels=layers("bwm-r4-preview",screen->name());
        const QRect original(S.x()+(S.width()-view->width())/2,S.bottom()+1-64-view->height(),view->width(),view->height());
        auto *cloned=runtime.view(copy->id());
        const QRect expectedCopy(S.x()+(S.width()-cloned->width())/2,S.top()+64,cloned->width(),cloned->height());
        QVERIFY(panels.contains(original));QVERIFY(panels.contains(expectedCopy));QCOMPARE(copy->applets().size(),1);
        QVERIFY(copy->applets().first()->id()!=c->applets().first()->id());QCOMPARE(reserved(screen->name()),before);QCOMPARE(ownClients(),0);
        m_steps.append(QJsonObject{{"step","original-clone-two-layers"},{"source",rect(original)},{"clone",rect(expectedCopy)},{"passed",true}});
        corona.setEditMode(false);QVERIFY(runtime.setSkin("default"));QTRY_VERIFY(layers("bwm-r4-preview").isEmpty());
        QTRY_VERIFY(layers("bwm-r5-edit-indicator").isEmpty());QTRY_VERIFY(layers("bwm-r4-popup").isEmpty());QCOMPARE(reserved(screen->name()),before);
        restore();QTRY_COMPARE(cursorPos(),cursor);
        if(!focused.value("address").toString().isEmpty())QTRY_COMPARE(activeWindow(),focused.value("address").toString());
        m_steps.append(QJsonObject{{"step","clone-cleanup-reservations-pointer-focus"},{"passed",true}});
        puts(QJsonDocument(QJsonObject{{"steps",m_steps}}).toJson(QJsonDocument::Compact).constData());
    }
    void autoHideEdgeStripInHyprland()
    {
        // AutoHide with the edge strip that stands in for KWin's screen edge: no reservation,
        // the layer stays mapped, the pointer reaching the output edge reveals the panel and
        // leaving it hides it again. Top edge: the daily Breeze panel is at the bottom.
        m_steps = {};
        const auto output = qEnvironmentVariable("BWM_R5_OUTPUT");
        auto *screen = BwmOutput::resolveScreen(output);
        QVERIFY(screen);
        const QString ns = QStringLiteral("bwm-r4-native-policy");
        const QMargins before = reserved(screen->name());
        const QPoint cursor = cursorPos();
        const QString focused = activeWindow();
        ViewCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"), QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(QStringLiteral("bwm-r5-autohide-appletsrc"));
        auto *c = corona.createContainment(QStringLiteral("org.kde.panel"));
        QVERIFY(c);
        c->setLocation(Plasma::Types::TopEdge);
        c->setFormFactor(Plasma::Types::Horizontal);
        QVERIFY(c->createApplet(QStringLiteral("org.kde.plasma.analogclock")));
        const uint id = c->id();
        PanelRuntime runtime(&corona, QStringLiteral("plasmashellrc-autohide"), true, nullptr, true);
        QVERIFY2(runtime.setAssignments({{id, output}}), qPrintable(runtime.error()));
        QVERIFY2(runtime.setSkin(QStringLiteral("plasma")), qPrintable(runtime.error()));
        QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
        QPointer<PanelViewHost> view = runtime.view(id);
        QVERIFY2(view->applyViewSettings({{"panelVisibility", 1}, {"panelLengthMode", 2}, {"minLength", 640}, {"maxLength", 640}}), qPrintable(view->error()));
        QTRY_VERIFY(view->autoHidden());
        QRect layer;
        QTRY_VERIFY((layer = layers(ns, screen->name()).value(0)).isValid() && layer.width() == 640);
        const QRect area = screen->geometry();
        const bool flush = layer.top() == area.top();
        const QMargins hiddenReserve = reserved(screen->name());
        m_steps.append(QJsonObject{{"step", "autohide-hidden-no-reservation"}, {"layer", rect(layer)}, {"reservedTopBefore", before.top()},
            {"reservedTopHidden", hiddenReserve.top()}, {"passed", flush && hiddenReserve == before}});
        bool revealed = false, rehidden = false;
        if (flush && hiddenReserve == before) {
            // Let the strip's input region reach the compositor before moving the pointer.
            QTest::qWait(250);
            EnterCounter counter;view->installEventFilter(&counter);
            warpCursor(QPoint(layer.center().x(), layer.top()));
            revealed = QTest::qWaitFor([&] {return view && !view->autoHidden() && view->contentItem()->position() == QPointF();}, 3000);
            const QPoint warped = cursorPos();
            m_steps.append(QJsonObject{{"step", "autohide-edge-reveals"}, {"cursor", QJsonObject{{"x", warped.x()}, {"y", warped.y()}}},
                {"enterEvents", counter.enters}, {"mask", rect(view->mask().boundingRect())}, {"passed", revealed}});
            view->removeEventFilter(&counter);
            warpCursor(QPoint(layer.center().x(), layer.top() + area.height() / 2));
            rehidden = QTest::qWaitFor([&] {return view && view->autoHidden();}, 3000);
            m_steps.append(QJsonObject{{"step", "autohide-leave-rehides"}, {"passed", rehidden}});
        }
        warpCursor(cursor);
        if (!focused.isEmpty() && activeWindow() != focused)
            hyprJson({QStringLiteral("dispatch"), QStringLiteral("hl.dsp.focus({window=\"address:%1\"})").arg(focused)});
        runtime.setSkin(QStringLiteral("default"));
        QTRY_VERIFY(layers(ns, screen->name()).isEmpty());
        m_steps.append(QJsonObject{{"step", "autohide-cleanup"}, {"cursorRestored", cursorPos() == cursor},
            {"focusRestored", focused.isEmpty() || activeWindow() == focused}, {"passed", layers(ns, screen->name()).isEmpty()}});
        puts(QJsonDocument(QJsonObject{{"steps", m_steps}}).toJson(QJsonDocument::Compact).constData());
        QVERIFY2(flush && hiddenReserve == before, "hidden panel is not flush with the edge or reserved space");
        QVERIFY2(revealed, "pointer on the edge strip did not reveal the panel");
        QVERIFY2(rehidden, "leaving the panel did not hide it again");
    }
    void panelOwnPopupsInHyprland()
    {
        // Popups of the panel containment itself (ConfigOverlay handle popup, paneltoolbox
        // tooltip) are layers next to the panel, never ordinary toplevels.
        m_steps = {};
        const auto output = qEnvironmentVariable("BWM_R5_OUTPUT");
        auto *screen = BwmOutput::resolveScreen(output);
        QVERIFY(screen);
        const auto cursor = cursorPos();
        const auto focused = hyprJson({"-j", "activewindow"}).object();
        const auto restore = [&] {
            if (cursorPos() != cursor) warpCursor(cursor);
            for (const auto &row : hyprJson({"-j", "clients"}).array()) {
                const auto c = row.toObject();
                if (!focused.value("address").toString().isEmpty() && c.value("address") == focused.value("address") && c.value("pid") == focused.value("pid")) {
                    hyprJson({"dispatch", QString("hl.dsp.focus({window=\"address:%1\"})").arg(c.value("address").toString())});
                    break;
                }
            }
        };
        struct Restore { std::function<void()> fn; ~Restore() { fn(); } } restoreOnReturn{restore};
        ViewCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"), QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(QStringLiteral("bwm-r5-popups-appletsrc"));
        auto *c = corona.createContainment(QStringLiteral("org.kde.panel"));
        QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);
        c->setFormFactor(Plasma::Types::Horizontal);
        auto *applet = c->createApplet(QStringLiteral("org.kde.plasma.analogclock"));
        QVERIFY(applet);
        const uint id = c->id();
        PanelRuntime runtime(&corona, QStringLiteral("plasmashellrc-popups"), true);
        QVERIFY2(runtime.setAssignments({{id, output}}), qPrintable(runtime.error()));
        QVERIFY2(runtime.setSkin(QStringLiteral("plasma")), qPrintable(runtime.error()));
        QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
        QPointer<PanelViewHost> view = runtime.view(id);
        QRect panel;
        QTRY_VERIFY((panel = layers(QStringLiteral("bwm-r4-preview")).value(0)).isValid());
        const int baselineClients = ownClients();
        c->internalAction(QStringLiteral("configure"))->trigger();
        QTRY_VERIFY(openDialog());
        // The Panel Settings dialog is itself a bwm-r4-popup layer: wait for it first.
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 1);
        const QRect settingsLayer = layers(QStringLiteral("bwm-r4-popup")).value(0);
        const int baselinePopups = 1;
        auto *root = PlasmaQuick::AppletQuickItem::itemForApplet(c);
        QVERIFY(root);
        QObject *overlay = nullptr;
        QTRY_VERIFY((overlay = root->property("configOverlay").value<QObject *>()));
        auto *appletItem = PlasmaQuick::AppletQuickItem::itemForApplet(applet);
        QVERIFY(appletItem && appletItem->parentItem());
        overlay->setProperty("currentApplet", QVariant::fromValue<QQuickItem *>(appletItem->parentItem()));
        // Without a pointer over the panel showTimer would clear currentApplet (containsMouse):
        // stop it, as when the pointer stays over the applet for the tooltip delay.
        QQmlExpression(qmlContext(overlay), overlay, QStringLiteral("showTimer.stop()")).evaluate();
        QList<QRect> popups;
        const bool shown = QTest::qWaitFor([&] {popups = layers(QStringLiteral("bwm-r4-popup"));return popups.size() == baselinePopups + 1;}, 4000);
        QRect handle;
        for (const auto &r : popups) if (r != settingsLayer) handle = r;
        const int clientsWithHandle = ownClients();
        // Anchored to the applet item (inside the panel's frame margins), as PopupPlasmaWindow
        // with its visual parent upstream: it ends on the applet, over the panel, never centered.
        const QRect appletRect(appletItem->mapToGlobal(QPointF(0, 0)).toPoint() - view->position() + panel.topLeft(),
                               appletItem->size().toSize());
        const bool handleOk = shown && handle.isValid() && handle.bottom() + 1 == appletRect.top()
            && handle.left() < appletRect.right() && handle.right() > appletRect.left() && clientsWithHandle == baselineClients;
        m_steps.append(QJsonObject{{"step", "configoverlay-handle-popup"}, {"panel", rect(panel)}, {"applet", rect(appletRect)}, {"observed", rect(handle)},
            {"ownClients", clientsWithHandle}, {"baselineClients", baselineClients}, {"passed", handleOk}});
        if (!handleOk) {
            QJsonArray seen;for (const auto &r : popups) seen.append(rect(r));
            QJsonArray windows;
            for (auto *w : QGuiApplication::allWindows()) if (w->isVisible())
                windows.append(QJsonObject{{"class", w->metaObject()->className()}, {"geometry", rect(w->geometry())}});
            puts(QJsonDocument(QJsonObject{{"debugPopups", seen}, {"steps", m_steps}, {"visibleWindows", windows}}).toJson(QJsonDocument::Compact).constData());
        }
        QVERIFY2(handleOk, "ConfigOverlay handle popup is not a layer above the panel");
        QQmlExpression(qmlContext(overlay), overlay, QStringLiteral("configurationArea.currentApplet = null")).evaluate();
        QList<QRect> remaining;
        const bool hidden = QTest::qWaitFor([&] {remaining = layers(QStringLiteral("bwm-r4-popup"));return remaining.size() == baselinePopups;}, 4000);
        if (!hidden) {
            QJsonArray seen;for (const auto &r : remaining) seen.append(rect(r));
            QJsonArray windows;
            for (auto *w : QGuiApplication::allWindows()) if (w->isVisible())
                windows.append(QJsonObject{{"class", w->metaObject()->className()}, {"name", w->objectName()}, {"geometry", rect(w->geometry())}});
            puts(QJsonDocument(QJsonObject{{"debugRemaining", seen}, {"baseline", baselinePopups}, {"visibleWindows", windows}}).toJson(QJsonDocument::Compact).constData());
        }
        QVERIFY2(hidden, "ConfigOverlay handle popup stayed mapped after clearing the applet");
        auto *toolBox = root->property("toolBox").value<QQuickItem *>();
        QVERIFY(toolBox);
        QTRY_VERIFY(toolBox->isVisible());
        QQmlExpression(qmlContext(toolBox), toolBox, QStringLiteral("toolTipArea.showToolTip()")).evaluate();
        const bool tipShown = QTest::qWaitFor([&] {return layers(QStringLiteral("bwm-r4-popup")).size() == baselinePopups + 1;}, 4000);
        const int clientsWithTip = ownClients();
        m_steps.append(QJsonObject{{"step", "toolbox-tooltip"}, {"layers", int(layers(QStringLiteral("bwm-r4-popup")).size())},
            {"ownClients", clientsWithTip}, {"passed", tipShown && clientsWithTip == baselineClients}});
        QVERIFY2(tipShown && clientsWithTip == baselineClients, "paneltoolbox tooltip is not a layer");
        QQmlExpression(qmlContext(toolBox), toolBox, QStringLiteral("toolTipArea.hideImmediately()")).evaluate();
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), baselinePopups);
        // AppletAlternatives.qml: opens as a layer above the widget (never an xdg_toplevel) and replaces it.
        Q_EMIT applet->contextualActionsAboutToShow();
        auto *altAction = applet->internalAction(QStringLiteral("alternatives"));
        QVERIFY(altAction);
        altAction->trigger();
        QPointer<QQuickWindow> altDialog;
        QTRY_VERIFY((altDialog = view->alternativesDialog()) && altDialog->isVisible());
        QList<QRect> altPopups;
        QRect altLayer;
        const bool altShown = QTest::qWaitFor([&] {
            altPopups = layers(QStringLiteral("bwm-r4-popup"));
            if (altPopups.size() != baselinePopups + 1) return false;
            altLayer = {};
            for (const auto &r : altPopups) if (r != settingsLayer) altLayer = r;
            return altLayer.isValid() && altLayer.width() > 10 && altLayer.bottom() + 1 == appletRect.top();
        }, 4000);
        const int clientsWithAlt = ownClients();
        const bool altOk = altShown && altLayer.isValid() && altLayer.bottom() + 1 == appletRect.top()
            && altLayer.left() <= appletRect.right() && altLayer.right() >= appletRect.left() && clientsWithAlt == baselineClients;
        auto *altHelper = altDialog->property("alternativesHelper").value<QObject *>();
        QVERIFY(altHelper);
        QMetaObject::invokeMethod(altHelper, "loadAlternative", Q_ARG(QString, QStringLiteral("org.kde.plasma.digitalclock")));
        altDialog->close();
        QTRY_VERIFY(!view->alternativesDialog());
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), baselinePopups);
        const bool switched = QTest::qWaitFor([&] {
            return c->applets().size() == 1 && c->applets().first()->pluginMetaData().pluginId() == QStringLiteral("org.kde.plasma.digitalclock");
        }, 4000);
        m_steps.append(QJsonObject{{"step", "applet-alternatives-popup-and-switch"}, {"observed", rect(altLayer)}, {"applet", rect(appletRect)},
            {"ownClients", clientsWithAlt}, {"switchedToDigitalClock", switched}, {"passed", altOk && switched}});
        if (!altOk || !switched) {
            QJsonArray seen; for (const auto &r : altPopups) seen.append(rect(r));
            puts(QJsonDocument(QJsonObject{{"debugAltPopups", seen}, {"altLayer", rect(altLayer)}, {"appletRect", rect(appletRect)},
                {"clientsWithAlt", clientsWithAlt}, {"switched", switched}}).toJson(QJsonDocument::Compact).constData());
        }
        QVERIFY2(altOk && switched, "AppletAlternatives.qml is not a layer above the widget or did not replace the clock");
        // Leaving edit mode is covered by the other cases (Escape); close it directly here.
        if (auto *dialog = openDialog()) dialog->hide();
        corona.setEditMode(false);
        QTRY_VERIFY(!corona.isEditMode());
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 0);
        runtime.setSkin(QStringLiteral("default"));
        QTRY_VERIFY(layers(QStringLiteral("bwm-r4-preview")).isEmpty());
        restore();
        QTRY_COMPARE(cursorPos(), cursor);
        if (!focused.value("address").toString().isEmpty())
            QTRY_COMPARE(activeWindow(), focused.value("address").toString());
        puts(QJsonDocument(QJsonObject{{"steps", m_steps}}).toJson(QJsonDocument::Compact).constData());
    }
    void originalPanelSettingsInHyprland()
    {
        const auto output = qEnvironmentVariable("BWM_R5_OUTPUT");
        QVERIFY2(!output.isEmpty(), "BWM_R5_OUTPUT is required");
        QCOMPARE(QGuiApplication::platformName(), QStringLiteral("wayland"));
        auto *screen = BwmOutput::resolveScreen(output);
        QVERIFY2(screen, "The output description did not resolve to one screen");
        const QRect S = screen->geometry();
        const int gap = 64; // R4 preview gap above the edge, so it never covers the daily panel.

        ViewCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"), QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(QStringLiteral("bwm-r5-session-appletsrc"));
        auto *c = corona.createContainment(QStringLiteral("org.kde.panel"));
        QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);
        c->setFormFactor(Plasma::Types::Horizontal);
        QVERIFY(c->createApplet(QStringLiteral("org.kde.plasma.analogclock")));
        const uint id = c->id();
        PanelRuntime runtime(&corona, QStringLiteral("plasmashellrc"), true);
        runtime.setOutputMovesAllowed(true);
        QVERIFY2(runtime.setAssignments({{id, output}}), qPrintable(runtime.error()));
        QVERIFY2(runtime.setSkin(QStringLiteral("plasma")), qPrintable(runtime.error()));
        QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
        QPointer<PanelViewHost> view = runtime.view(id);
        expectPanel(QStringLiteral("fill-width"), [&] { return QRect(S.x(), S.bottom() + 1 - gap - view->height(), S.width(), view->height()); });

        c->internalAction(QStringLiteral("configure"))->trigger();
        QPointer<PanelConfigView> dialog;
        QTRY_VERIFY((dialog = openDialog()));
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 1);
        auto *root = dialog->mainItem();
        QStringList errors;
        const auto run = [&](const QString &code, QWindow *target = nullptr) {
            QQmlContext context(qmlContext(dialog->mainItem()));
            context.setContextProperty(QStringLiteral("bwmTarget"), QVariant::fromValue(target));
            QQmlExpression e(&context, dialog->mainItem(), code);
            e.evaluate();
            if (e.hasError()) errors.append(e.error().toString());
        };
        Q_UNUSED(root);

        // Length: Custom (index 2), then the three alignments.
        run(QStringLiteral("widthBox.activated(2)"));
        QTRY_COMPARE(view->lengthMode(), 2);
        QTRY_VERIFY(view->width() < S.width());
        expectPanel(QStringLiteral("custom-left"), [&] { return QRect(S.x(), S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });
        run(QStringLiteral("alignmentBox.activated(2)"));
        QTRY_COMPARE(view->alignment(), int(Qt::AlignRight));
        expectPanel(QStringLiteral("custom-right"), [&] { return QRect(S.right() + 1 - view->width(), S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });
        run(QStringLiteral("alignmentBox.activated(1)"));
        QTRY_COMPARE(view->alignment(), int(Qt::AlignCenter));
        expectPanel(QStringLiteral("custom-center"), [&] { return QRect(S.x() + (S.width() - view->width()) / 2, S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });

        // Floating (index 2): the original frame floats and the window grows by its margins.
        const int before = view->height();
        run(QStringLiteral("floatingBox.activated(2)"));
        QTRY_VERIFY(view->floating());
        QTRY_COMPARE(view->rootObject()->property("floatingness").toDouble(), 1.0);
        QTRY_VERIFY(view->height() > before);
        expectPanel(QStringLiteral("floating-center"), [&] { return QRect(S.x() + (S.width() - view->width()) / 2, S.bottom() + 1 - gap - view->height(), view->width(), view->height()); });

        // Set Position…: indicators are overlay layers on every screen.
        run(QStringLiteral("setPositionButton.checked = true"));
        const int expectedIndicators = 4 * QGuiApplication::screens().size() - 1;
        QTRY_COMPARE_WITH_TIMEOUT(layers(QStringLiteral("bwm-r5-edit-indicator")).size(), expectedIndicators, 5000);
        int inside = 0;
        for (const auto &r : layers(QStringLiteral("bwm-r5-edit-indicator")))
            for (auto *s : QGuiApplication::screens())
                if (s->geometry().contains(r)) { ++inside; break; }
        m_steps.append(QJsonObject{{"step", "indicators"}, {"count", expectedIndicators}, {"insideAScreen", inside}, {"passed", inside == expectedIndicators}});
        QCOMPARE(inside, expectedIndicators);

        // Edges on the same output: the view and its settings stay, as in PanelView.
        struct Edge { int location; const char *name; };
        for (const Edge edge : {Edge{Plasma::Types::TopEdge, "top"}, Edge{Plasma::Types::LeftEdge, "left"},
                                Edge{Plasma::Types::RightEdge, "right"}, Edge{Plasma::Types::BottomEdge, "bottom"}}) {
            run(QStringLiteral("setPositionButton.checked = true; setPositionButton.moveTo(%1)").arg(edge.location));
            QTRY_COMPARE(int(c->location()), edge.location);
            QVERIFY2(dialog && dialog->isVisible(), "The panel settings must stay open");
            QCOMPARE(runtime.view(id), view.data());
            const bool vertical = edge.location == Plasma::Types::LeftEdge || edge.location == Plasma::Types::RightEdge;
            QTRY_COMPARE(c->formFactor(), vertical ? Plasma::Types::Vertical : Plasma::Types::Horizontal);
            QTRY_VERIFY(vertical ? view->height() < S.height() : view->width() < S.width());
            expectPanel(QStringLiteral("edge-") + QLatin1String(edge.name), [&] {
                const int w = view->width(), h = view->height();
                switch (edge.location) {
                case Plasma::Types::TopEdge: return QRect(S.x() + (S.width() - w) / 2, S.y() + gap, w, h);
                case Plasma::Types::LeftEdge: return QRect(S.x() + gap, S.y() + (S.height() - h) / 2, w, h);
                case Plasma::Types::RightEdge: return QRect(S.right() + 1 - gap - w, S.y() + (S.height() - h) / 2, w, h);
                default: return QRect(S.x() + (S.width() - w) / 2, S.bottom() + 1 - gap - h, w, h);
                }
            });
        }

        // Another output (when there is one): the runtime moves the panel and reopens its settings.
        QScreen *other = nullptr;
        for (auto *s : QGuiApplication::screens()) if (s != screen) other = s;
        if (other) {
            run(QStringLiteral("setPositionButton.checked = true"));
            QWindow *indicator = nullptr;
            QTRY_VERIFY_WITH_TIMEOUT([&] {
                for (auto *w : QGuiApplication::allWindows())
                    if (qobject_cast<PlasmaQuick::Dialog *>(w) && w->isVisible() && w->property("bwmIndicatorScreen").value<QScreen *>() == other) {indicator = w; return true;}
                return false;
            }(), 5000);
            run(QStringLiteral("setPositionButton.moveTo(%1, bwmTarget)").arg(int(Plasma::Types::BottomEdge)), indicator);
            QTRY_VERIFY_WITH_TIMEOUT(runtime.view(id) && runtime.view(id) != view.data() && runtime.view(id)->screen() == other, 5000);
            view = runtime.view(id);
            QTRY_VERIFY((dialog = openDialog()));
            const QRect O = other->geometry();
            expectPanel(QStringLiteral("other-output"), [&] { return QRect(O.x() + (O.width() - view->width()) / 2, O.bottom() + 1 - gap - view->height(), view->width(), view->height()); });
        }

        QVERIFY2(errors.isEmpty(), qPrintable(errors.join(u'\n')));
        dialog->requestActivate();
        QTRY_VERIFY(dialog->isActive());
        QTest::keyClick(dialog, Qt::Key_Escape);
        QTRY_VERIFY(!corona.isEditMode());
        {
            KConfig config(QStringLiteral("plasmashellrc"), KConfig::SimpleConfig);
            const auto g = KConfigGroup(&config, QStringLiteral("PlasmaViews")).group(QStringLiteral("Panel %1").arg(id));
            m_steps.append(QJsonObject{{"step", "stored"}, {"alignment", g.readEntry("alignment", 0)}, {"panelLengthMode", g.readEntry("panelLengthMode", -1)},
                                       {"floating", g.readEntry("floating", -1)}, {"location", int(c->location())}});
            QCOMPARE(g.readEntry("floating", 0), 1);
            QCOMPARE(g.readEntry("alignment", 0), int(Qt::AlignCenter));
        }
        runtime.setSkin(QStringLiteral("default"));
        QTRY_VERIFY(layers(QStringLiteral("bwm-r4-preview")).isEmpty());
        puts(QJsonDocument(QJsonObject{{"steps", m_steps}}).toJson(QJsonDocument::Compact).constData());
    }
    void originalWidgetExplorerInHyprland()
    {
        // "Add Widgets…" from the original Panel Settings: the installed WidgetExplorer.qml in
        // a layer beside the edited panel, inside the area Hyprland leaves free.
        m_steps = {};
        const auto output = qEnvironmentVariable("BWM_R5_OUTPUT");
        auto *screen = BwmOutput::resolveScreen(output);
        QVERIFY(screen);
        const QRect S = screen->geometry();
        const int gap = 64;
        ViewCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"), QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(QStringLiteral("bwm-r5-explorer-appletsrc"));
        auto *c = corona.createContainment(QStringLiteral("org.kde.panel"));
        QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);
        c->setFormFactor(Plasma::Types::Horizontal);
        QVERIFY(c->createApplet(QStringLiteral("org.kde.plasma.analogclock")));
        const uint id = c->id();
        PanelRuntime runtime(&corona, QStringLiteral("plasmashellrc-explorer"), true);
        QVERIFY2(runtime.setAssignments({{id, output}}), qPrintable(runtime.error()));
        QVERIFY2(runtime.setSkin(QStringLiteral("plasma")), qPrintable(runtime.error()));
        QTRY_VERIFY(runtime.view(id) && runtime.view(id)->isExposed());
        QPointer<PanelViewHost> view = runtime.view(id);
        expectPanel(QStringLiteral("explorer-panel"), [&] { return QRect(S.x(), S.bottom() + 1 - gap - view->height(), S.width(), view->height()); });
        c->internalAction(QStringLiteral("configure"))->trigger();
        QPointer<PanelConfigView> dialog;
        QTRY_VERIFY((dialog = openDialog()));
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 1);
        QQmlExpression(qmlContext(dialog->mainItem()), dialog->mainItem(), QStringLiteral("configDialog.showAddWidgetDialog()")).evaluate();
        QTRY_VERIFY(view->widgetExplorer() && view->widgetExplorer()->isVisible());
        auto *explorer = view->widgetExplorer();
        QVERIFY2(explorer->error().isEmpty(), qPrintable(explorer->error()));
        // PanelConfigView hides once the side bar opens, as upstream.
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 0);
        const QMargins R = reserved(screen->name());
        const auto expected = [&] {
            const int bottom = S.bottom() + 1 - R.bottom() - (gap + view->height());
            return QRect(S.x() + R.left(), S.y() + R.top(), explorer->sidePanel()->width(), bottom - S.y() - R.top());
        };
        QRect observed;
        const bool matched = QTest::qWaitFor([&] {
            const auto all = layers(QStringLiteral("bwm-r5-widget-explorer"));
            observed = all.size() == 1 ? all.first() : QRect();
            return observed == expected();
        }, 5000);
        record(QStringLiteral("explorer-layer"), expected(), observed);
        QVERIFY2(matched, qPrintable(QStringLiteral("explorer: expected %1,%2 %3x%4, Hyprland %5,%6 %7x%8")
            .arg(expected().x()).arg(expected().y()).arg(expected().width()).arg(expected().height())
            .arg(observed.x()).arg(observed.y()).arg(observed.width()).arg(observed.height())));
        auto *root = explorer->rootItem();
        const auto eval = [&](const QString &code) {QQmlExpression e(qmlContext(root), root, code);const auto v = e.evaluate();return v;};
        QTRY_VERIFY(eval(QStringLiteral("root.widgetExplorer !== null && root.widgetExplorer.widgetsModel.count > 1")).toBool());
        const int applets = c->applets().size();
        eval(QStringLiteral("root.widgetExplorer.addApplet('org.kde.plasma.digitalclock')"));
        QTRY_COMPARE(c->applets().size(), applets + 1);
        m_steps.append(QJsonObject{{"step", "explorer-add-applet"}, {"applets", int(c->applets().size())}, {"passed", true}});
        // Closing from a panel reopens its settings (WidgetExplorer.qml onClosed).
        eval(QStringLiteral("sidePanelStack.item.closed()"));
        QTRY_VERIFY(layers(QStringLiteral("bwm-r5-widget-explorer")).isEmpty());
        QTRY_VERIFY((dialog = openDialog()));
        QTRY_COMPARE(layers(QStringLiteral("bwm-r4-popup")).size(), 1);
        m_steps.append(QJsonObject{{"step", "explorer-closed-settings-reopened"}, {"passed", true}});
        dialog->requestActivate();
        QTRY_VERIFY(dialog->isActive());
        QTest::keyClick(dialog, Qt::Key_Escape);
        QTRY_VERIFY(!corona.isEditMode());
        runtime.setSkin(QStringLiteral("default"));
        QTRY_VERIFY(layers(QStringLiteral("bwm-r4-preview")).isEmpty());
        puts(QJsonDocument(QJsonObject{{"steps", m_steps}}).toJson(QJsonDocument::Compact).constData());
    }
};

QTEST_MAIN(EditModeSessionTest)
#include "test-editmode-session.moc"
