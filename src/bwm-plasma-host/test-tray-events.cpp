// SPDX-License-Identifier: GPL-2.0-or-later
#include "outputidentity.h"
#include "surfaces.h"
#include <KStatusNotifierItem>
#include <KWaylandExtras>
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <Plasma/Corona>
#include <Plasma/Plasma>
#include <QAbstractItemModel>
#include <QAction>
#include <QApplication>
#include <QDBusArgument>
#include <QDBusConnection>
#include <QDBusConnectionInterface>
#include <QDBusContext>
#include <QDBusError>
#include <QDBusMessage>
#include <QDBusMetaType>
#include <QDBusPendingCall>
#include <QDBusServiceWatcher>
#include <QFileInfo>
#include <QIcon>
#include <QMenu>
#include <QMouseEvent>
#include <QPainter>
#include <QPointer>
#include <QProcess>
#include <QQuickItem>
#include <QQuickPaintedItem>
#include <QQuickWindow>
#include <QScopeGuard>
#include <QScreen>
#include <QSignalSpy>
#include <QtGui/qguiapplication_platform.h>
#include <QtTest>
#include <QtWaylandClient/private/qwaylandshellsurface_p.h>
#include <QtWaylandClient/private/qwaylandwindow_p.h>
#include <any>
#include <functional>
#include <optional>
#include <utility>

using namespace Qt::StringLiterals;

struct TrayPixmap {
    int width;
    int height;
    QByteArray argb;
};
using TrayPixmaps = QList<TrayPixmap>;
Q_DECLARE_METATYPE(TrayPixmap)
struct xdg_popup;

QDBusArgument &operator<<(QDBusArgument &wire, const TrayPixmap &pixmap) {
    wire.beginStructure();
    wire << pixmap.width << pixmap.height << pixmap.argb;
    wire.endStructure();
    return wire;
}

const QDBusArgument &operator>>(const QDBusArgument &wire, TrayPixmap &pixmap) {
    wire.beginStructure();
    wire >> pixmap.width >> pixmap.height >> pixmap.argb;
    wire.endStructure();
    return wire;
}

namespace {
const auto watcherName = u"org.kde.StatusNotifierWatcher"_s;
const auto watcherPath = u"/StatusNotifierWatcher"_s;
const auto itemPath = u"/StatusNotifierItem"_s;
const auto itemInterface = u"org.kde.StatusNotifierItem"_s;
const auto hostPrefix = u"org.kde.StatusNotifierHost-"_s;

class TrayWatcher : public QObject, protected QDBusContext {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.kde.StatusNotifierWatcher")
    Q_PROPERTY(QStringList RegisteredStatusNotifierItems READ items)
    Q_PROPERTY(int ProtocolVersion READ protocolVersion CONSTANT)

public:
    explicit TrayWatcher(const QDBusConnection &bus) {
        owners.setConnection(bus);
        owners.setWatchMode(QDBusServiceWatcher::WatchForUnregistration);
        connect(&owners, &QDBusServiceWatcher::serviceUnregistered, this, [this](const QString &service) {
            if (!item.startsWith(service + u'/')) return;
            const auto removed = std::exchange(item, {});
            Q_EMIT StatusNotifierItemUnregistered(removed);
        });
    }

    QStringList items() const {
        ++inventoryReads;
        return item.isEmpty() ? QStringList{} : QStringList{item};
    }

    int protocolVersion() const { return 0; }
    QString registeredItem() const { return item; }

    mutable int inventoryReads = 0;
    QString host;

public Q_SLOTS:
    void RegisterStatusNotifierHost(const QString &name) { host = name; }
    void RegisterStatusNotifierItem(const QString &argument) {
        if (!calledFromDBus() || !item.isEmpty()) return;
        const auto service = argument == itemPath ? message().service() : argument;
        const auto *daemon = connection().interface();
        if (!service.startsWith(u':') || service.contains(u'/') || !daemon) return;
        const auto registered = daemon->isServiceRegistered(service);
        if (!registered.isValid() || !registered.value()) return;
        item = service + itemPath;
        owners.addWatchedService(service);
        Q_EMIT StatusNotifierItemRegistered(item);
    }

Q_SIGNALS:
    void StatusNotifierItemRegistered(const QString &item);
    void StatusNotifierItemUnregistered(const QString &item);

private:
    QDBusServiceWatcher owners;
    QString item;
};

class TrayItem : public QObject {
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "org.kde.StatusNotifierItem")
    Q_PROPERTY(QString Id READ id CONSTANT)
    Q_PROPERTY(QString Category READ category CONSTANT)
    Q_PROPERTY(QString Status READ status)
    Q_PROPERTY(TrayPixmaps IconPixmap READ pixmaps)
    Q_PROPERTY(TrayPixmaps AttentionIconPixmap READ emptyPixmaps CONSTANT)
    Q_PROPERTY(TrayPixmaps OverlayIconPixmap READ emptyPixmaps CONSTANT)

public:
    QString id() const { return u"bwm-r4-tray-test"_s; }
    QString category() const { return u"ApplicationStatus"_s; }
    QString status() const { return passive ? u"Passive"_s : u"Active"_s; }
    TrayPixmaps emptyPixmaps() const { return {}; }
    TrayPixmaps pixmaps() const {
        // SNI carries ARGB in network byte order.
        const auto pixel = QByteArray::fromHex(blue ? "ff0000ff" : "ffff0000");
        return {{16, 16, pixel.repeated(16 * 16)}};
    }

    void setPassive() {
        passive = true;
        Q_EMIT NewStatus(status());
    }
    void setBlue() {
        blue = true;
        Q_EMIT NewIcon();
    }

    QList<QVariantList> actions;

public Q_SLOTS:
    void ProvideXdgActivationToken(const QString &) {}
    void Activate(int x, int y) { actions.append({u"Activate"_s, x, y}); }
    void SecondaryActivate(int x, int y) { actions.append({u"SecondaryActivate"_s, x, y}); }
    void Scroll(int delta, const QString &orientation) { actions.append({u"Scroll"_s, delta, orientation}); }
    void ContextMenu(int x, int y) { actions.append({u"ContextMenu"_s, x, y}); }

Q_SIGNALS:
    void NewStatus(const QString &status);
    void NewIcon();

private:
    bool passive = false;
    bool blue = false;
};

class TestCorona : public Plasma::Corona {
public:
    QRect screenGeometry(int) const override { return {0, 0, 1280, 800}; }
};

class TrayMenuAnchor : public QQuickPaintedItem {
public:
    explicit TrayMenuAnchor(QQuickItem *parent) : QQuickPaintedItem(parent) { setAcceptedMouseButtons(Qt::LeftButton); }

    void paint(QPainter *painter) override {
        painter->fillRect(boundingRect(), QColor(u"#24517c"_s));
        painter->setPen(Qt::white);
        painter->drawText(boundingRect(), Qt::AlignCenter, u"Abrir menú de prueba"_s);
    }

    std::function<void()> clicked;

protected:
    void mousePressEvent(QMouseEvent *event) override { event->accept(); }
    void mouseReleaseEvent(QMouseEvent *event) override {
        if (contains(event->position()) && clicked) clicked();
        event->accept();
    }
};

class TrayEventsTest : public QObject {
    Q_OBJECT

public:
    static void initMain() {
        if (!qEnvironmentVariableIsSet("BWM_R4_TRAY_TEST_PROXY")) return;
        // The default Qt connection must see only the filtered socket. Fixture
        // endpoints use explicit connections to the private upstream daemon.
        qputenv("BWM_R4_TRAY_TEST_UPSTREAM", qgetenv("DBUS_SESSION_BUS_ADDRESS"));
        qputenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=" + qgetenv("XDG_RUNTIME_DIR") + "/tray-proxy");
        qputenv("QT_QPA_PLATFORMTHEME", "generic");
    }

private Q_SLOTS:
    void initTestCase() {
        const auto runtime = qEnvironmentVariable("XDG_RUNTIME_DIR");
        const bool wayland = qEnvironmentVariable("BWM_R4_TRAY_TEST_MENU_WAYLAND") == u"1"_s;
        QCOMPARE(QGuiApplication::platformName(), wayland ? u"wayland"_s : u"offscreen"_s);
        QVERIFY(QFileInfo(runtime).canonicalFilePath().startsWith(u"/tmp/bwm-r4-tray-events-"_s));
        qDBusRegisterMetaType<TrayPixmap>();
        qDBusRegisterMetaType<TrayPixmaps>();
    }

    void pixmapWireSignature() {
        const auto &meta = TrayItem::staticMetaObject;
        const auto property = meta.property(meta.indexOfProperty("IconPixmap"));
        QCOMPARE(QByteArray(QDBusMetaType::typeToSignature(property.metaType())), QByteArray("a(iiay)"));
    }

    void offscreenActivationFallback() {
        auto token = KWaylandExtras::xdgActivationToken(nullptr, QString());
        QTRY_VERIFY_WITH_TIMEOUT(token.isFinished(), 1000);
        QCOMPARE(token.resultCount(), 1);
        QVERIFY(token.result().isEmpty());
    }

    void originalTrayTracksItemLifecycle_data() {
        QTest::addColumn<bool>("actions");
        if (qEnvironmentVariableIsSet("BWM_R4_TRAY_TEST_ACTIONS")) {
            QTest::newRow("private-bus-actions") << true;
        } else if (qEnvironmentVariableIsSet("BWM_R4_TRAY_TEST_PROXY")) {
            QTest::newRow("filtered") << false;
        } else {
            QTest::newRow("private-bus") << false;
        }
    }

    void originalTrayTracksItemLifecycle() {
        QFETCH(bool, actions);
        const auto proxyBinary = qEnvironmentVariable("BWM_R4_TRAY_TEST_PROXY");
        const bool filtered = !proxyBinary.isEmpty();
        QVERIFY(!actions || !filtered);
        const auto address = qEnvironmentVariable(filtered ? "BWM_R4_TRAY_TEST_UPSTREAM" : "DBUS_SESSION_BUS_ADDRESS");
        const auto runtime = qEnvironmentVariable("XDG_RUNTIME_DIR");
        QCOMPARE(address.section(u',', 0, 0), u"unix:path="_s + runtime + u"/tray-events-bus"_s);
        auto watcherBus = QDBusConnection::connectToBus(address, u"fixture-watcher"_s);
        QVERIFY(watcherBus.isConnected());
        TrayWatcher watcher(watcherBus);
        QVERIFY(watcherBus.registerService(watcherName));
        QVERIFY(watcherBus.registerObject(watcherPath, &watcher, QDBusConnection::ExportAllContents));

        const auto itemConnection = u"fixture-item"_s;
        auto itemBus = std::optional{QDBusConnection::connectToBus(address, itemConnection)};
        QVERIFY(itemBus->isConnected());
        const auto service = itemBus->baseService();
        const auto identity = service + itemPath;
        const auto hostName = hostPrefix + QString::number(QCoreApplication::applicationPid());
        QProcess proxy;
        const auto stopProxy = qScopeGuard([&proxy] {
            if (proxy.state() != QProcess::NotRunning) {
                proxy.kill();
                proxy.waitForFinished(2000);
            }
        });
        if (filtered) {
            QCOMPARE(qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS"), u"unix:path="_s + runtime + u"/tray-proxy"_s);
            proxy.start(proxyBinary, {
                u"--fd=1"_s, address, runtime + u"/tray-proxy"_s, u"--filter"_s,
                u"--own="_s + hostName, u"--see="_s + watcherName,
                u"--call="_s + watcherName + u"=org.freedesktop.DBus.Properties.Get@"_s + watcherPath,
                u"--call="_s + watcherName + u"=org.kde.StatusNotifierWatcher.RegisterStatusNotifierHost@"_s + watcherPath,
                u"--broadcast="_s + watcherName + u"=org.kde.StatusNotifierWatcher.StatusNotifierItemRegistered@"_s + watcherPath,
                u"--broadcast="_s + watcherName + u"=org.kde.StatusNotifierWatcher.StatusNotifierItemUnregistered@"_s + watcherPath,
                u"--call="_s + service + u"=org.freedesktop.DBus.Properties.GetAll@"_s + itemPath,
                u"--broadcast="_s + service + u"=org.kde.StatusNotifierItem.NewStatus@"_s + itemPath,
                u"--broadcast="_s + service + u"=org.kde.StatusNotifierItem.NewIcon@"_s + itemPath,
            });
            QVERIFY2(proxy.waitForReadyRead(3000), proxy.readAllStandardError().constData());
            QCOMPARE(proxy.readAllStandardOutput(), QByteArray("x"));
            const auto filteredBus = QDBusConnection::sessionBus();
            QVERIFY(filteredBus.isConnected());
            auto wrongObject = QDBusMessage::createMethodCall(service, u"/OtherItem"_s,
                                                              u"org.freedesktop.DBus.Properties"_s, u"GetAll"_s);
            wrongObject << itemInterface;
            QCOMPARE(QDBusError(filteredBus.call(wrongObject, QDBus::BlockWithGui, 1000)).type(), QDBusError::AccessDenied);
        }

        TestCorona corona;
        auto *panel = corona.createContainment(u"org.kde.panel"_s);
        QVERIFY(panel);
        auto *tray = panel->createApplet(u"org.kde.plasma.systemtray"_s);
        QVERIFY(tray && !tray->failedToLaunch());
        auto *model = tray->property("systemTrayModel").value<QAbstractItemModel *>();
        QVERIFY(model);
        const auto roles = model->roleNames();
        const int source = roles.key("DataEngineSource", -1);
        const int status = roles.key("Status", -1);
        const int category = roles.key("Category", -1);
        const int icon = roles.key("Icon", -1);
        QVERIFY(source >= 0 && status >= 0 && category >= 0 && icon >= 0);
        QTRY_COMPARE_WITH_TIMEOUT(watcher.host, hostName, 3000);
        QTRY_VERIFY_WITH_TIMEOUT(watcher.inventoryReads > 0, 3000);

        const auto findItem = [&] {
            for (int row = 0; row < model->rowCount(); ++row) {
                const auto index = model->index(row, 0);
                if (index.data(source).toString() == identity) return index;
            }
            return QModelIndex{};
        };
        const auto iconColor = [&] {
            const auto image = findItem().data(icon).value<QIcon>().pixmap(16, 16).toImage();
            return image.isNull() ? QColor() : image.pixelColor(8, 8);
        };

        {
            QVERIFY(!findItem().isValid());
            TrayItem item;
            QVERIFY(itemBus->registerObject(itemPath, &item, QDBusConnection::ExportAllContents));

            auto registration = QDBusMessage::createMethodCall(watcherName, watcherPath, watcherName, u"RegisterStatusNotifierItem"_s);
            registration << itemPath;
            itemBus->call(registration, QDBus::NoBlock);
            QTRY_VERIFY_WITH_TIMEOUT(findItem().isValid(), 3000);
            QTRY_COMPARE_WITH_TIMEOUT(findItem().data(status).toInt(), int(Plasma::Types::ActiveStatus), 3000);
            QCOMPARE(findItem().data(category).toString(), item.category());
            QTRY_COMPARE_WITH_TIMEOUT(iconColor(), QColor(Qt::red), 3000);

            item.setPassive();
            QTRY_COMPARE_WITH_TIMEOUT(findItem().data(status).toInt(), int(Plasma::Types::PassiveStatus), 3000);
            item.setBlue();
            QTRY_COMPARE_WITH_TIMEOUT(iconColor(), QColor(Qt::blue), 3000);

            if (actions) {
                QQuickItem offscreenIcon;
                auto *iconItem = &offscreenIcon;
                QVERIFY(QMetaObject::invokeMethod(tray, "activate", Qt::DirectConnection, identity, QPoint(35, 47), iconItem));
                QTRY_COMPARE_WITH_TIMEOUT(item.actions.size(), 1, 3000);
                QVERIFY(QMetaObject::invokeMethod(tray, "secondaryActivate", Qt::DirectConnection, identity, QPoint(56, 78)));
                QTRY_COMPARE_WITH_TIMEOUT(item.actions.size(), 2, 3000);
                QVERIFY(QMetaObject::invokeMethod(tray, "scroll", Qt::DirectConnection, identity, -120, u"vertical"_s));
                QTRY_COMPARE_WITH_TIMEOUT(item.actions.size(), 3, 3000);
                // The fixture has no Menu property. KDE should send the SNI
                // ContextMenu request to this item instead of importing a menu.
                QVERIFY(QMetaObject::invokeMethod(tray, "openContextMenu", Qt::DirectConnection, identity, QPoint(90, 12), iconItem));
                const QList<QVariantList> expected{
                    {u"Activate"_s, 35, 47}, {u"SecondaryActivate"_s, 56, 78},
                    {u"Scroll"_s, -120, u"vertical"_s}, {u"ContextMenu"_s, 90, 12},
                };
                QTRY_COMPARE_WITH_TIMEOUT(item.actions, expected, 3000);
            }
            if (filtered) {
                auto forbiddenAction = QDBusMessage::createMethodCall(service, itemPath, itemInterface, u"Activate"_s);
                forbiddenAction << 35 << 47;
                const auto reply = QDBusConnection::sessionBus().call(forbiddenAction, QDBus::BlockWithGui, 1000);
                QCOMPARE(QDBusError(reply).type(), QDBusError::AccessDenied);
                QVERIFY(item.actions.isEmpty());
            }
        }
        itemBus.reset();
        QDBusConnection::disconnectFromBus(itemConnection);
        QTRY_VERIFY_WITH_TIMEOUT(!findItem().isValid(), 3000);
        QCOMPARE(watcher.items().size(), 0);
    }

    void originalTrayImportsMenu() {
        const bool wayland = QGuiApplication::platformName() == u"wayland"_s;
        const auto description = qEnvironmentVariable("BWM_R4_TRAY_TEST_OUTPUT");
        QPointer<QScreen> output;
        if (wayland) {
            QString reason;
            output = BwmOutput::resolveScreen(description, &reason);
            QVERIFY2(output, qPrintable(reason + u": "_s + description));
        }
        const auto address = qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS");
        QCOMPARE(address.section(u',', 0, 0),
                 u"unix:path="_s + qEnvironmentVariable("XDG_RUNTIME_DIR") + u"/tray-events-bus"_s);
        auto watcherBus = QDBusConnection::connectToBus(address, u"fixture-menu-watcher"_s);
        QVERIFY(watcherBus.isConnected());
        TrayWatcher watcher(watcherBus);
        QVERIFY(watcherBus.registerService(watcherName));
        QVERIFY(watcherBus.registerObject(watcherPath, &watcher, QDBusConnection::ExportAllContents));

        TestCorona corona;
        auto *panel = corona.createContainment(u"org.kde.panel"_s);
        QVERIFY(panel);
        if (wayland) panel->setLocation(Plasma::Types::TopEdge);
        auto *tray = qobject_cast<Plasma::Containment *>(panel->createApplet(u"org.kde.plasma.systemtray"_s));
        QVERIFY(tray && !tray->failedToLaunch());
        if (wayland) tray->setLocation(Plasma::Types::TopEdge);
        auto *model = tray->property("systemTrayModel").value<QAbstractItemModel *>();
        QVERIFY(model);
        const auto roles = model->roleNames();
        const int source = roles.key("DataEngineSource", -1);
        const int status = roles.key("Status", -1);
        QVERIFY(source >= 0 && status >= 0);
        QTRY_COMPARE_WITH_TIMEOUT(watcher.host, hostPrefix + QString::number(QCoreApplication::applicationPid()), 3000);
        QTRY_VERIFY_WITH_TIMEOUT(watcher.inventoryReads > 0, 3000);

        KStatusNotifierItem producer(u"bwm-r4-menu-test"_s);
        producer.setStandardActionsEnabled(false);
        producer.setStatus(KStatusNotifierItem::Active);
        auto *exported = producer.contextMenu();
        QVERIFY(exported);
        exported->clear();
        auto *command = exported->addAction(u"Test action"_s);
        exported->addAction(u"Disabled action"_s)->setEnabled(false);
        QSignalSpy receipt(command, &QAction::triggered);
        QVERIFY(receipt.isValid());
        QTRY_VERIFY_WITH_TIMEOUT(!watcher.registeredItem().isEmpty(), 3000);
        const auto identity = watcher.registeredItem();
        const auto itemIsActive = [&] {
            for (int row = 0; row < model->rowCount(); ++row) {
                const auto index = model->index(row, 0);
                if (index.data(source).toString() == identity)
                    return index.data(status).toInt() == Plasma::Types::ActiveStatus;
            }
            return false;
        };
        QTRY_VERIFY_WITH_TIMEOUT(itemIsActive(), 3000);

        QQuickWindow testPanel;
        if (wayland) {
            QVERIFY2(output, "The selected output disappeared before creating the fixture window");
            testPanel.setScreen(output);
        }
        testPanel.resize(240, 44);
        TrayMenuAnchor anchor(testPanel.contentItem());
        anchor.setSize(QSizeF(testPanel.size()));
        QQuickItem *anchorItem = &anchor;
        const auto popup = [] { return qobject_cast<QMenu *>(QApplication::activePopupWidget()); };
        const auto closePopup = qScopeGuard([&] {
            if (auto *menu = popup(); menu && menu != exported) menu->close();
        });
        const auto openMenu = [&] {
            return QMetaObject::invokeMethod(tray, "openContextMenu", Qt::DirectConnection, identity, QPoint(12, 12), anchorItem);
        };
        if (wayland) {
            auto *waylandApp = qGuiApp->nativeInterface<QNativeInterface::QWaylandApplication>();
            QVERIFY(waylandApp);
            bool requested = false;
            const auto disconnectClick = qScopeGuard([&] { anchor.clicked = {}; });
            anchor.clicked = [&] {
                if (!requested && waylandApp->lastInputSeat() && waylandApp->lastInputSerial()) requested = openMenu();
            };
            BwmSurface::configurePanel(&testPanel, Qt::TopEdge, 32);
            auto *layer = LayerShellQt::Window::get(&testPanel);
            layer->setScope(u"bwm-r4-tray-menu"_s);
            testPanel.show();
            QTRY_VERIFY_WITH_TIMEOUT(testPanel.isExposed(), 3000);
            const auto *parent = dynamic_cast<QtWaylandClient::QWaylandWindow *>(testPanel.handle());
            QVERIFY(parent && parent->shellSurface());
            QVERIFY(parent->shellSurface()->inherits("LayerShellQt::QWaylandLayerSurface"));
            QVERIFY(layer->exclusionZone() <= 0);
            QVERIFY(output && testPanel.screen() == output && layer->screen() == output);
            qInfo().noquote() << u"Monitor de ensayo:"_s << description;
            qInfo("Pulsa «Abrir menú de prueba» en ese monitor y luego elige «Test action».");
            QTRY_VERIFY_WITH_TIMEOUT(requested, 20000);
        } else {
            QVERIFY(openMenu());
        }
        QTRY_VERIFY_WITH_TIMEOUT(popup() && popup() != exported && popup()->isVisible(), 3000);
        if (wayland) {
            QTRY_VERIFY_WITH_TIMEOUT(popup() && popup()->windowHandle() && popup()->windowHandle()->isExposed() &&
                                     output && popup()->windowHandle()->screen() == output, 3000);
            const auto *window = popup()->windowHandle();
            QCOMPARE(window->transientParent(), &testPanel);
            const auto *platform = dynamic_cast<QtWaylandClient::QWaylandWindow *>(window->handle());
            QVERIFY(platform && platform->shellSurface());
            const auto role = platform->shellSurface()->surfaceRole();
            const auto nativePopup = std::any_cast<xdg_popup *>(&role);
            QVERIFY(nativePopup && *nativePopup);
            QCOMPARE(window->property("_q_waylandPopupAnchorRect").toRect(), QRect(QPoint(), anchor.size().toSize()));
            const auto near = qGuiApp->isLeftToRight() ? Qt::LeftEdge : Qt::RightEdge;
            const auto far = qGuiApp->isLeftToRight() ? Qt::RightEdge : Qt::LeftEdge;
            QCOMPARE(window->property("_q_waylandPopupAnchor").value<Qt::Edges>(), Qt::BottomEdge | near);
            QCOMPARE(window->property("_q_waylandPopupGravity").value<Qt::Edges>(), Qt::BottomEdge | far);
        }
        const auto entries = popup()->actions();
        QCOMPARE(entries.size(), 2);
        QCOMPARE(entries[0]->text().remove(u'&'), u"Test action"_s);
        QVERIFY(entries[0]->isEnabled());
        QCOMPARE(entries[1]->text().remove(u'&'), u"Disabled action"_s);
        QVERIFY(!entries[1]->isEnabled());
        if (!wayland) entries[0]->trigger();
        QTRY_COMPARE_WITH_TIMEOUT(receipt.size(), 1, wayland ? 20000 : 3000);

        if (auto *menu = popup(); menu && menu != exported) menu->close();
        // The importer sends Event("closed") on hide. Drain it before the
        // producer unregisters /MenuBar, using a read on the same connection.
        auto checkMenu = QDBusMessage::createMethodCall(identity.section(u'/', 0, 0), u"/MenuBar"_s,
                                                        u"org.freedesktop.DBus.Properties"_s, u"Get"_s);
        checkMenu << u"com.canonical.dbusmenu"_s << u"Version"_s;
        const auto readback = QDBusConnection::sessionBus().asyncCall(checkMenu);
        QTRY_VERIFY_WITH_TIMEOUT(readback.isFinished(), 3000);
        QVERIFY2(!readback.isError(), qPrintable(readback.error().message()));
    }
};
}

QTEST_MAIN(TrayEventsTest)
#include "test-tray-events.moc"
