// SPDX-License-Identifier: GPL-2.0-or-later
#include "configurationsession.h"
#include "catalog.h"
#include "surfaces.h"
#include "panelsession.h"
#include "packagewindows.h"
#include "viewcorona.h"
#include "panelviewhost.h"
#include "panelviewsettings.h"
#include "panelconfigview.h"
#include "widgetexplorerview.h"
#include <QQmlExpression>
#include <QQmlContext>
#include <QTest>
#include "panelruntime.h"
#include "outputidentity.h"
#include "runtimecontrol.h"
#include "profilestore.h"
#include "migration.h"
#include "desktopbridge.h"
#include "trayprobe.h"
#include <KWindowSystem>
#include <QtPlugin>
Q_IMPORT_PLUGIN(BwmWindowSystemPlugin)
#include <qpa/qplatformscreen.h>
#include <qpa/qwindowsysteminterface.h>
#include <QLockFile>
#include <KSvg/FrameSvg>
#include <QScreen>
#include <LayerShellQt/Window>
#include <KPackage/PackageJob>
#include <QTemporaryDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QCryptographicHash>
#include <QSaveFile>
#include <QProcess>
#include <QProcessEnvironment>
#include <QAbstractItemModel>
#include <QDir>
#include <QApplication>
#include <QAction>
#include <QMenu>
#include <QQuickWindow>
#include <QQuickItem>
#include <QMetaProperty>
#include <QQmlEngine>
#include <QQmlComponent>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <Plasma/Theme>
#include <Plasma/Plasma>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/ConfigView>
#include <PlasmaQuick/AppletPopup>
#include <PlasmaQuick/Dialog>
#include <QQmlContext>
#include <KConfigLoader>
#include <KSharedConfig>
#include <KConfigGroup>
#include <QtTest>
#include <functional>
class TestCorona:public Plasma::Corona {
public: QRect screenGeometry(int)const override { return QRect(0,0,1024,768); }
};
// Only the offscreen test process receives these screens. This exercises real
// QScreen/Qt hotplug signals without connecting to, or emulating, a compositor.
class RuntimeScreen:public QPlatformScreen {
public:
    RuntimeScreen(QString connector,QString model,QString serial,QRect geometry)
        :connector(std::move(connector)),product(std::move(model)),serial(std::move(serial)),rect(geometry){}
    QRect geometry()const override{return rect;}
    int depth()const override{return 32;}
    QImage::Format format()const override{return QImage::Format_ARGB32_Premultiplied;}
    QString name()const override{return connector;}
    QString manufacturer()const override{return "BWM Test";}
    QString model()const override{return product;}
    QString serialNumber()const override{return serial;}
    QString connector,product,serial;QRect rect;
};
class TestOutput {
public:
    TestOutput(QString connector,QString model,QString serial,QRect geometry) {
        platform=new RuntimeScreen(connector,model,serial,geometry);QWindowSystemInterface::handleScreenAdded(platform,false);
    }
    ~TestOutput(){remove();}
    void remove(){if(platform){auto *old=platform;platform=nullptr;QWindowSystemInterface::handleScreenRemoved(old);}}
    QScreen *screen()const{return platform ? platform->screen() : nullptr;}
    RuntimeScreen *platform=nullptr;
};
QQuickItem *findVisual(QQuickItem *item,const QString &name) {
    if(item->objectName()==name)return item;
    for(auto *child:item->childItems())if(auto *found=findVisual(child,name))return found;
    return nullptr;
}
class UiTest:public QObject {
    Q_OBJECT
    void click(PlasmaQuick::ConfigView *view,const char *name) {
        auto *button=findVisual(view->rootObject(),name);
        QVERIFY2(button,name);
        QVERIFY(button->isEnabled());
        QTest::mouseClick(view,Qt::LeftButton,Qt::NoModifier,button->mapToScene(QPointF(button->width()/2,button->height()/2)).toPoint());
        QCoreApplication::processEvents();
    }
private Q_SLOTS:
    void initTestCase() {
        BwmSurface::registerTypes();
        PanelViewHost::registerTypes();
        for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR"}) {
            const QString path=QFileInfo(qEnvironmentVariable(name)).canonicalFilePath();
            QVERIFY2(path.startsWith(QDir::tempPath()+"/"),name);
        }
        QVERIFY(qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS").startsWith("unix:path="+QDir::tempPath()+"/"));
    }
    void liveCatalogRefreshAndNativeMetadata() {
        Catalog catalog;
        auto has=[&](const QString &id){for(const auto &entry:catalog.entries())if(entry.toMap().value("id")==id)return true;return false;};
        QVERIFY(has("org.kde.plasma.analogclock")); // Built-in metadata may reside in a .so/qrc, not a package directory.
        auto entry=[&](const QString &id){for(const auto &e:catalog.entries())if(e.toMap().value("id")==id)return e.toMap();return QVariantMap();};
        QCOMPARE(entry("org.kde.panel").value("kind").toString(),"containment");
        QVERIFY(!entry("org.kde.panel").value("catalogVisible").toBool());
        QVERIFY(entry("org.kde.plasma.systemtray").value("catalogVisible").toBool());
        QCOMPARE(entry("org.kde.plasma.icontasks").value("runtime").toMap().value("status").toString(),"requires-backend-adapter");
        const QString id="org.bwm.r4.disposable";
        QVERIFY(!has(id));
        QTemporaryDir source;
        QVERIFY(QDir().mkpath(source.path()+"/contents/ui"));
        QFile metadata(source.path()+"/metadata.json");QVERIFY(metadata.open(QIODevice::WriteOnly));
        metadata.write(R"({"KPackageStructure":"Plasma/Applet","KPlugin":{"Id":"org.bwm.r4.disposable","Name":"Disposable catalog fixture","Version":"1.0","License":"GPL-2.0-or-later"}})");metadata.close();
        QFile qml(source.path()+"/contents/ui/main.qml");QVERIFY(qml.open(QIODevice::WriteOnly));
        qml.write("import org.kde.plasma.plasmoid\nPlasmoidItem {}\n");qml.close();
        QSignalSpy changes(&catalog,&Catalog::changed);
        const QString packageRoot=qEnvironmentVariable("XDG_DATA_HOME")+"/plasma/plasmoids/";
        auto *install=KPackage::PackageJob::install("Plasma/Applet",source.path(),packageRoot);
        install->setAutoDelete(false);
        QSignalSpy installed(install,&KJob::result);
        QTRY_COMPARE(installed.count(),1);
        QVERIFY2(install->error()==0,qPrintable(install->errorString()));delete install;
        QTRY_VERIFY_WITH_TIMEOUT(has(id),5000);
        QCOMPARE(entry(id).value("kind").toString(),"widget");
        QVERIFY(entry(id).value("catalogVisible").toBool());
        QCOMPARE(entry(id).value("runtime").toMap().value("status").toString(),"unassessed");
        QVERIFY(!entry(id).value("runtime").toMap().value("operationalVerified").toBool());
        QVERIFY(!changes.isEmpty());changes.clear();
        auto *remove=KPackage::PackageJob::uninstall("Plasma/Applet",id,packageRoot);
        remove->setAutoDelete(false);
        QSignalSpy removed(remove,&KJob::result);
        QTRY_COMPARE(removed.count(),1);
        QVERIFY2(remove->error()==0,qPrintable(remove->errorString()));delete remove;
        QTRY_VERIFY_WITH_TIMEOUT(!has(id),5000);
        QVERIFY(!changes.isEmpty());
    }
    void backendInventoryUsesLiveInstancesAndNativeMetadata() {
        const auto unknown=KPluginMetaData(QJsonObject{
            {"KPlugin",QJsonObject{{"Id","org.vendor.unseen"},{"Name","Unseen"}}},
            {"X-Plasma-RequiredExtensions",QJsonArray{"org.vendor.runtime"}}},QString());
        const auto assessment=Catalog::runtimeAssessment(unknown);
        QCOMPARE(assessment.value("status").toString(),"unassessed");
        QCOMPARE(assessment.value("declaredExtensions").toList(),QVariantList{"org.vendor.runtime"});
        QVERIFY(!assessment.value("operationalVerified").toBool());
        for(const auto &id:{"org.kde.plasma.icontasks","org.kde.plasma.pager","org.kde.plasma.showdesktop"}) {
            const auto metadata=KPluginMetaData(QJsonObject{{"KPlugin",QJsonObject{{"Id",id},{"Name",id}}}},QString());
            const auto data=Catalog::runtimeAssessment(metadata);
            QCOMPARE(data.value("status").toString(),"requires-backend-adapter");
            QVERIFY(!data.value("dependencies").toStringList().isEmpty());
            QVERIFY(!data.value("operationalVerified").toBool());
            if(QString(id)=="org.kde.plasma.icontasks"){
                const auto tasks=data.value("experimentalTaskSource").toMap();
                QVERIFY(tasks.value("operations").toStringList().contains("fullscreen"));
                QCOMPARE(tasks.value("ordering").toString(),"compositor-client-order-with-legacy-snapshot-fallback");
                const auto desktops=data.value("experimentalNativeDesktopProtocol").toMap();
                QCOMPARE(desktops.value("barrierProtocolVersion").toInt(),2);
                QCOMPARE(desktops.value("activationReadbackVersion").toInt(),1);
            }
        }
        TestCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);
        auto *a=c->createApplet("org.bwm.r4.shared-config"),*b=c->createApplet("org.bwm.r4.shared-config");
        QVERIFY(a && b);const auto first=a->id(),second=b->id();
        PanelSession session(c,false);
        const auto rows=session.widgetBackends();QCOMPARE(rows.size(),2);
        QSet<uint> ids;for(const auto &row:rows) {
            const auto data=row.toMap();ids.insert(data.value("id").toUInt());
            QCOMPARE(data.value("package").toString(),"org.bwm.r4.shared-config");
            QCOMPARE(data.value("runtime").toMap().value("status").toString(),"unassessed");
        }
        QCOMPARE(ids,(QSet<uint>{first,second}));
        a->destroy();QTRY_COMPARE(session.widgetBackends().size(),1);
        QCOMPARE(session.widgetBackends().first().toMap().value("id").toUInt(),second);
    }
    void nativeTrayPropertyRoles() {
        using ItemStatus = Plasma::Types::ItemStatus;
        // StatusNotifierModel::data returns the enum through QVariant implicitly.
        const auto modelValue = [](ItemStatus status) -> QVariant { return status; };
        const QVariant category{QStringLiteral("ApplicationStatus")};
        for (const auto status : {ItemStatus::ActiveStatus, ItemStatus::PassiveStatus, ItemStatus::NeedsAttentionStatus}) {
            const QVariant role = modelValue(status);
            QVERIFY(nativeTrayPropertiesLoaded(role, category));
            QVERIFY(nativeTrayPropertiesLoaded(QVariant::fromValue(status), category));
            QVERIFY(!nativeTrayPropertiesLoaded(role, QString()));
        }
        QVERIFY(!nativeTrayPropertiesLoaded(modelValue(ItemStatus::UnknownStatus), category));
        QVERIFY(!nativeTrayPropertiesLoaded(QVariant::fromValue(ItemStatus::UnknownStatus), category));
        QVERIFY(!nativeTrayPropertiesLoaded(QVariant::fromValue(ItemStatus::HiddenStatus), category));
        QVERIFY(!nativeTrayPropertiesLoaded(QStringLiteral("Active"), category));
        QVERIFY(!nativeTrayPropertiesLoaded({}, category));
    }
    void nativeTrayInventoryAndProfileCheckpoint() {
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));
        const QString childId = "org.bwm.r4.tray-child";
        const QByteArray legacy = R"({"bar":{"plasma":{"edge":"bottom","style":"opaque"}}})";
        const auto hash = QString::fromLatin1(QCryptographicHash::hash(legacy,QCryptographicHash::Sha256).toHex());
        const QJsonObject widget{{"package","org.kde.plasma.systemtray"},
            {"nativeSettings",QJsonObject{{"extraItems",QJsonArray{childId}}}}};
        const QJsonObject plan{{"version",1},{"legacyJson",QString::fromUtf8(legacy)},{"sourceSha256",hash},
            {"panels",QJsonArray{QJsonObject{{"outputDescription","BWM Test Tray T"},{"containmentPackage","org.kde.panel"},
                                             {"widgets",QJsonArray{widget}}}}}};
        const auto planPath = config.filePath("bwm-tray-plan.json");
        QFile file(planPath);QVERIFY(file.open(QIODevice::WriteOnly));file.write(QJsonDocument(plan).toJson());file.close();
        const auto staged = BwmMigration::stage(planPath).value("directory").toString();
        struct RemoveStage { QString path; ~RemoveStage(){ QDir(path).removeRecursively(); } } remove{staged};
        const auto path = config.filePath("bwm-ui-tray-profile");
        // check-isolated.py runs the whole suite once per package in the same roots.
        QDir(path).removeRecursively();
        ProfileStore::importStage(staged,path);
        ProfileStore profile(path);
        {
            TestCorona corona;
            corona.loadLayout(profile.layoutFile());
            QCOMPARE(corona.containments().size(),1);
            auto *panel = corona.containments().constFirst();
            QCOMPARE(panel->applets().size(),1);
            auto *tray = qobject_cast<Plasma::Containment *>(panel->applets().constFirst());
            QVERIFY(tray);
            QCOMPARE(tray->containmentType(),Plasma::Containment::CustomEmbedded);
            auto *model = tray->property("systemTrayModel").value<QAbstractItemModel *>();
            QVERIFY(model);
            QCOMPARE(model->roleNames().values().contains(QByteArrayLiteral("DataEngineSource")), true);
            QCOMPARE(model->roleNames().values().contains(QByteArrayLiteral("itemType")), true);
            PanelSession session(panel,false);
            const auto getChildRow = [&] {
                const auto rows = session.widgetBackends();
                if (rows.size() != 1) return QVariantMap();
                for (const auto &value : rows.constFirst().toMap().value("embeddedApplets").toList()) {
                    if (value.toMap().value("package").toString() == childId) return value.toMap();
                }
                return QVariantMap();
            };
            QTRY_VERIFY(!getChildRow().isEmpty());
            const auto row = session.widgetBackends().constFirst().toMap();
            QCOMPARE(row.value("package").toString(),"org.kde.plasma.systemtray");
            QCOMPARE(row.value("embeddedInventoryScope").toString(),"live-native-tray-applets");
            Plasma::Applet *child = nullptr;
            const auto childIdInInventory = getChildRow().value("id").toUInt();
            for (auto *candidate : tray->applets()) if (candidate->id() == childIdInInventory) child = candidate;
            QVERIFY(child && !child->failedToLaunch());
            QVERIFY(!getChildRow().value("runtime").toMap().value("operationalVerified").toBool());
            QCOMPARE(session.order().size(),1); // No child is registered as a direct panel widget.
            auto *entry = child->configScheme()->KCoreConfigSkeleton::findItem("caption");
            QVERIFY(entry);entry->setProperty(QStringLiteral("saved inside native tray"));
            QVERIFY(child->configScheme()->save());
            corona.saveLayout(profile.layoutFile());QVERIFY(corona.config()->sync());
        }
        const auto checkpoint = profile.checkpoint();
        QVERIFY(!checkpoint.value("snapshot").toString().isEmpty());
    }
    void nativeTrayChildFreshProcessReadback() {
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));
        ProfileStore profile(config.filePath("bwm-ui-tray-profile"));
        TestCorona corona;
        corona.loadLayout(profile.layoutFile());
        QCOMPARE(corona.containments().size(),1);
        auto *panel = corona.containments().constFirst();
        QCOMPARE(panel->applets().size(),1);
        auto *tray = qobject_cast<Plasma::Containment *>(panel->applets().constFirst());
        QVERIFY(tray);
        const auto findChild = [tray]() -> Plasma::Applet * {
            for (auto *child : tray->applets())
                if (child->pluginMetaData().pluginId() == "org.bwm.r4.tray-child") return child;
            return nullptr;
        };
        QTRY_VERIFY(findChild());
        auto *entry = findChild()->configScheme()->KCoreConfigSkeleton::findItem("caption");
        QVERIFY(entry);
        QCOMPARE(entry->property().toString(),"saved inside native tray");
        PanelSession session(panel,false);
        const auto childListed = [&] {
            for (const auto &value : session.widgetBackends().constFirst().toMap().value("embeddedApplets").toList())
                if (value.toMap().value("package").toString() == "org.bwm.r4.tray-child") return true;
            return false;
        };
        QVERIFY(childListed());
        findChild()->destroy();QTRY_VERIFY(!childListed());
    }
    void previewLoadsAndOpensOriginalConfig() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);
        c->setFormFactor(Plasma::Types::Horizontal);
        auto *a=c->createApplet(qEnvironmentVariable("BWM_TEST_APPLET"));
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(item);
        item->setSize(QSizeF(48,48));
        Catalog catalog;
        auto *action=new QAction("R4 test action",a);action->setObjectName("fixtureAction");action->setCheckable(true);
        QSignalSpy triggered(action,&QAction::triggered);
        auto actions=a->qmlContextualActions();QVERIFY(actions.append);actions.append(&actions,action);
        ConfigurationSession config(a);QVERIFY2(config.error().isEmpty(),qPrintable(config.error()));
        QQmlEngine engine;
        QQmlComponent component(&engine,corona.kPackage().fileUrl("views",QStringLiteral("Preview.qml")));
        auto *object=component.createWithInitialProperties({{"appletItem",QVariant::fromValue(item)},{"applet",QVariant::fromValue(a)},{"configurationSession",QVariant::fromValue(&config)},{"catalog",QVariant::fromValue(&catalog)}});
        auto *root=qobject_cast<QQuickItem*>(object);QVERIFY2(root,qPrintable(component.errorString()));
        QQuickWindow window;window.resize(640,160);root->setParentItem(window.contentItem());root->setSize(QSizeF(640,160));window.show();
        QCoreApplication::processEvents();
        auto *button=findVisual(root,"configureButton");QVERIFY(button);
        QVERIFY(findVisual(root,"getNewButton"));
        QTest::mouseClick(&window,Qt::LeftButton,Qt::NoModifier,button->mapToScene(QPointF(button->width()/2,button->height()/2)).toPoint());
        QTRY_VERIFY(config.view() && config.view()->isVisible());
        click(config.view(),"cancelButton");
        auto *actionsButton=findVisual(root,"actionsButton");QVERIFY(actionsButton);
        QTest::mouseClick(&window,Qt::LeftButton,Qt::NoModifier,actionsButton->mapToScene(QPointF(actionsButton->width()/2,actionsButton->height()/2)).toPoint());
        QQuickItem *menuItem=nullptr;
        QTRY_VERIFY(menuItem=findVisual(window.contentItem(),"fixtureAction"));
        QTRY_VERIFY(menuItem->isVisible());
        QTest::mouseClick(&window,Qt::LeftButton,Qt::NoModifier,menuItem->mapToScene(QPointF(menuItem->width()/2,menuItem->height()/2)).toPoint());
        QTRY_COMPARE(triggered.count(),1);QVERIFY(action->isChecked());
        delete root;
    }
    void originalPanelConfigureActionAndIndependentInstances() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c && !c->failedToLaunch());
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        auto *a=c->createApplet(qEnvironmentVariable("BWM_TEST_APPLET"));QVERIFY(a);
        auto *b=c->createApplet(qEnvironmentVariable("BWM_TEST_APPLET"));QVERIFY(b);
        PanelSession panel(c);
        QSignalSpy opened(&panel,&PanelSession::configurationOpened);
        QQuickWindow window;window.resize(640,48);
        BwmSurface::configurePanel(&window,Qt::BottomEdge,64);
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(root);
        root->setParentItem(window.contentItem());root->setSize(QSizeF(640,48));window.show();
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(item);
        QTRY_VERIFY(item->parentItem() && item->parentItem()->property("isAppletContainer").toBool());
        if(qEnvironmentVariable("BWM_TEST_APPLET")=="AndromedaLauncher") {
            // This package deliberately defines fullRepresentation as its launcher
            // button and creates a separate PlasmaCore.Dialog. Test that real path,
            // not a forced compact fallback wrapped around the launcher button.
            QTRY_VERIFY(item->fullRepresentationItem());
            auto *launcher=item->fullRepresentationItem();
            QWindow *popup=nullptr;
            QTRY_VERIFY(popup=qobject_cast<QWindow*>(launcher->property("dashWindow").value<QObject*>()));
            panel.packageWindows()->refresh();
            QVERIFY2(popup->property("bwmPackageWindowAdapted").toBool(),"Native package Dialog must acquire its layer role before showing");
            QCOMPARE(LayerShellQt::Window::get(popup)->layer(),LayerShellQt::Window::LayerOverlay);
            QVERIFY(!popup->isVisible());QTRY_VERIFY(launcher->width()>0 && launcher->height()>0);
            QTest::mouseClick(&window,Qt::LeftButton,Qt::NoModifier,launcher->mapToScene(QPointF(launcher->width()/2,launcher->height()/2)).toPoint());
            QTRY_VERIFY(popup->isVisible());
            QVERIFY(popup->property("bwmPopupRect").toRect().isValid());
            QVERIFY(!panel.packageWindows()->capabilities().isEmpty());
            QCOMPARE(popup->objectName(),"popupWindow");
            auto *other=PlasmaQuick::AppletQuickItem::itemForApplet(b);QVERIFY(other);
            QTRY_VERIFY(other->fullRepresentationItem());
            auto *otherPopup=qobject_cast<QWindow*>(other->fullRepresentationItem()->property("dashWindow").value<QObject*>());
            QVERIFY(otherPopup && otherPopup!=popup && !otherPopup->isVisible());
            popup->hide();QTRY_VERIFY(!popup->isVisible());
        }
        auto *configure=a->internalAction("configure");QVERIFY(configure && configure->isEnabled());
        configure->trigger();
        QTRY_COMPARE(opened.count(),1);
        auto *session=panel.configuration(a->id());QVERIFY(session);
        QVERIFY2(session->error().isEmpty(),qPrintable(session->error()));
        QTRY_VERIFY(session->view() && session->view()->isVisible());
        configure->trigger();QCOMPARE(panel.configuration(a->id()),session);
        QString key;QQuickItem *page=nullptr;
        for(const auto &category:session->pages()) {
            auto *candidate=category.toMap().value("item").value<QQuickItem*>();
            for(int i=0;i<candidate->metaObject()->propertyCount() && key.isEmpty();++i) {
                auto prop=candidate->metaObject()->property(i);const QString name=QString::fromLatin1(prop.name());
                if(!name.startsWith("cfg_"))continue;
                auto *entry=a->configScheme()->KCoreConfigSkeleton::findItem(name.mid(4));
                if(entry && entry->property().metaType().id()==QMetaType::Bool && prop.isWritable()) {key=name.mid(4);page=candidate;}
            }
        }
        QVERIFY(page && !key.isEmpty());
        const bool original=a->configScheme()->KCoreConfigSkeleton::findItem(key)->property().toBool();
        const auto independent=b->configScheme()->KCoreConfigSkeleton::findItem(key)->property();
        QVERIFY(page->setProperty(qPrintable("cfg_"+key),!original));
        click(session->view(),"applyButton");
        a->configScheme()->load();QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem(key)->property().toBool(),!original);
        QCOMPARE(b->configScheme()->KCoreConfigSkeleton::findItem(key)->property(),independent);
        click(session->view(),"cancelButton");QTRY_VERIFY(!session->view());
        configure->trigger();
        QTRY_VERIFY(panel.configuration(a->id())->view() && panel.configuration(a->id())->view()->isVisible());
        QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem(key)->property().toBool(),!original);
        click(panel.configuration(a->id())->view(),"cancelButton");
        QVERIFY(!panel.configure(0));
        // The panel has a schema but no applet categories: never offer silent Defaults/Apply.
        QVERIFY(panel.configure(c->id()));
        auto *panelConfig=panel.configuration(c->id());QVERIFY(!panelConfig->error().isEmpty());
        QVERIFY(!panelConfig->apply());click(panelConfig->view(),"cancelButton");
        const uint removedId=a->id();
        QVERIFY(panel.configure(removedId));
        QPointer<ConfigurationSession> removedSession=panel.configuration(removedId);
        QTRY_VERIFY(removedSession->view() && removedSession->view()->isVisible());
        delete a; // Removing a widget must also release its open configuration view.
        QTRY_VERIFY(!removedSession);
        QVERIFY(!panel.configuration(removedId));QVERIFY(!panel.configure(removedId));
        QVERIFY(b->configScheme());
    }
    void originalShellPanelView() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        auto *a=c->createApplet("org.bwm.r4.shared-config");QVERIFY(a);
        QStringList scriptErrors;
        PanelViewHost view(&corona);
        connect(view.engine().get(),&QQmlEngine::warnings,&view,[&scriptErrors](const QList<QQmlError> &errors){
            for(const auto &e:errors)if(e.description().contains("ReferenceError") || e.description().contains("TypeError") || e.description().contains("Unable to assign [undefined]"))scriptErrors.append(e.toString());
        });
        QVERIFY2(view.load(c),qPrintable(view.error()));view.setLengthMode(PanelViewEnums::Custom);view.show();
        auto *root=view.rootObject();QVERIFY(root);
        QVERIFY(view.source().toString().endsWith("/contents/views/Panel.qml"));
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(item);
        QCOMPARE(root->property("containment").value<QQuickItem*>(),item);
        QTRY_VERIFY(item->parentItem() && item->width()>0 && item->height()>0);
        QTRY_COMPARE(view.width(),640);QCOMPARE(view.height(),48);QCOMPARE(item->height(),48);
        QVERIFY(view.setLengthRange(320,320));QTRY_COMPARE(view.width(),320);
        QVERIFY(!view.setLengthRange(800,200));QCOMPARE(view.width(),320);
        QVERIFY(view.setLengthRange(640,640));QTRY_COMPARE(view.width(),640);
        QVERIFY(!view.capabilities().value("adaptiveWindowBackend").toBool());
        QVERIFY(!view.capabilities().value("compositorBlur").toBool());
        const int opacity=view.opacityMode();view.setOpacityMode(PanelViewEnums::Adaptive);
        QCOMPARE(view.opacityMode(),opacity);QVERIFY(!view.error().isEmpty());
        view.setOpacityMode(PanelViewEnums::Opaque);QVERIFY(view.error().isEmpty());QTRY_VERIFY(root->property("isOpaque").toBool());
        view.setOpacityMode(PanelViewEnums::Translucent);QTRY_VERIFY(root->property("isTransparent").toBool());
        view.setFloating(true);QTRY_COMPARE(root->property("floatingness").toDouble(),1.0);
        QTRY_VERIFY(view.height()>view.thickness());QCOMPARE(item->height(),view.thickness());
        QCOMPARE(view.enabledBorders(),int(KSvg::FrameSvg::AllBorders));
        view.setFloating(false);QTRY_COMPARE(root->property("floatingness").toDouble(),0.0);QTRY_COMPARE(view.height(),view.thickness());
        QCOMPARE(view.enabledBorders(),int(KSvg::FrameSvg::AllBorders & ~KSvg::FrameSvg::BottomBorder));
        view.setThickness(36);QTRY_VERIFY(view.thickness()>=36);QTRY_COMPARE(item->height(),view.thickness());
        view.setFloatingApplets(true);
        QTRY_VERIFY(c->containmentDisplayHints().testFlag(Plasma::Types::ContainmentPrefersFloatingApplets));
        auto *session=view.panelSession();QVERIFY(session);QSignalSpy configured(session,&PanelSession::configurationOpened);
        a->internalAction("configure")->trigger();QTRY_COMPARE(configured.count(),1);
        auto *config=session->configuration(a->id());QVERIFY(config && config->view());
        QTRY_VERIFY(config->view()->isVisible());click(config->view(),"cancelButton");
        QTRY_VERIFY(!config->view());
        QTRY_VERIFY(!view.grabWindow().isNull());
        const QPoint sample(view.width()-10,view.height()/2);
        QTRY_VERIFY(view.grabWindow().pixelColor(sample).alpha()>0);
        c->setBackgroundHints(Plasma::Types::NoBackground);
        QTRY_VERIFY(view.grabWindow().pixelColor(sample).alpha()==0);
        QVERIFY2(scriptErrors.isEmpty(),qPrintable(scriptErrors.join('\n')));
    }
    void nativePanelThemeAndEdges() {
        Plasma::Theme theme;
        struct RestoreTheme {Plasma::Theme &theme;QString previous;~RestoreTheme(){theme.setThemeName(previous);}} restore{theme,theme.themeName()};
        theme.setThemeName("org.bwm.r4.panel-a");
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        QVERIFY(c->createApplet(qEnvironmentVariable("BWM_TEST_APPLET")));
        PanelViewHost view(&corona);QVERIFY2(view.load(c),qPrintable(view.error()));view.setLengthMode(PanelViewEnums::Custom);view.show();
        auto *root=view.rootObject();QVERIFY(root);
        struct Edge {Plasma::Types::Location location;bool vertical;const char *prefix;const char *color;int disabled;};
        const Edge edges[]={
            {Plasma::Types::BottomEdge,false,"south","#22aa55",KSvg::FrameSvg::BottomBorder},
            {Plasma::Types::TopEdge,false,"north","#2255aa",KSvg::FrameSvg::TopBorder},
            {Plasma::Types::LeftEdge,true,"west","#cc6622",KSvg::FrameSvg::LeftBorder},
            {Plasma::Types::RightEdge,true,"east","#8844cc",KSvg::FrameSvg::RightBorder}};
        const auto renderedColor=[&] {
            const auto image=view.grabWindow();if(image.isNull())return QColor();
            return image.pixelColor(view.width()>view.height() ? QPoint(view.width()-10,view.height()/2) : QPoint(view.width()/2,view.height()-10));
        };
        const auto nearColor=[&](const QColor &expected){
            const auto actual=renderedColor();
            return actual.isValid() && actual.alpha()>250 && std::abs(actual.red()-expected.red())<=4 &&
                std::abs(actual.green()-expected.green())<=4 && std::abs(actual.blue()-expected.blue())<=4;
        };
        std::function<bool(QQuickItem*,const QString&)> hasVisiblePrefix=[&](QQuickItem *item,const QString &prefix){
            if(item->isVisible() && item->property("imagePath").toString()=="widgets/panel-background" && item->property("usedPrefix").toString()==prefix)return true;
            for(auto *child:item->childItems())if(hasVisiblePrefix(child,prefix))return true;return false;
        };
        for(const auto &edge:edges) {
            c->setLocation(edge.location);c->setFormFactor(edge.vertical ? Plasma::Types::Vertical : Plasma::Types::Horizontal);
            QTRY_COMPARE(view.size(),edge.vertical ? QSize(48,640) : QSize(640,48));
            QTRY_VERIFY(hasVisiblePrefix(root,QString::fromLatin1(edge.prefix)));
            QCOMPARE(view.enabledBorders(),int(KSvg::FrameSvg::AllBorders)&~edge.disabled);
            QTRY_VERIFY2(nearColor(QColor(edge.color)),qPrintable(renderedColor().name(QColor::HexArgb)));
        }
        c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);
        QTRY_COMPARE(view.size(),QSize(640,48));QTRY_VERIFY(nearColor(QColor("#22aa55")));
        theme.setThemeName("org.bwm.r4.panel-b");QTRY_VERIFY(nearColor(QColor("#dd2277")));
        view.setFloating(true);QTRY_COMPARE(root->property("floatingness").toDouble(),1.0);
        QTRY_COMPARE(view.height(),52);QCOMPARE(view.thickness(),48);
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(item);
        QTRY_COMPARE(item->width(),636);QCOMPARE(item->height(),48);
    }
    void nativePanelWidgetLifecycle() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        // Use a single native layout owner, as the production entry point does. Exporting
        // saveLayout to another filename copies containment state under Configuration.
        QFile::remove(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-panel-api-test"));
        corona.loadLayout("bwm-panel-api-test");
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c && !c->failedToLaunch());
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        PanelSession session(c);QSignalSpy changes(&session,&PanelSession::changed);
        QQuickWindow window;window.resize(640,48);window.show();
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(root);
        root->setParentItem(window.contentItem());root->setSize(QSizeF(640,48));
        session.bindPanelItem(root);QVERIFY(session.error().isEmpty());
        QVERIFY(session.panelInfo().value("canReorder").toBool());
        QVERIFY(!session.addWidget("org.bwm.r4.missing"));
        QVERIFY(!session.addWidget("org.kde.panel"));QCOMPARE(session.widgets().size(),0);
        const uint first=session.addWidget("org.bwm.r4.shared-config");QVERIFY(first);
        const uint removed=session.addWidget("org.bwm.r4.shared-config");QVERIFY(removed && removed!=first);
        const QString selected=qEnvironmentVariable("BWM_TEST_APPLET");
        const uint selectedId=session.addWidget(selected);QVERIFY2(selectedId,qPrintable(session.error()));
        QTRY_COMPARE(session.widgets().size(),3);QTRY_VERIFY(!changes.isEmpty());
        auto find=[&](uint id)->Plasma::Applet*{for(auto *a:c->applets())if(a->id()==id)return a;return nullptr;};
        auto *a=find(first);auto *b=find(removed);QVERIFY(a && b);
        auto *aItem=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(aItem);
        QTRY_VERIFY(aItem->parentItem() && aItem->parentItem()->property("isAppletContainer").toBool());
        const auto original=session.order();
        QVERIFY(!session.requestOrder({first,first,selectedId}));
        QVERIFY(!session.requestOrder({first,removed}));
        QVERIFY(!session.requestOrder({first,removed,c->id()}));
        QVERIFY(!session.requestOrder({double(first)+0.25,removed,selectedId}));
        QCOMPARE(session.order(),original);
        const QVariantList desired{selectedId,removed,first};
        QVERIFY2(session.requestOrder(desired),qPrintable(session.error()));
        QTRY_COMPARE(session.order(),desired);
        auto *orderEntry=c->configScheme()->KCoreConfigSkeleton::findItem("AppletOrder");QVERIFY(orderEntry);
        QTRY_COMPARE(orderEntry->property().toString(),QString("%1;%2;%3").arg(selectedId).arg(removed).arg(first));
        c->setImmutability(Plasma::Types::UserImmutable);
        QVERIFY(!session.panelInfo().value("canReorder").toBool());
        QVERIFY(!session.addWidget(selected));QVERIFY(!session.removeWidget(first));QVERIFY(!session.requestOrder(original));
        c->setImmutability(Plasma::Types::Mutable);
        a->setImmutability(Plasma::Types::UserImmutable);QVERIFY(!session.removeWidget(first));QVERIFY(!session.requestOrder(original));
        a->setImmutability(Plasma::Types::Mutable);
        QVERIFY(!session.removeWidget(c->id()));
        auto *foreign=corona.createContainment("null");QVERIFY(foreign);
        auto *other=foreign->createApplet("org.bwm.r4.shared-config");QVERIFY(other);
        QVERIFY(!session.removeWidget(other->id()));QVERIFY(!session.configure(other->id()));
        session.bindPanelItem(PlasmaQuick::AppletQuickItem::itemForApplet(other));
        QVERIFY(!session.error().isEmpty());QVERIFY(session.panelInfo().value("viewBound").toBool());
        QVERIFY(session.configure(removed));QPointer<ConfigurationSession> config=session.configuration(removed);
        QVERIFY(config && config->view());
        QPointer<Plasma::Applet> gone=b;
        QVERIFY(session.removeWidget(removed));QVERIFY(!config);
        QVERIFY(!session.removeWidget(removed));QVERIFY(!session.configure(removed));
        QTRY_VERIFY(!gone);QTRY_COMPARE(session.widgets().size(),2);
        QTRY_COMPARE(orderEntry->property().toString(),QString("%1;%2").arg(selectedId).arg(first));
        const uint added=session.addWidget("org.bwm.r4.shared-config");QVERIFY(added && added!=removed);
        const QVariantList finalOrder{added,first,selectedId};
        QTRY_COMPARE(session.widgets().size(),3);
        QVERIFY(session.requestOrder(finalOrder));QTRY_COMPARE(session.order(),finalOrder);
        a->configScheme()->KCoreConfigSkeleton::findItem("caption")->setProperty(QStringLiteral("panel API saved"));
        QVERIFY(a->configScheme()->save());
        // Save through Corona; removed applet instance/configuration must not come back.
        QPointer<Plasma::Containment> foreignGone=foreign;foreign->destroy();QTRY_VERIFY(!foreignGone);
        corona.saveLayout("bwm-panel-api-test");corona.config()->sync();
        KConfig saved("bwm-panel-api-test",KConfig::SimpleConfig);
        const QString expectedOrder=QString("%1;%2;%3").arg(added).arg(first).arg(selectedId);
        const auto savedOrder=KConfigGroup(&saved,"Containments").group(QString::number(c->id())).group("General").readEntry("AppletOrder",QString());
        QCOMPARE(savedOrder,expectedOrder);
        QVERIFY(!KConfigGroup(&saved,"Containments").group(QString::number(c->id())).group("Configuration").hasGroup("Applets"));
        KConfigGroup applets=KConfigGroup(&saved,"Containments").group(QString::number(c->id())).group("Applets");
        QVERIFY(!applets.hasGroup(QString::number(removed)));
        QCOMPARE(applets.groupList().size(),3);
    }
    void nativePanelApiFreshProcessReadback() {
        KConfig disk("bwm-panel-api-test",KConfig::SimpleConfig);
        const auto panelGroups=KConfigGroup(&disk,"Containments").groupList();QCOMPARE(panelGroups.size(),1);
        const auto diskOrder=KConfigGroup(&disk,"Containments").group(panelGroups.first()).group("General").readEntry("AppletOrder",QString());
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout("bwm-panel-api-test");QCOMPARE(corona.containments().size(),1);
        auto *c=corona.containments().first();PanelSession session(c);
        QCOMPARE(c->configScheme()->KCoreConfigSkeleton::findItem("AppletOrder")->property().toString(),diskOrder);
        QCOMPARE(session.widgets().size(),3);
        const auto order=session.order();QCOMPARE(order.size(),3);
        QCOMPARE(session.widgets()[0].toMap().value("package").toString(),"org.bwm.r4.shared-config");
        QCOMPARE(session.widgets()[1].toMap().value("package").toString(),"org.bwm.r4.shared-config");
        QCOMPARE(session.widgets()[2].toMap().value("package").toString(),qEnvironmentVariable("BWM_TEST_APPLET"));
        for(auto *a:c->applets())if(a->id()==order[1].toUInt())
            QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("caption")->property().toString(),"panel API saved");
        QQuickWindow window;window.resize(640,48);window.show();
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(root);
        root->setParentItem(window.contentItem());root->setSize(QSizeF(640,48));session.bindPanelItem(root);
        QTRY_COMPARE(session.order(),order);
        qreal previous=-1;
        for(const auto &id:order) {
            Plasma::Applet *a=nullptr;for(auto *candidate:c->applets())if(candidate->id()==id.toUInt())a=candidate;
            QVERIFY(a);auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(item);
            QTRY_VERIFY(item->parentItem() && item->parentItem()->property("isAppletContainer").toBool());
            QTRY_VERIFY(item->width()>0);
            const qreal x=item->mapToItem(root,QPointF()).x();QVERIFY(x>=previous-0.5);previous=x+item->width();
        }
    }
    void nativeContextualActionsRejectStaleAndForeignHandles() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);PanelSession session(c);
        const uint first=session.addWidget("org.bwm.r4.shared-config"),second=session.addWidget("org.bwm.r4.shared-config");
        QVERIFY(first && second);
        Plasma::Applet *a=nullptr;for(auto *candidate:c->applets())if(candidate->id()==first)a=candidate;QVERIFY(a);
        QAction toggle("Innocent test",a);toggle.setCheckable(true);
        QSignalSpy fired(&toggle,&QAction::triggered),updates(&session,&PanelSession::actionsChanged);
        auto list=a->qmlContextualActions();list.append(&list,&toggle);
        const auto snapshot=session.widgetActions(first);QCOMPARE(snapshot.size(),1);
        const QString token=snapshot[0].toMap().value("token").toString();QVERIFY(!token.isEmpty());
        QCOMPARE(session.widgetActions(first)[0].toMap().value("token").toString(),token);
        QVERIFY(!session.triggerAction(second,token));QCOMPARE(fired.count(),0);
        QVERIFY(session.triggerAction(first,token));QCOMPARE(fired.count(),1);QVERIFY(toggle.isChecked());
        QVERIFY(!updates.isEmpty());
        toggle.setEnabled(false);QVERIFY(!session.triggerAction(first,token));toggle.setEnabled(true);
        toggle.setVisible(false);QVERIFY(!session.triggerAction(first,token));toggle.setVisible(true);
        list.clear(&list);QVERIFY(!session.triggerAction(first,token));
        list.append(&list,&toggle);QVERIFY(session.triggerAction(first,token));QCOMPARE(fired.count(),2);
        QMenu menu;auto *submenu=menu.addAction("Nested harmless action");
        QSignalSpy nested(submenu,&QAction::triggered);
        list.append(&list,menu.menuAction());
        const auto tree=session.widgetActions(first);
        const QString menuToken=tree[1].toMap().value("token").toString();
        const QString childToken=tree[1].toMap().value("submenu").toList()[0].toMap().value("token").toString();
        QVERIFY(!session.triggerAction(first,menuToken));
        menu.menuAction()->setEnabled(false);QVERIFY(!session.triggerAction(first,childToken));
        menu.menuAction()->setEnabled(true);QVERIFY(session.triggerAction(first,childToken));QCOMPARE(nested.count(),1);
        delete submenu;QVERIFY(!session.triggerAction(first,childToken));
        QSignalSpy refreshed(a,&Plasma::Applet::contextualActionsAboutToShow);
        session.widgetActions(first);QCOMPARE(refreshed.count(),1);
        updates.clear();session.widgetActions(first,false);
        QCOMPARE(refreshed.count(),1);QCOMPARE(updates.count(),0);
        auto *generated=new QAction("Created when opening the menu",a);
        QSignalSpy generatedTriggered(generated,&QAction::triggered);
        connect(a,&Plasma::Applet::contextualActionsAboutToShow,a,[a,generated]{
            auto actions=a->qmlContextualActions();actions.clear(&actions);actions.append(&actions,generated);
        });
        const auto dynamic=session.widgetActions(first);QCOMPARE(dynamic.size(),1);
        QVERIFY(!session.triggerAction(first,token));
        QVERIFY(session.triggerAction(first,dynamic[0].toMap().value("token").toString()));
        QCOMPARE(generatedTriggered.count(),1);
        QVERIFY(session.removeWidget(first));QVERIFY(!session.triggerAction(first,token));
        QTRY_VERIFY(!session.configure(first));
    }
    void nativeGeometryUsesTheViewOutput() {
        QQuickWindow window;
        auto corona=std::make_unique<ViewCorona>();
        corona->setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona->createContainment("org.kde.panel");QVERIFY(c);
        QCOMPARE(corona->screenForContainment(c),-1);
        corona->bind(c,&window);
        const int screen=QGuiApplication::screens().indexOf(window.screen());
        QCOMPARE(corona->numScreens(),QGuiApplication::screens().size());
        QCOMPARE(corona->screenForContainment(c),screen);
        QCOMPARE(c->screenGeometry().toRect(),window.screen()->geometry());
        QCOMPARE(corona->availableScreenRect(screen),window.screen()->availableGeometry());
        QVERIFY(corona->screenGeometry(-1).contains(window.screen()->geometry()));
        QVERIFY(corona->screenGeometry(corona->numScreens()).isEmpty());
        corona.reset(); // Regression: base Corona deletes containments after derived members.
    }
    void packageWindowOwnershipAndPreSurfaceBoundary() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);
        auto *a=c->createApplet(qEnvironmentVariable("BWM_TEST_APPLET"));QVERIFY(a);
        QQuickWindow window;window.resize(300,48);BwmSurface::configurePanel(&window,Qt::BottomEdge);
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(item);
        item->setParentItem(window.contentItem());item->setSize({48,48});
        QQmlComponent component(qmlEngine(item));
        component.setData("import QtQuick\nimport org.kde.plasma.core as Core\nCore.Dialog { objectName: \"unknown-package-dialog\"; mainItem: Item { implicitWidth: 120; implicitHeight: 80 } }",QUrl());
        auto create=[&]{return std::unique_ptr<PlasmaQuick::Dialog>(qobject_cast<PlasmaQuick::Dialog*>(component.create(qmlContext(item))));};
        auto owned=create();QVERIFY2(owned,qPrintable(component.errorString()));
        auto late=create();QVERIFY(late);late->show();
        auto output=create();QVERIFY(output);output->setOutputOnly(true);
        auto notification=create();QVERIFY(notification);notification->setType(PlasmaQuick::Dialog::Notification);
        notification->setPosition({30,40}); // Requested by the package (no visualParent).
        QQmlComponent plainComponent(qmlEngine(item));
        plainComponent.setData("import QtQuick\nWindow { objectName: \"unknown-plain-window\"; visible: false }",QUrl());
        std::unique_ptr<QObject> plain(plainComponent.create(qmlContext(item)));QVERIFY(plain);
        PlasmaQuick::Dialog unrelated;
        PackageWindows windows(c);windows.refresh();
        QVERIFY(owned->property("bwmPackageWindowAdapted").toBool());
        QVERIFY(!late->property("bwmPackageWindowAdapted").toBool());
        // Output-only and Notification Dialogs get an overlay role without keyboard focus
        // instead of becoming xdg toplevels (Andromeda's floating avatar, verified in Hyprland).
        for(auto *quiet:{output.get(),notification.get()}) {
            QVERIFY(quiet->property("bwmPackageWindowAdapted").toBool());
            QVERIFY(quiet->property("bwmPackageWindowNonInteractive").toBool());
            auto *role=LayerShellQt::Window::get(quiet);
            QCOMPARE(role->keyboardInteractivity(),LayerShellQt::Window::KeyboardInteractivityNone);
            QCOMPARE(role->layer(),LayerShellQt::Window::LayerOverlay);
        }
        QVERIFY(!owned->property("bwmPackageWindowNonInteractive").toBool());
        QCOMPARE(LayerShellQt::Window::get(owned.get())->keyboardInteractivity(),LayerShellQt::Window::KeyboardInteractivityOnDemand);
        QVERIFY(!unrelated.property("bwmPackageWindowAdapted").toBool());
        QVERIFY(!plain->property("bwmPackageWindowAdapted").toBool());
        bool sawLate=false,sawQuiet=false,sawPlain=false;
        for(const auto &v:windows.capabilities()) {
            const auto record=v.toMap();QCOMPARE(record.value("appletId").toUInt(),a->id());
            sawLate=sawLate || record.value("status")=="requires-pre-surface-registration";
            sawQuiet=sawQuiet || (record.value("status")=="layer-role-prepared" && record.value("nonInteractive").toBool());
            sawPlain=sawPlain || record.value("status")=="requires-explicit-window-type-adapter";
            QVERIFY(!record.value("waylandVerified").toBool());
        }
        QVERIFY(sawLate && sawQuiet && sawPlain);
        const int count=windows.capabilities().size();owned.reset();
        QCOMPARE(windows.capabilities().size(),count-1);
        late->hide();
    }
    void moduleConfigurationTransactions() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QFile::remove(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-module-config-test"));
        corona.loadLayout("bwm-module-config-test");
        auto *c=corona.createContainment("null");QVERIFY(c);
        auto *a=c->createApplet("org.bwm.r4.module-config"),*b=c->createApplet("org.bwm.r4.module-config");QVERIFY(a && b);
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(item);
        QQuickWindow window;window.resize(300,64);window.show();
        item->setParentItem(window.contentItem());item->setSize(QSizeF(300,64));item->setPreferredRepresentation(item->fullRepresentation());
        QTRY_VERIFY(item->fullRepresentationItem());
        auto *scheme=a->configScheme();
        scheme->KCoreConfigSkeleton::findItem("hidden")->setProperty(QStringLiteral("keep until defaults"));QVERIFY(scheme->save());
        corona.saveLayout("bwm-module-config-test");corona.config()->sync();
        const auto path=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-module-config-test");
        auto bytes=[&]{QFile file(path);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const auto baseline=bytes();QVERIFY(!baseline.isEmpty());
        {
            ConfigurationSession session(a);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QCOMPARE(session.pages().size(),2);
            QCOMPARE(session.pages()[0].toMap().value("loader").toString(),"source");
            QCOMPARE(session.pages()[1].toMap().value("loader").toString(),"module");
            auto *file=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *module=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QCOMPARE(file->property("completionGreeting").toString(),"hello");
            QCOMPARE(module->property("completionGreeting").toString(),"hello");
            QCOMPARE(module->property("completionAmount").toInt(),3);
            QCOMPARE(module->property("completionTitle").toString(),"Module category");
            QCOMPARE(module->property("owner").value<QObject*>(),static_cast<QObject*>(a));
            QVERIFY(!module->property("localizedText").toString().isEmpty());
            QCOMPARE(module->property("cfg_amountDefault").toInt(),3);QVERIFY(!module->property("cfg_amountImmutable").toBool());
            session.show();QTRY_VERIFY(session.view()->isVisible());click(session.view(),"categoryButton_1");
            QVERIFY(module->isVisible());QVERIFY(module->setProperty("cfg_greeting",QStringLiteral("cancel this")));
            QCOMPARE(file->property("cfg_greeting").toString(),"cancel this");
            QVERIFY(module->setProperty("cfg_amount",15));QVERIFY(session.dirty());QCOMPARE(bytes(),baseline);
            click(session.view(),"cancelButton");QCOMPARE(bytes(),baseline);
        }
        {
            ConfigurationSession session(a);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            auto *file=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *module=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QCOMPARE(module->property("completionGreeting").toString(),"hello");
            QVERIFY(file->setProperty("cfg_greeting",QStringLiteral("Module persisted")));
            QCOMPARE(module->property("cfg_greeting").toString(),"Module persisted");QVERIFY(module->setProperty("cfg_amount",17));
            session.show();QTRY_VERIFY(session.view()->isVisible());click(session.view(),"applyButton");
            QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));QVERIFY(!session.dirty());
            QTRY_COMPARE(item->fullRepresentationItem()->property("text").toString(),"Module persisted:17");
            QCOMPARE(b->configScheme()->KCoreConfigSkeleton::findItem("greeting")->property().toString(),"hello");
            const auto committed=bytes();click(session.view(),"defaultsButton");QVERIFY(session.dirty());
            QCOMPARE(module->property("cfg_greeting").toString(),"hello");QCOMPARE(module->property("cfg_amount").toInt(),3);
            QCOMPARE(bytes(),committed);click(session.view(),"cancelButton");QCOMPARE(bytes(),committed);
        }
        {
            ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
            auto *module=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QCOMPARE(module->property("completionGreeting").toString(),"Module persisted");QCOMPARE(module->property("completionAmount").toInt(),17);
            session.defaults();QVERIFY(session.apply());
            QCOMPARE(scheme->KCoreConfigSkeleton::findItem("hidden")->property().toString(),"hidden default");
            QVERIFY(module->setProperty("cfg_greeting",QStringLiteral("Module persisted")));QVERIFY(module->setProperty("cfg_amount",17));QVERIFY(session.apply());
        }
        corona.saveLayout("bwm-module-config-test");corona.config()->sync();
    }
    void moduleConfigurationFreshProcessReadback() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout("bwm-module-config-test");QCOMPARE(corona.containments().size(),1);
        int edited=0,instances=0;
        for(auto *a:corona.containments().first()->applets()) {
            QCOMPARE(a->pluginMetaData().pluginId(),"org.bwm.r4.module-config");++instances;
            ConfigurationSession session(a);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QCOMPARE(session.pages().size(),2);
            auto *module=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            const auto greeting=module->property("completionGreeting").toString();
            if(greeting=="Module persisted"){++edited;QCOMPARE(module->property("completionAmount").toInt(),17);}
            else{QCOMPARE(greeting,"hello");QCOMPARE(module->property("completionAmount").toInt(),3);}
            QCOMPARE(module->property("owner").value<QObject*>(),static_cast<QObject*>(a));QVERIFY(!session.dirty());
        }
        QCOMPARE(instances,2);QCOMPARE(edited,1);
    }
    void moduleConfigurationDescriptors_data() {
        QTest::addColumn<QString>("suffix");QTest::addColumn<QString>("errorFragment");
        QTest::newRow("missing module")<<QString("missing-module")<<QString("org.bwm.r4.missing");
        QTest::newRow("missing component")<<QString("missing-component")<<QString("MissingPage");
        QTest::newRow("root is not Item")<<QString("non-item")<<QString("must be an Item");
        QTest::newRow("required unknown property")<<QString("required-extra")<<QString("unrelated");
        QTest::newRow("incomplete module pair")<<QString("incomplete")<<QString("both a QML module");
        QTest::newRow("KCM still blocked")<<QString("kcm")<<QString("KCM adapter");
        QTest::newRow("incomplete pair falls back to source")<<QString("fallback")<<QString();
        QTest::newRow("absolute native source path")<<QString("absolute")<<QString();
    }
    void moduleConfigurationDescriptors() {
        QFETCH(QString,suffix);QFETCH(QString,errorFragment);
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);
        auto *a=c->createApplet("org.bwm.r4.module-"+suffix);QVERIFY(a);
        ConfigurationSession session(a);
        if(errorFragment.isEmpty()) {
            QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));QCOMPARE(session.pages().size(),1);
            QCOMPARE(session.pages()[0].toMap().value("loader").toString(),"source");
            QCOMPARE(session.pages()[0].toMap().value("item").value<QQuickItem*>()->property("completionGreeting").toString(),"hello");
        } else {
            QVERIFY2(session.error().contains(errorFragment),qPrintable(session.error()));
            QVERIFY(!session.apply());session.defaults();QVERIFY(!session.apply());
            QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("greeting")->property().toString(),"hello");
        }
    }
    void sharedConfigurationTransactions() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);
        auto *a=c->createApplet("org.bwm.r4.shared-config"),*b=c->createApplet("org.bwm.r4.shared-config");
        QVERIFY(a && b && a->configScheme() && b->configScheme());
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY(item);
        QQuickWindow panel;panel.resize(300,64);panel.show();
        item->setParentItem(panel.contentItem());item->setSize(QSizeF(300,64));
        item->setPreferredRepresentation(item->fullRepresentation());
        QTRY_VERIFY(item->fullRepresentationItem());
        auto *scheme=a->configScheme();
        auto entry=[&](const QString &key){return scheme->KCoreConfigSkeleton::findItem(key);};
        entry("unexposed")->setProperty(QStringLiteral("keep until defaults"));QVERIFY(scheme->save());
        corona.saveLayout("bwm-shared-config-test");
        {
            KConfig external(scheme->config()->name(),KConfig::SimpleConfig);
            KConfigGroup group(&external,entry("amount")->group());
            group.writeEntry("ForeignKey","preserved");external.sync();
        }
        const QString configPath=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath(scheme->config()->name());
        auto bytes=[&]{QFile file(configPath);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const QByteArray baseline=bytes();QVERIFY2(!baseline.isEmpty(),qPrintable(configPath));
        {
            ConfigurationSession session(a);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QCOMPARE(session.pages().size(),2);session.show();QTRY_VERIFY(session.view()->isVisible());
            auto *first=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            auto *parent=first->parentItem();QVERIFY(parent);
            QSignalSpy pagesChanged(&session,&ConfigurationSession::pagesChanged);
            QVERIFY(first->property("cfg_enabledDefault").toBool());
            QVERIFY(!first->property("cfg_enabledImmutable").toBool());
            auto *toggle=findVisual(first,"sharedToggle");QVERIFY(toggle);
            QTest::mouseClick(session.view(),Qt::LeftButton,Qt::NoModifier,toggle->mapToScene(QPointF(toggle->width()/2,toggle->height()/2)).toPoint());
            QVERIFY(!first->property("cfg_enabled").toBool());
            QVERIFY(!second->property("cfg_enabled").toBool());QVERIFY(session.dirty());
            click(session.view(),"categoryButton_1");
            QVERIFY(second->isVisible());
            for(int value=4;value<=60;++value) {
                QVERIFY(second->setProperty("cfg_amount",value));
                QCOMPARE(first->property("cfg_amount").toInt(),value);
            }
            QCoreApplication::processEvents();
            QCOMPARE(pagesChanged.count(),0);QCOMPARE(first->parentItem(),parent);
            QCOMPARE(bytes(),baseline);QCOMPARE(entry("amount")->property().toInt(),3);
            QCOMPARE(b->configScheme()->KCoreConfigSkeleton::findItem("amount")->property().toInt(),3);
            QVERIFY(first->setProperty("cfg_amount",3));
            QVERIFY(second->setProperty("cfg_enabled",true));QVERIFY(!session.dirty());
            QVERIFY(first->setProperty("cfg_caption",QStringLiteral("cancel this")));
            click(session.view(),"cancelButton");
            QCOMPARE(bytes(),baseline);
        }
        {
            ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
            session.show();QTRY_VERIFY(session.view()->isVisible());
            auto *first=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QCOMPARE(first->property("cfg_caption").toString(),"initial");
            QVERIFY(first->setProperty("cfg_caption",QStringLiteral("applied caption")));
            QVERIFY(first->setProperty("cfg_amount",42));
            QCOMPARE(second->property("cfg_amount").toInt(),42);
            click(session.view(),"applyButton");QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QVERIFY(!session.dirty());QCOMPARE(entry("amount")->property().toInt(),42);
            QTRY_COMPARE(item->fullRepresentationItem()->property("text").toString(),"applied caption");
            QCOMPARE(entry("unexposed")->property().toString(),"keep until defaults");
            const auto committed=bytes();
            click(session.view(),"defaultsButton");
            QCOMPARE(first->property("cfg_amount").toInt(),3);QCOMPARE(second->property("cfg_amount").toInt(),3);
            QCOMPARE(bytes(),committed);QVERIFY(session.dirty());
            click(session.view(),"cancelButton");QCOMPARE(bytes(),committed);
        }
        {
            ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
            session.defaults();QVERIFY(session.dirty());QVERIFY(session.apply());QVERIFY(!session.dirty());
            QCOMPARE(entry("unexposed")->property().toString(),"hidden default");
            QCOMPARE(entry("amount")->property().toInt(),3);
            auto *first=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QVERIFY(second->setProperty("cfg_amount",42));
            QVERIFY(first->setProperty("cfg_caption",QStringLiteral("applied caption")));
            QVERIFY(session.apply());
        }
        {
            ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
            auto *first=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QCOMPARE(first->property("cfg_amount").toInt(),42);QCOMPARE(second->property("cfg_amount").toInt(),42);
            QVERIFY(second->setProperty("cfg_amount",50));
            KConfig external(scheme->config()->name(),KConfig::SimpleConfig);
            KConfigGroup group(&external,entry("amount")->group());group.writeEntry("amount",43);external.sync();
            QVERIFY(!session.apply());QVERIFY(!session.error().isEmpty());
            external.reparseConfiguration();QCOMPARE(group.readEntry("amount",0),43);
        }
        {
            ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
            auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            QVERIFY(second->setProperty("cfg_amount",42));QVERIFY(session.apply());
        }
        KConfig reread(scheme->config()->name(),KConfig::SimpleConfig);
        QCOMPARE(KConfigGroup(&reread,entry("amount")->group()).readEntry("ForeignKey",QString()),"preserved");
        QCOMPARE(b->configScheme()->KCoreConfigSkeleton::findItem("caption")->property().toString(),"initial");
        corona.saveLayout("bwm-shared-config-test");
    }
    void sharedConfigurationConstraintRejected() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        auto *c=corona.createContainment("null");QVERIFY(c);
        auto *a=c->createApplet("org.bwm.r4.shared-config");QVERIFY(a && a->configScheme());
        ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
        auto *first=session.pages()[0].toMap().value("item").value<QQuickItem*>();
        auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
        auto *spin=findVisual(second,"sharedAmount");QVERIFY(spin);
        QVERIFY(spin->setProperty("to",10));QVERIFY(first->setProperty("cfg_amount",20));
        QCOMPARE(second->property("cfg_amount").toInt(),10);
        QVERIFY(!session.error().isEmpty());QVERIFY(!session.apply());
        QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("amount")->property().toInt(),3);
    }
    void sharedConfigurationFreshProcessReadback() {
        TestCorona corona;
        corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout("bwm-shared-config-test");
        int instances=0,edited=0;
        for(auto *containment:corona.containments())for(auto *applet:containment->applets()) {
            if(applet->pluginMetaData().pluginId()!="org.bwm.r4.shared-config")continue;
            ++instances;
            ConfigurationSession session(applet);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            auto *first=session.pages()[0].toMap().value("item").value<QQuickItem*>();
            auto *second=session.pages()[1].toMap().value("item").value<QQuickItem*>();
            const auto caption=first->property("cfg_caption").toString();
            if(caption=="applied caption") {
                ++edited;QCOMPARE(first->property("cfg_amount").toInt(),42);QCOMPARE(second->property("cfg_amount").toInt(),42);
            } else {
                QCOMPARE(caption,"initial");QCOMPARE(first->property("cfg_amount").toInt(),3);QCOMPARE(second->property("cfg_amount").toInt(),3);
            }
            QVERIFY(!session.dirty());
        }
        QCOMPARE(instances,2);QCOMPARE(edited,1);
    }
    void configButtonsAndPopup() {
        const QString id=qEnvironmentVariable("BWM_TEST_APPLET");
        QVERIFY(!id.isEmpty());
        TestCorona corona;
        auto shell=KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR));
        QVERIFY(shell.isValid()); corona.setKPackage(shell);
        auto *c=corona.createContainment("null"); QVERIFY(c);
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);
        auto *a=c->createApplet(id); auto *b=c->createApplet(id);
        QVERIFY(a && b);
        QQuickWindow panel;panel.resize(200,48);panel.show();
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);QVERIFY2(item,qPrintable(a->launchErrorMessage()));
        item->setParentItem(panel.contentItem());item->setSize(QSizeF(48,48));
        // The host is permitted to choose the panel compact representation, even when the
        // package prefers an expanded representation on a desktop.
        item->setPreferredRepresentation(item->compactRepresentation());
        QTRY_VERIFY(item->compactRepresentationItem());
        auto *expander=findVisual(item,"bwmCompactExpander");QVERIFY(expander);
        auto *popup=expander->findChild<PlasmaQuick::AppletPopup*>("bwmAppletPopup");QVERIFY(popup);
        auto *compact=item->compactRepresentationItem();QVERIFY(compact);
        QTRY_VERIFY(compact->width()>0);
        QTest::mouseClick(&panel,Qt::LeftButton,Qt::NoModifier,compact->mapToScene(QPointF(compact->width()/2,compact->height()/2)).toPoint());
        QTRY_VERIFY(popup->isVisible());
        QVERIFY(popup->mainItem());
        item->setExpanded(false);QTRY_VERIFY(!popup->isVisible());
        item->setExpanded(true);QTRY_VERIFY(popup->isVisible());
        popup->hide();QTRY_VERIFY(!item->isExpanded());
        corona.saveLayout("bwm-ui-test-appletsrc");
        if(id=="org.kde.example.configuration") {
            auto *unexposed=a->configScheme()->KCoreConfigSkeleton::findItem("OtherTest");
            unexposed->setProperty(QStringLiteral("non-default unexposed value"));QVERIFY(a->configScheme()->save());
        }
        QString key;
        QVariant original;
        {
            ConfigurationSession session(a);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QVERIFY(!session.pages().isEmpty());
            auto *page=session.pages().first().toMap().value("item").value<QQuickItem*>();QVERIFY(page);
            for(int i=0;i<page->metaObject()->propertyCount();++i) {
                auto property=page->metaObject()->property(i);
                const QString name=QString::fromLatin1(property.name());
                if(!name.startsWith("cfg_"))continue;
                auto *entry=a->configScheme()->KCoreConfigSkeleton::findItem(name.mid(4));
                if(entry && entry->property().metaType().id()==QMetaType::Bool) {key=name.mid(4);original=entry->property();break;}
            }
            QVERIFY(!key.isEmpty());
            session.show();QTRY_VERIFY(session.view()->isVisible());
            page->setProperty(("cfg_"+key).toUtf8(),!original.toBool());
            QVERIFY(session.dirty());
            click(session.view(),"cancelButton");
            QTRY_VERIFY(!session.view() || !session.view()->isVisible());
            QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem(key)->property(),original);
        }
        {
            ConfigurationSession session(a);QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            session.show();QTRY_VERIFY(session.view()->isVisible());
            auto *page=session.pages().first().toMap().value("item").value<QQuickItem*>();
            page->setProperty(("cfg_"+key).toUtf8(),!original.toBool());
            QVERIFY(session.dirty());
            if(id=="org.kde.example.configuration") {
                QVERIFY(page->setProperty("cfg_Test",QStringLiteral("staged text")));
                QVERIFY(page->setProperty("cfg_IntTest",25));
                auto *other=session.pages()[1].toMap().value("item").value<QQuickItem*>();
                click(session.view(),"categoryButton_1");
                QVERIFY(other->isVisible());
            }
            if(id=="AndromedaLauncher") {
                QVERIFY(page->setProperty("cfg_customGreeting",QStringLiteral("staged greeting")));
                auto *other=session.pages()[1].toMap().value("item").value<QQuickItem*>();
                QVERIFY(other->setProperty("cfg_numberColumns",5));
                click(session.view(),"categoryButton_1");
                QVERIFY(other->isVisible());
            }
            click(session.view(),"applyButton");
            QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QVERIFY(!session.dirty());
            if(id=="org.kde.example.configuration") {
                QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("Test")->property().toString(),QStringLiteral("staged text"));
                QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("IntTest")->property().toInt(),25);
            }
            if(id=="AndromedaLauncher") {
                QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("customGreeting")->property().toString(),QStringLiteral("staged greeting"));
                QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("numberColumns")->property().toInt(),5);
            }
            QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem(key)->property().toBool(),!original.toBool());
            QCOMPARE(b->configScheme()->KCoreConfigSkeleton::findItem(key)->property(),original);
            click(session.view(),"defaultsButton");
            QVERIFY(session.dirty());
            QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem(key)->property().toBool(),!original.toBool());
            click(session.view(),"applyButton");
            QVERIFY2(session.error().isEmpty(),qPrintable(session.error()));
            QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem(key)->property(),original);
            if(id=="org.kde.example.configuration")
                QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("OtherTest")->property().toString(),QStringLiteral("test2"));
        }
        // A separate configurator changed the same key. Save must reject a stale page.
        {
            ConfigurationSession session(a);QVERIFY(session.error().isEmpty());
            auto *page=session.pages().first().toMap().value("item").value<QQuickItem*>();
            page->setProperty(("cfg_"+key).toUtf8(),!original.toBool());
            auto *entry=a->configScheme()->KCoreConfigSkeleton::findItem(key);
            KConfig external(a->configScheme()->config()->name(),KConfig::SimpleConfig);
            KConfigGroup group(&external,entry->group());group.writeEntry(entry->key(),!original.toBool());external.sync();
            QVERIFY(!session.apply());
            QVERIFY(!session.error().isEmpty());
        }
    }
    void nativePanelPreferenceStore() {
        const QVariantMap fallback={{"floating",0},{"floatingApplets",0},{"panelOpacity",2},{"thickness",48},{"minLength",640},{"maxLength",640}};
        const QString path=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("plasmashellrc");
        const auto bytes=[&]{QFile f(path);return f.open(QIODevice::ReadOnly)?f.readAll():QByteArray();};
        {
            KConfig config("plasmashellrc");auto base=KConfigGroup(&config,"PlasmaViews").group("Panel 900001");
            base.deleteGroup();base.writeEntry("VendorKey","preserved");
            auto defaults=base.group("Defaults");defaults.writeEntry("thickness",36);defaults.writeEntry("minLength",300);defaults.writeEntry("maxLength",500);defaults.writeEntry("VendorDefaults",13);
            auto scope=base.group("Horizontal800");scope.writeEntry("minLength",320);scope.writeEntry("maxLength",480);scope.writeEntry("VendorScope",42);
            KConfigGroup(&config,"PlasmaViews").group("Panel 900002").writeEntry("floating",0);QVERIFY(config.sync());
        }
        PanelViewSettings store("plasmashellrc",900001,false,800,fallback);QVERIFY2(store.reload(),qPrintable(store.error()));
        QCOMPARE(store.values().value("minLength").toInt(),320);QCOMPARE(store.values().value("maxLength").toInt(),480);
        QCOMPARE(store.values().value("thickness").toInt(),36);
        const auto initial=bytes();QVERIFY(store.reload());QCOMPARE(bytes(),initial);
        QVERIFY2(store.apply({{"floating",true},{"floatingApplets",true},{"panelOpacity",1},{"thickness",40},{"minLength",330},{"maxLength",460}}),qPrintable(store.error()));
        {
            KConfig config("plasmashellrc");const auto base=KConfigGroup(&config,"PlasmaViews").group("Panel 900001");
            QCOMPARE(base.readEntry("floating",-1),1);QCOMPARE(base.readEntry("floatingApplets",-1),1);QCOMPARE(base.readEntry("panelOpacity",-1),1);
            QCOMPARE(base.group("Defaults").readEntry("thickness",0),40);
            for(const auto &name:{"Defaults","Horizontal800"}) {
                QCOMPARE(base.group(name).readEntry("minLength",0),330);QCOMPARE(base.group(name).readEntry("maxLength",0),460);
            }
            QCOMPARE(base.readEntry("VendorKey",QString()),"preserved");QCOMPARE(base.group("Defaults").readEntry("VendorDefaults",0),13);
            QCOMPARE(base.group("Horizontal800").readEntry("VendorScope",0),42);
            QCOMPARE(KConfigGroup(&config,"PlasmaViews").group("Panel 900002").readEntry("floating",-1),0);
        }
        // A change hidden by the current resolution still matters: min/max write Defaults too.
        {
            KConfig external("plasmashellrc");auto defaults=KConfigGroup(&external,"PlasmaViews").group("Panel 900001").group("Defaults");
            defaults.writeEntry("minLength",340);QVERIFY(external.sync());
        }
        const auto externallyChanged=bytes();QVERIFY(!store.apply({{"minLength",350}}));QCOMPARE(bytes(),externallyChanged);
        QVERIFY(store.reload());QCOMPARE(store.values().value("minLength").toInt(),330);
        {
            KConfig external("plasmashellrc");auto base=KConfigGroup(&external,"PlasmaViews").group("Panel 900001");
            base.writeEntry("floatingApplets",0);base.writeEntry("OtherWriter","keep me");QVERIFY(external.sync());
        }
        QVERIFY(store.apply({{"thickness",42}}));QCOMPARE(store.values().value("floatingApplets").toInt(),0);
        PanelViewSettings verticalScope("plasmashellrc",900001,true,600,fallback);QVERIFY(verticalScope.reload());
        QCOMPARE(verticalScope.values().value("minLength").toInt(),340);QCOMPARE(verticalScope.values().value("maxLength").toInt(),460);
        const auto committed=bytes();
        for(const auto &bad:QList<QVariantMap>{{{"panelOpacity",0}},{{"floating",QString("false")}},{{"thickness",12}},{{"minLength",500},{"maxLength",100}},{{"unknownNativeKey",42}}}) {
            QVERIFY(!store.apply(bad));QCOMPARE(bytes(),committed);
        }
        {
            QLockFile lock(store.lockPath());QVERIFY(lock.tryLock(0));
            QVERIFY(!store.apply({{"thickness",43}}));QCOMPARE(bytes(),committed);
        }
        // Native KConfig cascade and immutable flags, without touching any user defaults.
        const QString defaultsRoot=qEnvironmentVariable("XDG_CONFIG_DIRS").section(':',0,0);
        QVERIFY(QFileInfo(defaultsRoot).canonicalFilePath().startsWith(QDir::tempPath()+"/"));
        const QString policyPath=QDir(defaultsRoot).filePath("plasmashellrc");
        QFile policy(policyPath);const bool existed=policy.exists();QByteArray before;
        if(existed){QVERIFY(policy.open(QIODevice::ReadOnly));before=policy.readAll();policy.close();}
        struct RestoreFile{QString path;bool existed;QByteArray bytes;~RestoreFile(){if(existed){QFile f(path);if(f.open(QIODevice::WriteOnly))f.write(bytes);}else QFile::remove(path);}} restore{policyPath,existed,before};
        QVERIFY(policy.open(QIODevice::WriteOnly));policy.write(before);
        policy.write("\n[PlasmaViews][Panel 900001][Defaults]\nthickness[$i]=44\n");policy.close();
        QVERIFY2(store.reload(),qPrintable(store.error()));QCOMPARE(store.values().value("thickness").toInt(),44);
        const auto locked=bytes();QVERIFY(!store.apply({{"thickness",48}}));QVERIFY(store.error().contains("locked"));QCOMPARE(bytes(),locked);
        QVERIFY(!store.apply({{"floating",0},{"thickness",48}}));QCOMPARE(bytes(),locked);
    }
    void originalPanelSettingsEditMode() {
        // R5: "Enter Edit Mode" opens the installed PanelConfiguration.qml through the
        // panel's own configure action; its real controls persist like PanelView 6.7.5.
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QFile::remove(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-r5-edit-test"));corona.loadLayout("bwm-r5-edit-test");
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);QVERIFY(c->createApplet("org.bwm.r4.shared-config"));
        const auto path=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-r5-plasmashellrc");QFile::remove(path);
        const auto group=[&](KConfig &config){return KConfigGroup(&config,"PlasmaViews").group(QString("Panel %1").arg(c->id()));};
        QStringList scriptErrors;
        PanelViewHost view(&corona,path);corona.bind(c,&view);
        QVERIFY2(view.load(c),qPrintable(view.error()));view.show();
        QCOMPARE(view.lengthMode(),int(PanelViewEnums::FillAvailable));QCOMPARE(view.alignment(),int(Qt::AlignLeft));
        QTRY_COMPARE(view.width(),view.screen()->size().width());
        auto *configure=c->internalAction("configure");QVERIFY(configure);
        configure->trigger();
        PanelConfigView *dialog=nullptr;
        QTRY_VERIFY((dialog=[]{for(auto *w:QGuiApplication::allWindows())if(auto *d=qobject_cast<PanelConfigView*>(w))if(d->isVisible())return d;return (PanelConfigView*)nullptr;}()));
        QVERIFY(corona.isEditMode());QVERIFY(view.userConfiguring());
        auto *root=dialog->mainItem();QVERIFY(root);
        QVERIFY(qmlContext(root)->baseUrl().toString().endsWith("/contents/configuration/PanelConfiguration.qml"));
        connect(qmlEngine(root),&QQmlEngine::warnings,this,[&scriptErrors](const QList<QQmlError> &errors){
            for(const auto &e:errors)if(e.description().contains("ReferenceError") || e.description().contains("TypeError"))scriptErrors.append(e.toString());
        });
        QStringList expressionErrors;const auto run=[&](const char *code){QQmlExpression e(qmlContext(root),root,QString::fromUtf8(code));e.evaluate();if(e.hasError())expressionErrors.append(e.error().toString());};
        // Alignment combo: index 2 = Right. Length combo: index 2 = Custom shows the ruler.
        run("alignmentBox.activated(2)");QTRY_COMPARE(view.alignment(),int(Qt::AlignRight));
        run("widthBox.activated(2)");QTRY_COMPARE(view.lengthMode(),int(PanelViewEnums::Custom));
        QTRY_VERIFY(dialog->panelRulerView()->isVisible());
        run("spinBox.value=52;spinBox.valueModified()");QTRY_COMPARE(view.thickness(),52);
        run("floatingBox.activated(2)");QTRY_VERIFY(view.floating());
        // Opacity options follow the Plasma style, as PanelView::adaptiveOpacityEnabled.
        QCOMPARE(view.adaptiveOpacityEnabled(),Plasma::Theme().adaptiveTransparencyEnabled());
        if(view.adaptiveOpacityEnabled()){run("transparencyBox.activated(1)");QTRY_COMPARE(view.opacityMode(),int(PanelViewEnums::Opaque));}
        // Auto hide has no controller here: refused, and the combo returns to the stored value.
        run("autoHideBox.activated(1)");QCOMPARE(view.visibilityMode(),int(PanelViewEnums::WindowsGoBelow));
        QVERIFY(!view.error().isEmpty());
        {
            KConfig config(path,KConfig::SimpleConfig);auto g=group(config);
            QCOMPARE(g.readEntry("alignment",0),int(Qt::AlignRight));QCOMPARE(g.readEntry("panelLengthMode",-1),2);
            QCOMPARE(g.group("Defaults").readEntry("thickness",0),52);QCOMPARE(g.readEntry("floating",0),1);
            QVERIFY(!g.hasKey("panelVisibility"));
        }
        // "Set Position…" moves the panel in place, keeping the settings open, as PanelView.
        run("setPositionButton.checked=true;setPositionButton.moveTo(5)");
        QTRY_COMPARE(c->location(),Plasma::Types::LeftEdge);QCOMPARE(c->formFactor(),Plasma::Types::Vertical);
        QVERIFY(dialog->isVisible());QVERIFY(view.userConfiguring());
        QCOMPARE(view.capabilities().value("viewSettingsScope").toString(),"Vertical"+QString::number(view.screen()->size().height()));
        QTRY_VERIFY(view.height()>view.width());
        run("setPositionButton.checked=true;setPositionButton.moveTo(4)");
        QTRY_COMPARE(c->location(),Plasma::Types::BottomEdge);QCOMPARE(c->formFactor(),Plasma::Types::Horizontal);QVERIFY(dialog->isVisible());
        // "Add New > Spacer" uses the original containment, not a BWM list.
        run("configDialog.addPanelSpacer()");
        bool spacer=false;for(auto *a:c->applets())spacer|=a->pluginMetaData().pluginId()=="org.kde.plasma.panelspacer";QVERIFY(spacer);
        QVERIFY2(expressionErrors.isEmpty(),qPrintable(expressionErrors.join('\n')));
        QVERIFY2(scriptErrors.isEmpty(),qPrintable(scriptErrors.join('\n')));
        dialog->requestActivate();QTRY_VERIFY(dialog->isActive());
        QTest::keyClick(dialog,Qt::Key_Escape);
        QTRY_VERIFY(!corona.isEditMode());QTRY_VERIFY(!view.userConfiguring());
        // Outside the settings the setters stay preview-only.
        const auto bytes=[&]{QFile f(path);return f.open(QIODevice::ReadOnly)?f.readAll():QByteArray();};
        const auto stored=bytes();view.setAlignment(Qt::AlignCenter);QCOMPARE(view.alignment(),int(Qt::AlignCenter));QCOMPARE(bytes(),stored);
        PanelViewHost fresh(&corona,path);QVERIFY2(fresh.load(c),qPrintable(fresh.error()));
        QCOMPARE(fresh.alignment(),int(Qt::AlignRight));QCOMPARE(fresh.lengthMode(),int(PanelViewEnums::Custom));QCOMPARE(fresh.thickness(),52);
        corona.unbind(c);corona.saveLayout("bwm-r5-edit-test");QVERIFY(corona.config()->sync());
    }
    void originalPanelToolBoxOverlayAndContextMenu() {
        // R5: the shell package [Panel] defaults of plasma-desktop 6.7.5 give the panel its
        // ToolBox (the configure button ConfigOverlay.qml sizes itself against) and the
        // org.kde.contextmenu right-click action; without them ConfigOverlay hit a null toolBox
        // and right-clicking the panel did nothing.
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QFile::remove(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-r5-toolbox-test"));corona.loadLayout("bwm-r5-toolbox-test");
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);QVERIFY(c->createApplet("org.bwm.r4.shared-config"));
        QVERIFY(c->containmentActions().contains(QStringLiteral("RightButton;NoModifier")));
        const auto path=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-r5-toolbox-plasmashellrc");QFile::remove(path);
        PanelViewHost view(&corona,path);corona.bind(c,&view);
        QVERIFY2(view.load(c),qPrintable(view.error()));view.show();
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(c);QVERIFY(root);
        QStringList scriptErrors;
        connect(qmlEngine(root),&QQmlEngine::warnings,this,[&scriptErrors](const QList<QQmlError> &errors){
            for(const auto &e:errors)if((e.url().toString().contains("org/kde/panel") || e.url().toString().contains("paneltoolbox")) &&
                (e.description().contains("ReferenceError") || e.description().contains("TypeError")))scriptErrors.append(e.toString());});
        QTRY_VERIFY(root->property("toolBox").value<QQuickItem*>());
        auto *toolBox=root->property("toolBox").value<QQuickItem*>();
        QVERIFY(qmlContext(toolBox)->baseUrl().toString().contains("org.kde.paneltoolbox"));
        QVERIFY(!toolBox->isVisible());
        // Edit mode: the original ConfigOverlay is created and the toolbox button shows.
        c->internalAction("configure")->trigger();
        QTRY_VERIFY(view.userConfiguring());QVERIFY(corona.isEditMode());
        QTRY_VERIFY(root->property("configOverlay").value<QObject*>());QTRY_VERIFY(toolBox->isVisible());
        QPointer<PanelConfigView> dialog;
        QTRY_VERIFY((dialog=[]{for(auto *w:QGuiApplication::allWindows())if(auto *d=qobject_cast<PanelConfigView*>(w))if(d->isVisible())return d;return (PanelConfigView*)nullptr;}()));
        dialog->requestActivate();QTRY_VERIFY(dialog->isActive());QTest::keyClick(dialog,Qt::Key_Escape);
        QTRY_VERIFY(!corona.isEditMode());QTRY_VERIFY(!root->property("configOverlay").value<QObject*>());QTRY_VERIFY(!toolBox->isVisible());
        // Right click on the panel opens the containment menu of org.kde.contextmenu.
        const auto visibleMenu=[]{for(auto *w:QApplication::topLevelWidgets())if(auto *m=qobject_cast<QMenu*>(w))if(m->isVisible())return m;return (QMenu*)nullptr;};
        QTRY_VERIFY(view.width()>200);
        QTest::mouseClick(&view,Qt::RightButton,{},QPoint(view.width()-4,view.height()/2));
        QMenu *menu=nullptr;QTRY_VERIFY((menu=visibleMenu()));
        QVERIFY(menu->actions().contains(c->internalAction("configure")));
        QVERIFY(menu->actions().contains(c->internalAction("add widgets")));
        // Its "Add Widgets…" reaches the original explorer through showAddWidgetsInterface.
        c->internalAction("add widgets")->trigger();menu->close();
        QTRY_VERIFY(view.widgetExplorer() && view.widgetExplorer()->isVisible());QVERIFY(corona.isEditMode());
        view.widgetExplorer()->sidePanel()->setVisible(false);QTRY_VERIFY(!corona.isEditMode());
        QVERIFY2(scriptErrors.isEmpty(),qPrintable(scriptErrors.join('\n')));
        corona.unbind(c);corona.saveLayout("bwm-r5-toolbox-test");QVERIFY(corona.config()->sync());
    }
    void originalWidgetExplorerAddsToPanel() {
        // R5: "Add Widgets…" of the original Panel Settings opens the installed, unmodified
        // explorer/WidgetExplorer.qml; addApplet() uses the panel containment, and closing it
        // returns to the Panel Settings like ShellCorona/WidgetExplorer.qml 6.7.5.
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QFile::remove(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-r5-explorer-test"));corona.loadLayout("bwm-r5-explorer-test");
        auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);QVERIFY(c->createApplet("org.bwm.r4.shared-config"));
        const auto path=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-r5-explorer-plasmashellrc");QFile::remove(path);
        PanelViewHost view(&corona,path);corona.bind(c,&view);
        QVERIFY2(view.load(c),qPrintable(view.error()));view.show();
        c->internalAction("configure")->trigger();
        const auto settings=[]{for(auto *w:QGuiApplication::allWindows())if(auto *d=qobject_cast<PanelConfigView*>(w))if(d->isVisible())return d;return (PanelConfigView*)nullptr;};
        QPointer<PanelConfigView> dialog;QTRY_VERIFY((dialog=settings()));
        QStringList scriptErrors;
        const auto watch=[&](QQmlEngine *engine){connect(engine,&QQmlEngine::warnings,this,[&scriptErrors](const QList<QQmlError> &errors){
            // SharedQmlEngine shares one engine with the panel: keep the explorer's own files.
            for(const auto &e:errors)if((e.url().toString().contains("/explorer/") || e.url().toString().contains("WidgetExplorerHost")) &&
                (e.description().contains("ReferenceError") || e.description().contains("TypeError") || e.description().contains("is not defined")))scriptErrors.append(e.toString());});};
        QQmlExpression(qmlContext(dialog->mainItem()),dialog->mainItem(),"configDialog.showAddWidgetDialog()").evaluate();
        QTRY_VERIFY(view.widgetExplorer());
        auto *explorer=view.widgetExplorer();QVERIFY2(explorer->error().isEmpty(),qPrintable(explorer->error()));
        auto *root=explorer->rootItem();QVERIFY(root);watch(qmlEngine(root));
        // PanelConfigView deletes itself once hidden, like upstream.
        QTRY_VERIFY(explorer->isVisible());QTRY_VERIFY(!dialog || !dialog->isVisible());QVERIFY(corona.isEditMode());
        QCOMPARE(root->property("explorerState").toString(),"widgetExplorer");
        const auto eval=[&](const QString &code){QQmlExpression e(qmlContext(root),root,code);const auto v=e.evaluate();if(e.hasError())scriptErrors.append(e.error().toString());return v;};
        QTRY_VERIFY(eval("sidePanelStack.item !== null && root.widgetExplorer !== null").toBool());
        QVERIFY(eval("sidePanelStack.item.containment === root.containment").toBool());
        QVERIFY(qmlContext(eval("sidePanelStack.item").value<QObject*>())->baseUrl().toString().endsWith("/contents/explorer/WidgetExplorer.qml"));
        // The original model lists the installed widgets; its search narrows it.
        QTRY_VERIFY(eval("root.widgetExplorer.widgetsModel.count").toInt()>1);
        const int all=eval("root.widgetExplorer.widgetsModel.count").toInt();
        eval("root.widgetExplorer.widgetsModel.searchTerm='analog clock'");
        QTRY_VERIFY(eval("root.widgetExplorer.widgetsModel.count").toInt()<all);
        eval("root.widgetExplorer.widgetsModel.searchTerm=''");
        const auto has=[&](const QString &id){for(auto *a:c->applets())if(a->pluginMetaData().pluginId()==id)return true;return false;};
        QVERIFY(!has("org.kde.plasma.analogclock"));
        eval("root.widgetExplorer.addApplet('org.kde.plasma.analogclock')");
        QTRY_VERIFY(has("org.kde.plasma.analogclock"));
        // ShellCorona::isScreenUiReady, called by the original Folder View added to a panel.
        QCOMPARE(eval("typeof root.containment.corona.isScreenUiReady").toString(),"function");
        QTRY_VERIFY(eval("root.containment.corona.isScreenUiReady(root.containment.screen)").toBool());
        QVERIFY(!eval("root.containment.corona.isScreenUiReady(-1)").toBool());
        // BWM: Hyprland focuses an on-demand layer on hover; the edited panel taking focus is
        // not the deactivation that hides the side bar (Dialog::focusOutEvent "viewClicked").
        explorer->sidePanel()->requestActivate();QTRY_VERIFY(explorer->sidePanel()->isActive());
        view.requestActivate();QTRY_VERIFY(view.isActive());
        QTest::qWait(100);QVERIFY(explorer->isVisible());QCOMPARE(root->property("explorerState").toString(),"widgetExplorer");
        // Closing the explorer from a panel reopens its settings (WidgetExplorer.qml onClosed).
        eval("sidePanelStack.item.closed()");
        QTRY_VERIFY(!explorer->isVisible());QTRY_VERIFY((dialog=settings()));
        QTRY_VERIFY(view.userConfiguring());QVERIFY(corona.isEditMode());
        dialog->requestActivate();QTRY_VERIFY(dialog->isActive());QTest::keyClick(dialog,Qt::Key_Escape);
        QTRY_VERIFY(!corona.isEditMode());
        // The containment's own "add widgets" action toggles the same side bar; hiding it
        // (window deactivation) leaves edit mode without reopening the settings.
        c->internalAction("add widgets")->trigger();
        QTRY_VERIFY(explorer->isVisible());QVERIFY(corona.isEditMode());
        explorer->sidePanel()->setVisible(false);
        QTRY_VERIFY(!corona.isEditMode());QVERIFY(!settings());
        QTRY_COMPARE(root->property("explorerState").toString(),"closed");
        QVERIFY2(scriptErrors.isEmpty(),qPrintable(scriptErrors.join('\n')));
        corona.unbind(c);corona.saveLayout("bwm-r5-explorer-test");QVERIFY(corona.config()->sync());
    }
    void panelViewPreferencesPersistAndApply() {
        TestCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QFile::remove(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-panel-preferences-test"));corona.loadLayout("bwm-panel-preferences-test");
        auto *c=corona.createContainment("org.kde.panel"),*other=corona.createContainment("org.kde.panel");QVERIFY(c && other);
        for(auto *panel:{c,other}){panel->setLocation(Plasma::Types::BottomEdge);panel->setFormFactor(Plasma::Types::Horizontal);QVERIFY(panel->createApplet("org.bwm.r4.shared-config"));}
        {
            KConfig config("plasmashellrc");for(auto *panel:{c,other})KConfigGroup(&config,"PlasmaViews").group(QString("Panel %1").arg(panel->id())).deleteGroup();QVERIFY(config.sync());
        }
        const auto path=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("plasmashellrc");
        const auto bytes=[&]{QFile f(path);return f.open(QIODevice::ReadOnly)?f.readAll():QByteArray();};
        {
            PanelViewHost view(&corona),second(&corona);QVERIFY2(view.load(c),qPrintable(view.error()));QVERIFY(second.load(other));
            view.show();second.show();const auto initial=bytes();
            view.setFloating(true);view.setThickness(40);QCoreApplication::processEvents();QCOMPARE(bytes(),initial);
            QVERIFY(view.reloadViewSettings());QVERIFY(!view.floating());QTRY_COMPARE(view.thickness(),48);
            QVERIFY2(view.applyViewSettings({{"floating",true},{"floatingApplets",true},{"panelOpacity",1},{"thickness",40},{"minLength",360},{"maxLength",360},{"panelLengthMode",2}}),qPrintable(view.error()));
            QTRY_VERIFY(view.floating());QTRY_COMPARE(view.thickness(),40);QTRY_COMPARE(view.width(),360);
            QTRY_COMPARE(view.rootObject()->property("floatingness").toDouble(),1.0);QVERIFY(view.rootObject()->property("isOpaque").toBool());
            QVERIFY(!second.floating());QCOMPARE(second.viewSettings().value("thickness").toInt(),48);
            const auto committed=bytes();QVERIFY(view.reloadViewSettings());QCOMPARE(bytes(),committed);
            c->setImmutability(Plasma::Types::UserImmutable);QVERIFY(!view.applyViewSettings({{"thickness",44}}));QCOMPARE(bytes(),committed);c->setImmutability(Plasma::Types::Mutable);
            c->setLocation(Plasma::Types::LeftEdge);c->setFormFactor(Plasma::Types::Vertical);
            QVERIFY(!view.applyViewSettings({{"thickness",44}}));QCOMPARE(bytes(),committed);
            QVERIFY(view.reloadViewSettings());QCOMPARE(view.capabilities().value("viewSettingsScope").toString(),"Vertical"+QString::number(view.screen()->size().height()));
            QTRY_COMPARE(view.height(),360);QCOMPARE(bytes(),committed);
            c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);QVERIFY(view.reloadViewSettings());
        }
        {
            KConfig config("plasmashellrc");KConfigGroup(&config,"PlasmaViews").group(QString("Panel %1").arg(c->id())).writeEntry("panelOpacity",0);QVERIFY(config.sync());
        }
        const auto unsupported=bytes();
        {PanelViewHost rejected(&corona);QVERIFY(!rejected.load(c));QVERIFY(rejected.error().contains("Adaptive"));QVERIFY(!rejected.rootObject());QCOMPARE(bytes(),unsupported);}
        {
            KConfig config("plasmashellrc");KConfigGroup(&config,"PlasmaViews").group(QString("Panel %1").arg(c->id())).writeEntry("panelOpacity",1);QVERIFY(config.sync());
        }
        corona.saveLayout("bwm-panel-preferences-test");QVERIFY(corona.config()->sync());
    }
    void panelViewPreferencesFreshProcessReadback() {
        TestCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout("bwm-panel-preferences-test");QCOMPARE(corona.containments().size(),2);
        int edited=0;
        for(auto *c:corona.containments()) {
            PanelViewHost view(&corona);QVERIFY2(view.load(c),qPrintable(view.error()));view.setLengthMode(PanelViewEnums::Custom);view.show();
            QVERIFY(view.capabilities().value("viewSettingsReady").toBool());
            if(view.viewSettings().value("floating").toInt()==1) {
                ++edited;QCOMPARE(view.thickness(),40);QTRY_COMPARE(view.width(),360);QVERIFY(view.floatingApplets());
                QCOMPARE(view.opacityMode(),int(PanelViewEnums::Opaque));
                QTRY_COMPARE(view.rootObject()->property("floatingness").toDouble(),1.0);
            } else {QCOMPARE(view.thickness(),48);QTRY_COMPARE(view.width(),640);}
        }
        QCOMPARE(edited,1);
    }
    void outputDescriptionsRejectAmbiguityAndWrongSerials() {
        using BwmOutput::Identity;using BwmOutput::resolve;
        const QList<Identity> outputs={{"Maker","Model 24","A"},{"Maker","Model 24","B"},{"Other","Model 240","C"},{"","",""}};
        QCOMPARE(resolve("Model 24",outputs).status,"ambiguous-output-description");
        QCOMPARE(resolve(" desc: maker   model 24 A ",outputs).index,0);
        QCOMPARE(resolve("Another EDID maker Model 24 B",outputs).index,1);
        QCOMPARE(resolve("Model 24 C",outputs).index,-1);
        QCOMPARE(resolve("model 2",outputs).index,-1);
        QCOMPARE(resolve("Other Model 240 C",outputs).index,2);
        QCOMPARE(resolve("DP-1",outputs).status,"invalid-output-description");
        QCOMPARE(resolve("desc:HDMI-A-1",outputs).status,"invalid-output-description");
        QCOMPARE(resolve("",outputs).status,"invalid-output-description");
        QCOMPARE(resolve("anything",{{"","",""}}).index,-1);
        QCOMPARE(resolve("Maker Model 24 A",{outputs[0],outputs[0]}).status,"ambiguous-output-description");
        QCOMPARE(resolve("Model 24",{outputs[0]}).index,0);
        QCOMPARE(resolve("Maker Model 24 A",{outputs[1],outputs[0]}).index,1);
        const QList<Identity> wayland={{"Micro-Star Int'l Co. Ltd.","MAG 274Q X24",""},{"LG Electronics","LG ULTRAFINE",""}};
        QCOMPARE(resolve("Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101",wayland).index,0);
        QCOMPARE(resolve("LG Electronics LG ULTRAFINE 405NTVS2J655",wayland).index,1);
        QCOMPARE(resolve("Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101",{wayland[0],wayland[0]}).status,"ambiguous-output-description");
        QCOMPARE(resolve("Wrong Maker MAG 274Q X24 0x01010101",wayland).index,-1);
        QCOMPARE(resolve("Micro-Star Int'l Co. Ltd. MAG 274Q X2 0x01010101",wayland).index,-1);
        QCOMPARE(resolve("Micro-Star Int'l Co. Ltd. MAG 274Q X24 extra serial fields",wayland).index,-1);
        QCOMPARE(resolve("Maker Model 24 B",{outputs[0]}).index,-1); // A known serial is never discarded.
        const Identity liveMsi={"Micro-Star Int'l Co., Ltd.","MAG 274Q X24",""};
        const QString liveDescription="Micro-Star Int'l Co. Ltd. MAG 274Q X24 0x01010101";
        QCOMPARE(resolve(liveDescription,{liveMsi,wayland[1]}).index,0);
        QCOMPARE(resolve(liveDescription,{liveMsi,liveMsi}).status,"ambiguous-output-description");
        QCOMPARE(resolve("Micro-Star Int'l Co., Ltd. MAG 274Q X24 0x01010101",{wayland[0]}).index,0);
        QCOMPARE(resolve("Micro Star Int'l Co. Ltd. MAG 274Q X24 0x01010101",{liveMsi}).index,-1);
        QCOMPARE(resolve("Maker Model 24 SERIAL",{{"Maker","Model, 24",""}}).index,-1); // Model punctuation stays significant.
        QCOMPARE(resolve("Maker Model, 24 SERIAL",{{"Maker","Model 24",""}}).index,-1);
    }
    void nativeViewBindingsCanBeReplacedAndWithdrawn() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput first("DP-91","Binding A","A",{0,0,1024,768}),second("DP-92","Binding B","B",{1024,0,1024,768});
        ViewCorona corona;auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        auto *old=new QQuickWindow;old->setScreen(first.screen());
        QQuickWindow current;current.setScreen(second.screen());
        corona.bind(c,old);corona.bind(c,&current);corona.bind(c,&current);
        QCOMPARE(corona.screenForContainment(c),QGuiApplication::screens().indexOf(second.screen()));
        delete old; // A retired window must not remove the newer binding.
        QCOMPARE(corona.screenForContainment(c),QGuiApplication::screens().indexOf(second.screen()));
        corona.unbind(c);QCOMPARE(corona.screenForContainment(c),-1);QCOMPARE(c->screen(),-1);
        corona.bind(c,&current);QCOMPARE(c->screenGeometry().toRect(),second.screen()->geometry());
        QSignalSpy removed(&corona,&Plasma::Corona::screenRemoved);
        const int previous=QGuiApplication::screens().indexOf(first.screen());first.remove();
        QCOMPARE(removed.count(),1);QCOMPARE(removed[0][0].toInt(),previous);
        QCOMPARE(corona.screenForContainment(c),QGuiApplication::screens().indexOf(second.screen()));
    }
    void panelRuntimeFollowsOutputsAndSkinWithoutLosingInstances() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput first("DP-81","Runtime A","A",{0,0,1280,800}),second("DP-82","Runtime B","B",{1280,0,1024,768});
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        const auto layout=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-runtime-layout");
        const auto preferences=QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-runtime-plasmashellrc");
        QFile::remove(layout);QFile::remove(preferences);corona.loadLayout(layout);
        auto *a=corona.createContainment("org.kde.panel"),*b=corona.createContainment("org.kde.panel");QVERIFY(a && b);
        for(auto *c:{a,b}){c->setLocation(Plasma::Types::BottomEdge);c->setFormFactor(Plasma::Types::Horizontal);QVERIFY(c->createApplet("org.bwm.r4.shared-config"));}
        const uint idA=a->id(),idB=b->id();
        const QHash<uint,QString> assignments={{idA,"BWM Test Runtime A A"},{idB,"BWM Test Runtime B B"}};
        {
            KConfig cfg(preferences,KConfig::SimpleConfig);
            KConfigGroup(&cfg,"PlasmaViews").group(QString("Panel %1").arg(idA)).group("Defaults").writeEntry("thickness",38);
            KConfigGroup(&cfg,"PlasmaViews").group(QString("Panel %1").arg(idB)).group("Defaults").writeEntry("thickness",60);QVERIFY(cfg.sync());
        }
        const auto bytes=[&]{QFile f(preferences);return f.open(QIODevice::ReadOnly)?f.readAll():QByteArray();};const auto initial=bytes();
        {
            PanelRuntime runtime(&corona,preferences,true);QVERIFY(runtime.setAssignments(assignments));
            QVERIFY(!runtime.view(idA));QVERIFY(runtime.setSkin("plasma"));
            QTRY_VERIFY(runtime.view(idA) && runtime.view(idB));
            QCOMPARE(runtime.view(idA)->screen(),first.screen());QCOMPARE(runtime.view(idB)->screen(),second.screen());
            QCOMPARE(runtime.view(idA)->thickness(),38);QCOMPARE(runtime.view(idB)->thickness(),60);
            QPointer<PanelViewHost> firstView=runtime.view(idA),secondView=runtime.view(idB);
            runtime.reconcile();QCOMPARE(runtime.view(idA),firstView.data());QCOMPARE(runtime.view(idB),secondView.data());
            // Open a native config window; staged controls must not be committed by withdrawal.
            auto *session=runtime.view(idA)->panelSession();auto *widget=a->applets().first();
            QVERIFY(session->configure(widget->id()));auto *configuration=session->configuration(widget->id());QVERIFY(configuration && configuration->view());
            QPointer<PlasmaQuick::ConfigView> configView=configuration->view();
            auto *page=configuration->pages().first().toMap().value("item").value<QQuickItem*>();QVERIFY(page);
            QVERIFY(page->setProperty("cfg_enabled",!page->property("cfg_enabled").toBool()));
            QVERIFY(runtime.setSkin("retro"));QVERIFY(!firstView && !secondView && !configView);
            QCOMPARE(corona.screenForContainment(a),-1);QCOMPARE(corona.containments().size(),2);QCOMPARE(bytes(),initial);
            QVERIFY(runtime.setSkin("plasma"));QTRY_VERIFY(runtime.view(idA) && runtime.view(idB));
            QCOMPARE(a->id(),idA);QCOMPARE(a->applets().first(),widget);QCOMPARE(runtime.view(idB)->thickness(),60);
            QVERIFY(widget->configScheme()->KCoreConfigSkeleton::findItem("enabled")->property().toBool());
            // Withdraw only the disappearing panel's original package window.
            QQmlEngine engine;QQmlContext contextA(engine.rootContext()),contextB(engine.rootContext());
            contextA.setContextProperty("plasmoid",widget);contextB.setContextProperty("plasmoid",b->applets().first());
            QQmlComponent dialogComponent(&engine);dialogComponent.setData("import QtQuick; import org.kde.plasma.core as PC; PC.Dialog { mainItem: Item { width: 40; height: 40 } }",QUrl());
            std::unique_ptr<QObject> dialogObjectA(dialogComponent.create(&contextA)),dialogObjectB(dialogComponent.create(&contextB));
            auto *dialogA=qobject_cast<QQuickWindow*>(dialogObjectA.get()),*dialogB=qobject_cast<QQuickWindow*>(dialogObjectB.get());QVERIFY(dialogA && dialogB);
            dialogA->show();dialogB->show();QVERIFY(dialogA->isVisible() && dialogB->isVisible());
            // A screen disappearing must not move its panel to the surviving screen.
            secondView=runtime.view(idB);first.remove();QTRY_VERIFY(!runtime.view(idA));
            QCOMPARE(runtime.view(idB),secondView.data());QCOMPARE(corona.screenForContainment(a),-1);
            QVERIFY(!dialogA->isVisible());QVERIFY(dialogB->isVisible());
            {
                // New connector, different Qt index, same EDID description.
                TestOutput reconnected("DP-99","Runtime A","A",{-1280,0,1280,800});
                QTRY_VERIFY(runtime.view(idA));QCOMPARE(runtime.view(idA)->screen(),reconnected.screen());
                QCOMPARE(runtime.view(idB),secondView.data());QCOMPARE(runtime.view(idA)->thickness(),38);
                QPointer<PanelViewHost> before=runtime.view(idA);
                TestOutput duplicate("DP-98","Runtime A","A",{0,900,1280,800});
                QTRY_VERIFY(!runtime.view(idA));QVERIFY(!before);QCOMPARE(runtime.view(idB),secondView.data());
                bool ambiguous=false;for(const auto &row:runtime.panels())if(row.toMap().value("containmentId").toUInt()==idA)ambiguous=row.toMap().value("status")=="ambiguous-output-description";
                QVERIFY(ambiguous);duplicate.remove();QTRY_VERIFY(runtime.view(idA));
                QVERIFY(!runtime.setSkin("invalid"));QVERIFY(runtime.view(idA));
                auto invalid=assignments;invalid[idA]="DP-99";QVERIFY(!runtime.setAssignments(invalid));QVERIFY(runtime.view(idA));
                QPointer<PanelViewHost> beforeEdgeChange=runtime.view(idA);
                a->setLocation(Plasma::Types::RightEdge);a->setFormFactor(Plasma::Types::Vertical);
                QTRY_VERIFY(!beforeEdgeChange);QVERIFY(runtime.view(idA));
                QCOMPARE(runtime.view(idA)->property("bwmRuntimeEdge").toInt(),int(Qt::RightEdge));
                QCOMPARE(runtime.view(idB),secondView.data());
                // An unavailable policy blocks only its own panel, with a reason.
                QVERIFY(runtime.setSkin("retro"));
                {KConfig cfg(preferences,KConfig::SimpleConfig);KConfigGroup(&cfg,"PlasmaViews").group(QString("Panel %1").arg(idA)).writeEntry("panelOpacity",0);QVERIFY(cfg.sync());}
                QVERIFY(runtime.setSkin("plasma"));QVERIFY(!runtime.view(idA));QVERIFY(runtime.view(idB));
                bool rejected=false;for(const auto &row:runtime.panels())if(row.toMap().value("containmentId").toUInt()==idA)
                    rejected=row.toMap().value("status")=="view-unavailable" && row.toMap().value("error").toString().contains("Adaptive");
                QVERIFY(rejected);
                {QFile restore(preferences);QVERIFY(restore.open(QIODevice::WriteOnly));QCOMPARE(restore.write(initial),initial.size());}
                runtime.reconcile();QVERIFY(runtime.view(idA));
                // A logical resolution change selects the native resolution group
                // without replacing the stable output binding or touching panel B.
                {KConfig cfg(preferences,KConfig::SimpleConfig);auto scope=KConfigGroup(&cfg,"PlasmaViews").group(QString("Panel %1").arg(idA)).group("Vertical900");
                    scope.writeEntry("minLength",400);scope.writeEntry("maxLength",400);scope.parent().writeEntry("panelLengthMode",2);QVERIFY(cfg.sync());}
                reconnected.platform->rect.setHeight(900);
                QWindowSystemInterface::handleScreenGeometryChange(reconnected.screen(),reconnected.platform->rect,reconnected.platform->rect);
                QTRY_COMPARE(runtime.view(idA)->capabilities().value("viewSettingsScope").toString(),"Vertical900");
                QTRY_COMPARE(runtime.view(idA)->height(),400);
                {QFile restore(preferences);QVERIFY(restore.open(QIODevice::WriteOnly));QCOMPARE(restore.write(initial),initial.size());}
            }
            QVERIFY(runtime.setSkin("default"));QVERIFY(!runtime.view(idA) && !runtime.view(idB));QCOMPARE(bytes(),initial);
            corona.saveLayout(layout);QVERIFY(corona.config()->sync());
            // Test-only caller metadata; production binding persistence/activation is separate.
            QJsonObject metadata;for(auto it=assignments.cbegin();it!=assignments.cend();++it)metadata.insert(QString::number(it.key()),it.value());
            QFile bindings(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-runtime-test-bindings.json"));
            QVERIFY(bindings.open(QIODevice::WriteOnly));bindings.write(QJsonDocument(metadata).toJson());
        }
        QCOMPARE(corona.containments().size(),2);
    }
    void panelRuntimeFreshProcessReadback() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        // Reverse Qt enumeration and change both connector names after restart.
        TestOutput second("DP-72","Runtime B","B",{0,0,1024,768}),first("DP-71","Runtime A","A",{1024,0,1280,800});
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));
        QFile metadata(config.filePath("bwm-runtime-test-bindings.json"));QVERIFY(metadata.open(QIODevice::ReadOnly));
        const auto object=QJsonDocument::fromJson(metadata.readAll()).object();QCOMPARE(object.size(),2);
        QHash<uint,QString> bindings;for(auto it=object.begin();it!=object.end();++it)bindings.insert(it.key().toUInt(),it.value().toString());
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(config.filePath("bwm-runtime-layout"));QCOMPARE(corona.containments().size(),2);
        PanelRuntime runtime(&corona,config.filePath("bwm-runtime-plasmashellrc"),true);QVERIFY(runtime.setAssignments(bindings));
        QVERIFY(runtime.setSkin("plasma"));
        for(auto *c:corona.containments()) {
            QTRY_VERIFY(runtime.view(c->id()));const bool isA=bindings.value(c->id()).endsWith(" A");
            QCOMPARE(runtime.view(c->id())->screen(),isA ? first.screen() : second.screen());
            QCOMPARE(runtime.view(c->id())->thickness(),isA ? 38 : 60);
            QCOMPARE(c->applets().size(),1);
            QVERIFY(c->applets().first()->configScheme()->KCoreConfigSkeleton::findItem("enabled")->property().toBool());
        }
        QVERIFY(runtime.setSkin("default"));for(auto *c:corona.containments())QVERIFY(!runtime.view(c->id()));
    }
    void nativeVisibilityPolicyUsesKdeAuthority() {
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));const auto path=config.filePath("bwm-native-policy-authority");QFile::remove(path);
        const QVariantMap defaults={{"floating",0},{"floatingApplets",0},{"panelOpacity",2},{"thickness",48},{"minLength",640},{"maxLength",640},{"panelVisibility",0}};
        {KConfig file(path,KConfig::SimpleConfig);auto base=KConfigGroup(&file,"PlasmaViews").group("Panel 880001");
            base.group("Horizontal1280").writeEntry("panelVisibility",3);base.writeEntry("VendorKeep",42);QVERIFY(file.sync());}
        PanelViewSettings store(path,880001,false,1280,defaults,true);QVERIFY(store.reload());QCOMPARE(store.values().value("panelVisibility").toInt(),3);
        QVERIFY(store.apply({{"panelVisibility",0}}));
        {KConfig file(path,KConfig::SimpleConfig);const auto base=KConfigGroup(&file,"PlasmaViews").group("Panel 880001");
            QCOMPARE(base.readEntry("panelVisibility",-1),0);QCOMPARE(base.group("Horizontal1280").readEntry("panelVisibility",-1),3);QCOMPARE(base.readEntry("VendorKeep",0),42);}
        // Concurrent native changes cannot be overwritten by a stale form.
        {KConfig file(path,KConfig::SimpleConfig);KConfigGroup(&file,"PlasmaViews").group("Panel 880001").writeEntry("panelVisibility",3);QVERIFY(file.sync());}
        QVERIFY(!store.apply({{"panelVisibility",3}}));QVERIFY(store.error().contains("changed elsewhere"));
        QVERIFY(store.reload());QCOMPARE(store.values().value("panelVisibility").toInt(),3);
        // The default preview must also reject a legacy resolution-specific NormalPanel.
        {KConfig file(path,KConfig::SimpleConfig);auto base=KConfigGroup(&file,"PlasmaViews").group("Panel 880001");base.deleteEntry("panelVisibility");base.group("Horizontal1280").writeEntry("panelVisibility",0);QVERIFY(file.sync());}
        PanelViewSettings preview(path,880001,false,1280,defaults);QVERIFY(!preview.reload());QVERIFY(preview.error().contains("panelVisibility"));
        const auto inheritedName=QStringLiteral("bwm-native-policy-kdedefaults");
        const auto inherited=QDir(qEnvironmentVariable("XDG_CONFIG_DIRS").split(QDir::listSeparator()).first()).filePath(inheritedName);
        {QFile file(inherited);QVERIFY(file.open(QIODevice::WriteOnly));file.write("[PlasmaViews][Panel 880001]\npanelVisibility[$i]=3\nVendorKeep=42\n");}
        PanelViewSettings locked(inheritedName,880001,false,1280,defaults,true);QVERIFY(locked.reload());QCOMPARE(locked.values().value("panelVisibility").toInt(),3);
        QVERIFY(!locked.apply({{"panelVisibility",0},{"thickness",44}}));QVERIFY(locked.error().contains("locked"));
        QVERIFY(!QFileInfo::exists(config.filePath(inheritedName)));
    }
    void nativePanelPolicyPersistsAndWithdrawsReservations() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput first("DP-57","Policy A","A",{0,0,1280,800}),second("DP-58","Policy B","B",{1280,0,1280,900});
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));const auto prefs=config.filePath("bwm-native-policy-plasmashellrc");
        const auto layout=config.filePath("bwm-native-policy-layout");QFile::remove(prefs);QFile::remove(layout);
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));corona.loadLayout(layout);
        auto *a=corona.createContainment("org.kde.panel");QVERIFY(a);a->setLocation(Plasma::Types::BottomEdge);a->setFormFactor(Plasma::Types::Horizontal);QVERIFY(a->createApplet("org.bwm.r4.shared-config"));
        const QString descriptionA="BWM Test Policy A A",descriptionB="BWM Test Policy B B";
        {KConfig file(prefs,KConfig::SimpleConfig);KConfigGroup(&file,"PlasmaViews").group(QString("Panel %1").arg(a->id())).writeEntry("VendorKeep",42);QVERIFY(file.sync());}
        const auto bytes=[&]{QFile f(prefs);return f.open(QIODevice::ReadOnly)?f.readAll():QByteArray();};
        PanelRuntime runtime(&corona,prefs,true,nullptr,true);QVERIFY(runtime.setAssignments({{a->id(),descriptionA}}));QVERIFY(runtime.setSkin("plasma"));
        auto *view=runtime.view(a->id());QVERIFY2(view,qPrintable(runtime.error()));auto *role=LayerShellQt::Window::get(view);
        QTRY_COMPARE(role->exclusionZone(),view->thickness());QVERIFY(view->capabilities().value("nativeVisibilityPolicy").toBool());
        QVERIFY(!view->capabilities().value("reservedArea").toBool());QVERIFY(!runtime.readiness().value("replacementReady").toBool());
        QVERIFY2(view->applyViewSettings({{"panelVisibility",0},{"floating",true},{"thickness",40},{"minLength",360},{"maxLength",360},{"panelLengthMode",2}}),qPrintable(view->error()));
        QTRY_COMPARE(view->width(),360);QTRY_COMPARE(role->exclusionZone(),40);
        QTRY_COMPARE(view->rootObject()->property("floatingness").toDouble(),1.0);
        QVERIFY(view->height()>role->exclusionZone()); // SVG floating padding is not reserved twice.
        QCOMPARE(role->margins().right(),1280-360);QCOMPARE(role->margins().bottom(),0);
        const auto original=bytes();
        for(int unsupported:{4,-1}){QVERIFY(!view->applyViewSettings({{"panelVisibility",unsupported}}));QCOMPARE(bytes(),original);QCOMPARE(role->exclusionZone(),40);}
        QVERIFY(!view->applyViewSettings({{"maxLength",1400}}));QCOMPARE(bytes(),original);
        QVERIFY(view->applyViewSettings({{"panelVisibility",3}}));QTRY_COMPARE(role->exclusionZone(),-1);QCOMPARE(view->visibilityMode(),3);
        QVERIFY(view->applyViewSettings({{"panelVisibility",0},{"thickness",42}}));QTRY_COMPARE(role->exclusionZone(),42);
        const auto persisted=bytes();
        QVERIFY(runtime.setSkin("retro"));QVERIFY(!runtime.view(a->id()));QCOMPARE(bytes(),persisted);
        QVERIFY(runtime.setSkin("plasma"));view=runtime.view(a->id());QVERIFY(view);role=LayerShellQt::Window::get(view);
        QTRY_COMPARE(role->exclusionZone(),42);QCOMPARE(view->visibilityMode(),0);QCOMPARE(bytes(),persisted);
        QPointer<PanelViewHost> old=view;bool reservedOnFallback=false;
        connect(role,&LayerShellQt::Window::exclusionZoneChanged,&runtime,[&,old,role]{
            if(old && old->screen()!=first.screen() && role->exclusionZone()>0)reservedOnFallback=true;
        });
        view->setScreen(second.screen());
        if(old){QVERIFY(!old->isVisible());QCOMPARE(role->exclusionZone(),-1);}
        QTRY_VERIFY(!old);QVERIFY(!reservedOnFallback);
        view=runtime.view(a->id());QVERIFY(view);role=LayerShellQt::Window::get(view);
        QCOMPARE(view->screen(),first.screen());QTRY_COMPARE(role->exclusionZone(),42);
        QTRY_VERIFY(view->presentationState().value("renderReady").toBool());
        QVERIFY(runtime.readiness().value("blockers").toStringList().contains("reserved-area-unverified"));
        // A second native-policy panel on the same output is explicitly blocked
        // until a multi-panel placement/stacking controller is available.
        auto *b=corona.createContainment("org.kde.panel");QVERIFY(b);b->setLocation(Plasma::Types::TopEdge);b->setFormFactor(Plasma::Types::Horizontal);QVERIFY(b->createApplet("org.bwm.r4.shared-config"));
        QVERIFY(runtime.setAssignments({{a->id(),descriptionA},{b->id(),descriptionA}}));QVERIFY(!runtime.view(a->id()) && !runtime.view(b->id()));
        for(const auto &row:runtime.panels())QCOMPARE(row.toMap().value("status").toString(),"native-policy-output-conflict");
        QVERIFY(runtime.setAssignments({{a->id(),descriptionA},{b->id(),descriptionB}}));QVERIFY(runtime.view(a->id()) && runtime.view(b->id()));
        QVERIFY(runtime.view(b->id())->applyViewSettings({{"panelVisibility",3}}));QTRY_COMPARE(LayerShellQt::Window::get(runtime.view(b->id()))->exclusionZone(),-1);
        QTRY_COMPARE(LayerShellQt::Window::get(runtime.view(a->id()))->exclusionZone(),42);
        QVERIFY(runtime.setSkin("default"));corona.saveLayout(layout);QVERIFY(corona.config()->sync());
        PanelViewHost regular(&corona,prefs);QVERIFY(!regular.load(a));QVERIFY(regular.error().contains("panelVisibility"));
        {KConfig file(prefs,KConfig::SimpleConfig);const auto base=KConfigGroup(&file,"PlasmaViews").group(QString("Panel %1").arg(a->id()));
            QCOMPARE(base.readEntry("VendorKeep",0),42);QCOMPARE(base.readEntry("panelVisibility",-1),0);
            QVERIFY(!base.group("Horizontal1280").hasKey("panelVisibility"));}
    }
    // R5: AutoHide/DodgeWindows with the edge strip that stands in for KWin's screen edge.
    void nativePanelAutoHideAndDodge() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput output("DP-60","Hide A","A",{0,0,1280,800});
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));const auto prefs=config.filePath("bwm-autohide-plasmashellrc");
        const auto layout=config.filePath("bwm-autohide-layout");QFile::remove(prefs);QFile::remove(layout);
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));corona.loadLayout(layout);
        auto *a=corona.createContainment("org.kde.panel");QVERIFY(a);a->setLocation(Plasma::Types::BottomEdge);a->setFormFactor(Plasma::Types::Horizontal);QVERIFY(a->createApplet("org.bwm.r4.shared-config"));
        PanelRuntime runtime(&corona,prefs,true,nullptr,true);QVERIFY(runtime.setAssignments({{a->id(),"BWM Test Hide A A"}}));QVERIFY(runtime.setSkin("plasma"));
        auto *view=runtime.view(a->id());QVERIFY2(view,qPrintable(runtime.error()));auto *role=LayerShellQt::Window::get(view);
        QTRY_VERIFY(view->isExposed());QVERIFY(view->capabilities().value("autohide").toBool());
        QVERIFY2(view->applyViewSettings({{"panelVisibility",0},{"thickness",40},{"minLength",360},{"maxLength",360},{"panelLengthMode",2}}),qPrintable(view->error()));
        QTRY_COMPARE(role->exclusionZone(),40);QVERIFY(!view->autoHidden());
        const auto strip=[view]{return QRegion(0,view->height()-2,view->width(),2);};
        // AutoHide: no reservation, content slides below the output, only the edge strip takes input.
        QVERIFY2(view->applyViewSettings({{"panelVisibility",1}}),qPrintable(view->error()));QCOMPARE(view->visibilityMode(),1);
        QTRY_COMPARE(role->exclusionZone(),-1);QTRY_VERIFY(view->autoHidden());
        QTRY_COMPARE(view->contentItem()->position(),QPointF(0,view->height()));QCOMPARE(view->mask(),strip());
        {KConfig file(prefs,KConfig::SimpleConfig);QCOMPARE(KConfigGroup(&file,"PlasmaViews").group(QString("Panel %1").arg(a->id())).readEntry("panelVisibility",-1),1);}
        // Pointer reaching the strip reveals it; leaving rehides after PanelView's 500 ms.
        QEnterEvent enter(QPointF(10,view->height()-1),QPointF(10,view->height()-1),QPointF(10,799));QCoreApplication::sendEvent(view,&enter);
        QVERIFY(!view->autoHidden());QTRY_COMPARE(view->contentItem()->position(),QPointF());QVERIFY(view->mask()!=strip());
        QEvent leave(QEvent::Leave);QCoreApplication::sendEvent(view,&leave);
        QTest::qWait(250);QVERIFY(!view->autoHidden());QTRY_VERIFY(view->autoHidden());
        // Edit mode and a visible transient window keep it shown (restoreAutoHide).
        corona.setEditMode(true);QVERIFY(!view->autoHidden());corona.setEditMode(false);QTRY_VERIFY(view->autoHidden());
        QQuickWindow transient;transient.setTransientParent(view);transient.resize(100,100);transient.show();
        QCoreApplication::sendEvent(view,&enter);QCoreApplication::sendEvent(view,&leave);
        QTest::qWait(800);QVERIFY(!view->autoHidden());transient.hide();QTRY_VERIFY(view->autoHidden());
        // Attention shows it; going passive hides it again.
        a->setStatus(Plasma::Types::NeedsAttentionStatus);QVERIFY(!view->autoHidden());
        a->setStatus(Plasma::Types::PassiveStatus);QTRY_VERIFY(view->autoHidden());
        // DodgeWindows follows Panel.qml's touchingWindow.
        QVERIFY2(view->applyViewSettings({{"panelVisibility",2}}),qPrintable(view->error()));
        view->rootObject()->setProperty("touchingWindow",false);QTRY_VERIFY(!view->autoHidden());QCOMPARE(role->exclusionZone(),-1);
        view->rootObject()->setProperty("touchingWindow",true);QTRY_VERIFY(view->autoHidden());QVERIFY(view->touchingWindow());
        view->rootObject()->setProperty("touchingWindow",false);QTRY_VERIFY(!view->autoHidden());QTRY_COMPARE(view->contentItem()->position(),QPointF());
        // Back to a normal panel: reserved again and in place.
        QVERIFY(view->applyViewSettings({{"panelVisibility",0}}));QTRY_COMPARE(role->exclusionZone(),40);QVERIFY(!view->autoHidden());
        // The preview surface keeps a gap from the edge: no strip, modes rejected.
        PanelRuntime preview(&corona,config.filePath("bwm-autohide-preview-plasmashellrc"),true,nullptr,false);
        QVERIFY(runtime.setSkin("default"));QVERIFY(preview.setAssignments({{a->id(),"BWM Test Hide A A"}}));QVERIFY(preview.setSkin("plasma"));
        auto *gap=preview.view(a->id());QVERIFY(gap);QVERIFY(!gap->capabilities().value("autohide").toBool());
        gap->setVisibilityMode(1);QCOMPARE(gap->visibilityMode(),3);QVERIFY(!gap->error().isEmpty());
        QVERIFY(preview.setSkin("default"));
    }
    void nativePanelPolicyFreshProcessReadback() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput second("DP-156","Policy B","B",{0,0,1280,900}),first("DP-155","Policy A","A",{1280,0,1280,800});
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));const auto prefs=config.filePath("bwm-native-policy-plasmashellrc");
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));corona.loadLayout(config.filePath("bwm-native-policy-layout"));
        QCOMPARE(corona.containments().size(),2);QHash<uint,QString> assignments;
        for(auto *c:corona.containments())assignments[c->id()]=c->location()==Plasma::Types::BottomEdge?"BWM Test Policy A A":"BWM Test Policy B B";
        PanelRuntime runtime(&corona,prefs,true,nullptr,true);QVERIFY(runtime.setAssignments(assignments));QVERIFY(runtime.setSkin("plasma"));
        for(auto *c:corona.containments()) {
            auto *view=runtime.view(c->id());QVERIFY(view);const bool a=c->location()==Plasma::Types::BottomEdge;
            QCOMPARE(view->screen(),a?first.screen():second.screen());QCOMPARE(view->visibilityMode(),a?0:3);
            QTRY_COMPARE(LayerShellQt::Window::get(view)->exclusionZone(),a?42:-1);
            if(a){QCOMPARE(view->thickness(),42);QTRY_COMPARE(view->width(),360);QVERIFY(view->floating());}
        }
        QVERIFY(runtime.setSkin("default"));
    }
    void previewStatusRequiresRenderedFrameAndFreshAcknowledgement() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput output("DP-59","Readiness","R",{0,0,1280,800});
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QTemporaryDir profile(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("readiness-profile-XXXXXX"));QVERIFY(profile.isValid());
        corona.loadLayout(profile.path()+"/layout");auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);QVERIFY(c->createApplet("org.bwm.r4.shared-config"));
        PanelRuntime runtime(&corona,profile.path()+"/plasmashellrc",false);
        QVERIFY(runtime.setAssignments({{c->id(),"BWM Test Readiness R"}}));
        QTemporaryDir directory(QDir(qEnvironmentVariable("XDG_RUNTIME_DIR")).filePath("readiness-control-XXXXXX"));QVERIFY(directory.isValid());
        const QString token(64,'c');
        const auto request=[&](int revision,const QString &action,const QString &skin="default") {
            QSaveFile file(directory.path()+"/control.json");if(!file.open(QIODevice::WriteOnly))return false;
            file.setPermissions(QFile::ReadOwner|QFile::WriteOwner);
            const auto bytes=QJsonDocument(QJsonObject{{"version",1},{"token",token},{"revision",revision},{"command",action},{"skin",skin}}).toJson();
            return file.write(bytes)==bytes.size() && file.commit();
        };
        const auto ack=[&]{QFile file(directory.path()+"/ack.json");if(!file.open(QIODevice::ReadOnly))return QJsonObject();return QJsonDocument::fromJson(file.readAll()).object();};
        const auto snapshot=[&]{return ack().value("runtime").toObject();};
        QVERIFY(request(0,"skin"));RuntimeControl control(&runtime,directory.path(),token);QVERIFY(control.start());
        QVERIFY(!snapshot().value("renderReady").toBool());QVERIFY(!snapshot().value("replacementReady").toBool());
        QCOMPARE(snapshot().value("qtPlatform").toString(),"offscreen");
        bool foundOutput=false;
        for(const auto &value:snapshot().value("availableOutputs").toArray()) {
            const auto info=value.toObject();
            if(info.value("model").toString()=="Readiness") {
                foundOutput=true;QCOMPARE(info.value("manufacturer").toString(),"BWM Test");QCOMPARE(info.value("serial").toString(),"R");
                QCOMPARE(info.value("geometry").toObject().value("width").toInt(),1280);
            }
        }
        QVERIFY(foundOutput);
        // A synchronous activation ack precedes the first software-rendered frame.
        QVERIFY(runtime.setSkin("plasma"));QPointer<PanelViewHost> frame=runtime.view(c->id());QVERIFY(frame);
        QVERIFY(!runtime.readiness().value("renderReady").toBool());
        QTRY_VERIFY(frame->presentationState().value("frameSubmitted").toBool());
        QTRY_VERIFY(runtime.readiness().value("renderReady").toBool());
        // A brief control withdrawal can be confirmed again before queued
        // teardown runs. Restore that same hidden view, not a fresh instance.
        frame->setProperty("bwmControlWithdrawn",true);frame->hide();runtime.reconcile();
        QCOMPARE(runtime.view(c->id()),frame.data());QVERIFY(frame->isVisible());
        QVERIFY(!frame->property("bwmControlWithdrawn").toBool());
        QVERIFY(request(1,"status"));QTRY_COMPARE(control.revision(),1);
        QVERIFY(snapshot().value("renderReady").toBool());QVERIFY(!snapshot().value("replacementReady").toBool());
        QVERIFY(snapshot().value("blockers").toArray().contains("reserved-area-unavailable"));
        QVERIFY(snapshot().value("blockers").toArray().contains("isolated-preview-only"));
        const auto panelState=snapshot().value("panels").toArray().first().toObject();
        QCOMPARE(panelState.value("widgetInventoryScope").toString(),"direct-panel-instances");
        QVERIFY(!panelState.value("widgetBackendsVerified").toBool());
        QCOMPARE(panelState.value("widgetBackends").toArray().size(),1);
        QVERIFY(snapshot().value("blockers").toArray().contains("widget-runtime-unverified"));
        QCOMPARE(runtime.view(c->id()),frame.data());QCOMPARE(runtime.skin(),"plasma");
        // A late old-frame swap must not certify a newly visible surface.
        frame->beforeRendering();frame->hide();frame->show();frame->frameSwapped();
        QVERIFY(!frame->presentationState().value("frameSubmitted").toBool());
        frame->hide();QVERIFY(request(2,"status"));QTRY_COMPARE(control.revision(),2);
        QVERIFY(!snapshot().value("renderReady").toBool());QCOMPARE(runtime.view(c->id()),frame.data());
        QVERIFY(!snapshot().value("panels").toArray().first().toObject().value("visible").toBool());
        frame->show();QTRY_VERIFY(runtime.readiness().value("renderReady").toBool());
        // Inject a Qt scene graph failure; no claim of a real GPU/driver failure.
        frame->sceneGraphError(QQuickWindow::ContextNotAvailable,QStringLiteral("injected-render-error"));
        QVERIFY(request(3,"status"));QTRY_COMPARE(control.revision(),3);
        QVERIFY(!snapshot().value("renderReady").toBool());
        QVERIFY(snapshot().value("blockers").toArray().contains("scene-graph-error"));
        output.remove();QTRY_VERIFY(!runtime.view(c->id()));QVERIFY(!frame);
        QVERIFY(request(4,"status"));QTRY_COMPARE(control.revision(),4);
        QVERIFY(!snapshot().value("renderReady").toBool());
        QVERIFY(snapshot().value("blockers").toArray().contains("output-unavailable"));
        QVERIFY(request(5,"skin","retro"));QTRY_COMPARE(control.revision(),5);
        QVERIFY(request(6,"status"));QTRY_COMPARE(control.revision(),6);
        QCOMPARE(snapshot().value("skin").toString(),"retro");QCOMPARE(runtime.skin(),"retro");
        QVERIFY(!snapshot().value("renderReady").toBool());
        QVERIFY(snapshot().value("blockers").toArray().contains("skin-inactive"));
    }
    void skinHookControlsOnlyRegisteredPreview() {
        QCOMPARE(QGuiApplication::platformName(),"offscreen");
        TestOutput output("DP-61","Control A","A",{0,0,1280,800});
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        QTemporaryDir profile(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("control-profile-XXXXXX"));QVERIFY(profile.isValid());
        corona.loadLayout(profile.path()+"/layout");auto *c=corona.createContainment("org.kde.panel");QVERIFY(c);
        c->setFormFactor(Plasma::Types::Horizontal);c->setLocation(Plasma::Types::BottomEdge);QVERIFY(c->createApplet("org.bwm.r4.shared-config"));
        PanelRuntime runtime(&corona,QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-control-plasmashellrc"),true);
        QVERIFY2(runtime.setAssignments({{c->id(),"BWM Test Control A A"}}),qPrintable(runtime.error()));
        QTemporaryDir directory(QDir(qEnvironmentVariable("XDG_RUNTIME_DIR")).filePath("control-XXXXXX"));QVERIFY(directory.isValid());
        const QString token(64,'a');
        const auto request=[&](int revision,const QString &skin,const QString &sessionToken=QString(64,'a')) {
            QSaveFile file(directory.path()+"/control.json");if(!file.open(QIODevice::WriteOnly))return false;
            file.setPermissions(QFile::ReadOwner|QFile::WriteOwner);
            const QJsonObject value{{"version",1},{"token",sessionToken},{"revision",revision},{"command","skin"},{"skin",skin}};
            const auto bytes=QJsonDocument(value).toJson();return file.write(bytes)==bytes.size() && file.commit();
        };
        QVERIFY(request(0,"default"));RuntimeControl control(&runtime,directory.path(),token);
        QSignalSpy applied(&control,&RuntimeControl::applied),stopped(&control,&RuntimeControl::stopRequested);
        QVERIFY2(control.start(),qPrintable(control.error()));QCOMPARE(control.revision(),0);QVERIFY(!runtime.view(c->id()));
        QVERIFY(request(1,"plasma"));QTRY_VERIFY(runtime.view(c->id()));QTRY_COMPARE(control.revision(),1);
        QVERIFY(request(1,"retro"));QTRY_VERIFY(control.error().contains("increase"));QVERIFY(runtime.view(c->id()));
        QVERIFY(request(2,"retro",QString(64,'b')));QTRY_VERIFY(control.error().contains("token"));QVERIFY(runtime.view(c->id()));
        QVERIFY(request(2,"retro"));QTRY_COMPARE(control.revision(),2);QVERIFY(!runtime.view(c->id()));
        QVERIFY(request(3,"plasma"));QTRY_COMPARE(control.revision(),3);QVERIFY(runtime.view(c->id()));
        RuntimeControl duplicate(&runtime,directory.path(),token);QVERIFY(!duplicate.start());QVERIFY(duplicate.error().contains("Another"));
        const auto root=QDir(QStringLiteral(BWM_SHELL_SOURCE_DIR)+"/../../..").canonicalPath();QVERIFY(!root.isEmpty());
        const auto publisher=root+"/config/hypr/skins/plasma/scripts/panel-session.py";
        const auto common=root+"/config/hypr/scripts/bwm_settings_hooks.py";
        const auto python=QStandardPaths::findExecutable("python3");QVERIFY(!python.isEmpty());
        const auto invoke=[&](const QStringList &args) {
            QProcess process;process.start(python,args);
            QElapsedTimer timer;timer.start();
            while(process.state()!=QProcess::NotRunning && timer.elapsed()<5000){QCoreApplication::processEvents();QTest::qWait(5);}
            if(process.state()!=QProcess::NotRunning){process.kill();process.waitForFinished();return false;}
            if(process.exitStatus()!=QProcess::NormalExit || process.exitCode()!=0){qWarning().noquote()<<process.readAllStandardError();return false;}
            return true;
        };
        QVERIFY(invoke({publisher,"register",directory.path(),QString::number(QCoreApplication::applicationPid()),token}));
        QPointer<PanelViewHost> current=runtime.view(c->id());QVERIFY(invoke({publisher,"status"}));
        QCOMPARE(runtime.view(c->id()),current.data());QCOMPARE(runtime.skin(),"plasma");QCOMPARE(control.revision(),4);
        QVERIFY(invoke({common,"skin","before","plasma","retro"}));QVERIFY(!runtime.view(c->id()));QCOMPARE(control.revision(),5);
        QVERIFY(invoke({common,"skin","before","retro","plasma"}));QCOMPARE(control.revision(),5);
        QVERIFY(invoke({common,"skin","after","retro","plasma"}));QVERIFY(runtime.view(c->id()));QCOMPARE(control.revision(),6);
        QVERIFY(invoke({publisher,"stop"}));QCOMPARE(stopped.count(),1);QVERIFY(!runtime.view(c->id()));QCOMPARE(control.revision(),7);
        QCOMPARE(applied.count(),8); // initial + 3 direct + status + 2 skin events + stop
        QVERIFY(invoke({publisher,"unregister",token}));
        QVERIFY(invoke({common,"skin","before","plasma","retro"}));QCOMPARE(control.revision(),7);
        QVERIFY(!QFileInfo::exists(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-control-plasmashellrc")));
    }
    void profileStoreKeepsNativeDataAndRestoresNewGeneration() {
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));const auto destination=config.filePath("bwm-ui-native-profile");
        if(QFileInfo::exists(destination))QVERIFY(QDir(destination).removeRecursively());
        const auto stagePath=config.filePath("bwm-native-staged");QVERIFY(!QFileInfo::exists(stagePath));
        const QByteArray source=R"({"bar":{"plasma":{"edge":"bottom","widgets":["clock","clock"],"thickness":44,"style":"opaque"}},"vendor":{"keep":42}})";
        const QJsonObject widget{{"package","org.kde.plasma.digitalclock"},{"nativeSettings",QJsonObject()}};
        QJsonArray panels;for(const auto &description:{"BWM Test Profile A A","BWM Test Profile B B"})
            panels.append(QJsonObject{{"outputDescription",description},{"containmentPackage","org.kde.panel"},{"widgets",QJsonArray{widget,widget}}});
        const QJsonObject plan{{"version",1},{"legacyJson",QString::fromUtf8(source)},
            {"sourceSha256",QString::fromLatin1(QCryptographicHash::hash(source,QCryptographicHash::Sha256).toHex())},{"panels",panels}};
        const auto planPath=config.filePath("bwm-profile-plan.json");
        {QFile file(planPath);QVERIFY(file.open(QIODevice::WriteOnly));file.write(QJsonDocument(plan).toJson());}
        const auto stage=BwmMigration::stage(planPath);QCOMPARE(stage.value("directory").toString(),stagePath);
        struct RemoveStage{QString path;~RemoveStage(){QDir(path).removeRecursively();}} remove{stagePath};
        {KConfig prefs(stagePath+"/plasmashellrc",KConfig::SimpleConfig);KConfigGroup(&prefs,"Vendor").writeEntry("Keep","view-unknown");QVERIFY(prefs.sync());
         KConfig layout(stagePath+"/layout",KConfig::SimpleConfig);KConfigGroup(&layout,"Vendor").writeEntry("Keep","layout-unknown");QVERIFY(layout.sync());}
        const auto readBytes=[](const QString &path){QFile file(path);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const auto imported=ProfileStore::importStage(stagePath,destination);QVERIFY(!imported.value("activationAllowed").toBool());
        QCOMPARE(readBytes(imported.value("layoutFile").toString()),readBytes(stagePath+"/layout"));
        QCOMPARE(readBytes(imported.value("viewSettingsFile").toString()),readBytes(stagePath+"/plasmashellrc"));
        {const auto path=destination+"/head.json";auto head=QJsonDocument::fromJson(readBytes(path)).object();head["VendorKeep"]="head-unknown";
            QSaveFile file(path);QVERIFY(file.open(QIODevice::WriteOnly));file.write(QJsonDocument(head).toJson());QVERIFY(file.commit());}
        ProfileStore profile(destination);QCOMPARE(profile.assignments().size(),2);
        QVERIFY_EXCEPTION_THROWN((void)ProfileStore(destination),std::runtime_error);
        const auto baseline=profile.checkpoint();const auto oldLayout=profile.layoutFile();const auto originalGeneration=profile.info().value("generation");
        auto retained=KSharedConfig::openConfig(oldLayout,KConfig::SimpleConfig);
        {
            TestOutput first("DP-51","Profile A","A",{0,0,1280,800}),second("DP-52","Profile B","B",{1280,0,1280,800});
            ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
            corona.loadLayout(profile.layoutFile());PanelRuntime runtime(&corona,profile.viewSettingsFile(),true);
            QVERIFY(runtime.setAssignments(profile.assignments()));QVERIFY(runtime.setSkin("plasma"));
            uint firstId=0;
            const auto outputs=profile.assignments();for(auto it=outputs.cbegin();it!=outputs.cend();++it)if(it.value().endsWith(" A"))firstId=it.key();
            QVERIFY(firstId);QTRY_VERIFY(runtime.view(firstId));
            QVERIFY(runtime.view(firstId)->applyViewSettings({{"thickness",52}}));QTRY_COMPARE(runtime.view(firstId)->thickness(),52);
            auto *session=runtime.view(firstId)->panelSession();const uint widgetId=session->addWidget("org.bwm.r4.shared-config");QVERIFY(widgetId);
            QVERIFY(session->configure(widgetId));auto *configuration=session->configuration(widgetId);QVERIFY(configuration && configuration->error().isEmpty());
            auto *page=configuration->pages().first().toMap().value("item").value<QQuickItem*>();QVERIFY(page);
            QVERIFY(page->setProperty("cfg_enabled",false));QVERIFY(page->setProperty("cfg_caption","saved in native profile"));QVERIFY(configuration->apply());
            QCoreApplication::processEvents();
            QVERIFY(runtime.setSkin("retro"));QVERIFY(runtime.setSkin("plasma"));QVERIFY(runtime.view(firstId));
            QCOMPARE(runtime.view(firstId)->thickness(),52);QVERIFY(runtime.setSkin("default"));
            corona.saveLayout(profile.layoutFile());QVERIFY(corona.config()->sync());
        }
        const auto edited=profile.checkpoint();QVERIFY(edited.value("snapshot")!=baseline.value("snapshot"));
        const auto headBefore=readBytes(destination+"/head.json");const auto snapshotLayout=baseline.value("directory").toString()+"/layout";
        const auto originalSnapshot=readBytes(snapshotLayout);
        {QFile file(snapshotLayout);QVERIFY(file.open(QIODevice::Append));file.write("\n[Changed]\nKeep=false\n");}
        QVERIFY_EXCEPTION_THROWN(profile.restore(baseline.value("snapshot").toString()),std::runtime_error);
        QCOMPARE(readBytes(destination+"/head.json"),headBefore);
        {QFile file(snapshotLayout);QVERIFY(file.open(QIODevice::WriteOnly));file.write(originalSnapshot);}
        const auto restored=profile.restore(baseline.value("snapshot").toString());QVERIFY(restored.value("generation")!=originalGeneration);
        QVERIFY(profile.layoutFile()!=oldLayout);QCOMPARE(readBytes(profile.layoutFile()),originalSnapshot);
        KConfigGroup(retained,"LateOldOwner").writeEntry("Keep","old-generation-only");QVERIFY(retained->sync());
        QCOMPARE(readBytes(profile.layoutFile()),originalSnapshot); // cached old owner cannot overwrite the restored path
        profile.restore(edited.value("snapshot").toString());
        QCOMPARE(QJsonDocument::fromJson(readBytes(destination+"/head.json")).object().value("VendorKeep").toString(),"head-unknown");
        {KConfig prefs(profile.viewSettingsFile(),KConfig::SimpleConfig);QCOMPARE(KConfigGroup(&prefs,"Vendor").readEntry("Keep",QString()),"view-unknown");}
        {KConfig layout(profile.layoutFile(),KConfig::SimpleConfig);QCOMPARE(KConfigGroup(&layout,"Vendor").readEntry("Keep",QString()),"layout-unknown");}
        QCOMPARE(readBytes(QFileInfo(profile.layoutFile()).absolutePath()+"/legacy.json"),source);
        // Detect an uncooperative metadata writer before publishing another head.
        const auto head=readBytes(destination+"/head.json");
        {auto foreign=QJsonDocument::fromJson(head).object();foreign["ForeignHead"]=1;QFile file(destination+"/head.json");QVERIFY(file.open(QIODevice::WriteOnly));file.write(QJsonDocument(foreign).toJson());}
        QVERIFY_EXCEPTION_THROWN(profile.checkpoint(),std::runtime_error);
        {QFile file(destination+"/head.json");QVERIFY(file.open(QIODevice::WriteOnly));file.write(head);}
    }
    void profileStoreFreshProcessReadback() {
        TestOutput second("DP-42","Profile B","B",{0,0,1280,800}),first("DP-41","Profile A","A",{1280,0,1280,800});
        ProfileStore profile(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-ui-native-profile"));
        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona.loadLayout(profile.layoutFile());QCOMPARE(corona.containments().size(),2);
        PanelRuntime runtime(&corona,profile.viewSettingsFile(),true);QVERIFY(runtime.setAssignments(profile.assignments()));QVERIFY(runtime.setSkin("plasma"));
        const auto outputs=profile.assignments();int configured=0;
        for(auto *c:corona.containments()) {
            const bool isA=outputs.value(c->id()).endsWith(" A");QTRY_VERIFY(runtime.view(c->id()));
            QCOMPARE(runtime.view(c->id())->screen(),isA ? first.screen() : second.screen());
            QCOMPARE(runtime.view(c->id())->thickness(),isA ? 52 : 44);
            QCOMPARE(c->applets().size(),isA ? 3 : 2);
            for(auto *a:c->applets())if(a->pluginMetaData().pluginId()=="org.bwm.r4.shared-config") {
                ++configured;QVERIFY(isA);QVERIFY(!a->configScheme()->KCoreConfigSkeleton::findItem("enabled")->property().toBool());
                QCOMPARE(a->configScheme()->KCoreConfigSkeleton::findItem("caption")->property().toString(),"saved in native profile");
            }
        }
        QCOMPARE(configured,1);QVERIFY(runtime.setSkin("default"));
    }
    void profileRecoveryFromExplicitSnapshot() {
        const QDir config(qEnvironmentVariable("XDG_CONFIG_HOME"));const auto root=config.filePath("bwm-ui-recovery-profile");
        QVERIFY(!QFileInfo::exists(root));const auto stagePath=config.filePath("bwm-native-staged");QVERIFY(!QFileInfo::exists(stagePath));
        struct RemoveStage{QString path;~RemoveStage(){QDir(path).removeRecursively();}} remove{stagePath};
        const auto readBytes=[](const QString &path){QFile file(path);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const auto writeBytes=[](const QString &path,const QByteArray &bytes){QSaveFile file(path);return file.open(QIODevice::WriteOnly) && file.write(bytes)==bytes.size() && file.commit();};
        const auto hash=[](const QByteArray &bytes){return QString::fromLatin1(QCryptographicHash::hash(bytes,QCryptographicHash::Sha256).toHex());};
        const QByteArray legacy=R"({"bar":{"plasma":{"edge":"bottom","thickness":44,"style":"opaque"}}})";
        const QJsonObject widget{{"package","org.bwm.r4.shared-config"},{"nativeSettings",QJsonObject{{"enabled",false},{"caption","recovered-native-option"}}}};
        const QJsonObject plan{{"version",1},{"legacyJson",QString::fromUtf8(legacy)},{"sourceSha256",hash(legacy)},
            {"panels",QJsonArray{QJsonObject{{"outputDescription","BWM Test Recovery A A"},{"containmentPackage","org.kde.panel"},{"widgets",QJsonArray{widget}}}}}};
        const auto planPath=config.filePath("bwm-recovery-plan.json");QVERIFY(writeBytes(planPath,QJsonDocument(plan).toJson()));
        BwmMigration::stage(planPath);
        {KConfig layout(stagePath+"/layout",KConfig::SimpleConfig);KConfigGroup(&layout,"Vendor").writeEntry("Keep","layout-recovery");QVERIFY(layout.sync());
         KConfig views(stagePath+"/plasmashellrc",KConfig::SimpleConfig);KConfigGroup(&views,"Vendor").writeEntry("Keep","views-recovery");QVERIFY(views.sync());}
        const auto imported=ProfileStore::importStage(stagePath,root);const auto headPath=root+"/head.json";
        auto head=QJsonDocument::fromJson(readBytes(headPath)).object();head["VendorKeep"]="head-recovery";QVERIFY(writeBytes(headPath,QJsonDocument(head).toJson()));
        QJsonObject checkpoint;
        {
            ProfileStore owner(root);checkpoint=owner.checkpoint();
            QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,checkpoint.value("snapshot").toString()),std::runtime_error);
        }
        const auto snapshot=checkpoint.value("snapshot").toString(),snapshotDir=checkpoint.value("directory").toString();
        const auto originalHead=readBytes(headPath),originalLayout=readBytes(imported.value("layoutFile").toString());
        auto retained=KSharedConfig::openConfig(imported.value("layoutFile").toString(),KConfig::SimpleConfig);
        // An unreadable current generation prevents ordinary restore, but not
        // explicit snapshot recovery. Keep the broken generation untouched.
        QVERIFY(QFile::remove(imported.value("layoutFile").toString()));
        QVERIFY_EXCEPTION_THROWN((void)ProfileStore(root),std::runtime_error);
        auto recovered=ProfileStore::recover(root,snapshot);QCOMPARE(recovered.value("status").toString(),"native-profile-recovered");
        QVERIFY(!recovered.value("activationAllowed").toBool());QVERIFY(recovered.value("previousHeadPresent").toBool());
        QVERIFY(recovered.value("generation")!=imported.value("generation"));
        QCOMPARE(readBytes(recovered.value("recoveryDirectory").toString()+"/head.json"),originalHead);
        const auto record=QJsonDocument::fromJson(readBytes(recovered.value("recoveryDirectory").toString()+"/recovery.json")).object();
        QCOMPARE(record.value("previousHeadSha256").toString(),hash(originalHead));QCOMPARE(record.value("snapshot").toString(),snapshot);
        for(const auto &name:{"layout","plasmashellrc","legacy.json","report.json","bindings.json"})
            QCOMPARE(readBytes(QFileInfo(recovered.value("layoutFile").toString()).absolutePath()+'/'+name),readBytes(snapshotDir+'/'+name));
        QVERIFY(!QFileInfo::exists(imported.value("layoutFile").toString()));
        KConfigGroup(retained,"LateOldOwner").writeEntry("Keep","old-only");QVERIFY(retained->sync());
        QCOMPARE(readBytes(recovered.value("layoutFile").toString()),originalLayout);
        QCOMPARE(QJsonDocument::fromJson(readBytes(headPath)).object().value("VendorKeep").toString(),"head-recovery");
        // No usable head is needed, including no file at all. Every recovery gets
        // a new path and an exact record, rather than overwriting an old archive.
        for(const auto &broken:{QByteArray("{broken"),QByteArray(),QByteArray("[]"),QByteArray("{\"version\":1,\"generation\":\"../bad\",\"VendorKeep\":42}")}) {
            QVERIFY(writeBytes(headPath,broken));QVERIFY_EXCEPTION_THROWN((void)ProfileStore(root),std::runtime_error);
            const auto before=recovered.value("layoutFile");recovered=ProfileStore::recover(root,snapshot);
            QVERIFY(recovered.value("layoutFile")!=before);QVERIFY(recovered.value("previousHeadPresent").toBool());
            QCOMPARE(readBytes(recovered.value("recoveryDirectory").toString()+"/head.json"),broken);
            QCOMPARE(readBytes(recovered.value("layoutFile").toString()),originalLayout);
        }
        QCOMPARE(QJsonDocument::fromJson(readBytes(headPath)).object().value("VendorKeep").toInt(),42);
        QVERIFY(QFile::remove(headPath));recovered=ProfileStore::recover(root,snapshot);QVERIFY(!recovered.value("previousHeadPresent").toBool());
        QVERIFY(!QFileInfo::exists(recovered.value("recoveryDirectory").toString()+"/head.json"));
        QVERIFY(QJsonDocument::fromJson(readBytes(recovered.value("recoveryDirectory").toString()+"/recovery.json")).object().value("previousHeadSha256").isNull());
        const auto goodHead=readBytes(headPath);const auto manifestPath=snapshotDir+"/snapshot.json";const auto manifest=readBytes(manifestPath);
        const auto generations=QDir(root+"/generations").entryList(QDir::Dirs|QDir::NoDotAndDotDot);
        const auto recoveries=QDir(root+"/recoveries").entryList(QDir::Dirs|QDir::NoDotAndDotDot);
        const auto unchanged=[&]{return readBytes(headPath)==goodHead && QDir(root+"/generations").entryList(QDir::Dirs|QDir::NoDotAndDotDot)==generations &&
            QDir(root+"/recoveries").entryList(QDir::Dirs|QDir::NoDotAndDotDot)==recoveries;};
        for(const auto &invalid:{QString("../escape"),QString(""),QString(32,'0'),QString(32,'A')}) {
            QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,invalid),std::runtime_error);QVERIFY(unchanged());
        }
        QVERIFY(writeBytes(snapshotDir+"/layout",originalLayout+"\n[Changed]\nUnknown=1\n"));
        QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);QVERIFY(unchanged());
        QVERIFY(writeBytes(snapshotDir+"/layout",originalLayout));
        auto invalidManifest=QJsonDocument::fromJson(manifest).object();auto hashes=invalidManifest.value("files").toObject();hashes.remove("layout");invalidManifest["files"]=hashes;
        QVERIFY(writeBytes(manifestPath,QJsonDocument(invalidManifest).toJson()));
        QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);QVERIFY(unchanged());
        // Rehashing invalid native data must not bypass the Corona/binding check.
        const QByteArray invalidLayout="[Containments][999]\nplugin=org.kde.panel\n";
        QVERIFY(writeBytes(snapshotDir+"/layout",invalidLayout));invalidManifest=QJsonDocument::fromJson(manifest).object();
        hashes=invalidManifest.value("files").toObject();hashes["layout"]=hash(invalidLayout);invalidManifest["files"]=hashes;
        QVERIFY(writeBytes(manifestPath,QJsonDocument(invalidManifest).toJson()));
        QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);QVERIFY(unchanged());
        QVERIFY(writeBytes(snapshotDir+"/layout",originalLayout));QVERIFY(writeBytes(manifestPath,manifest));
        // Refuse a future head schema and aliases, without touching their target.
        QVERIFY(writeBytes(headPath,"{\"version\":2,\"generation\":\"future\"}"));
        QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);
        QCOMPARE(readBytes(headPath),QByteArray("{\"version\":2,\"generation\":\"future\"}"));QVERIFY(QFile::remove(headPath));
        const auto foreign=config.filePath("recovery-foreign.json");QVERIFY(writeBytes(foreign,"do-not-change"));
        QVERIFY(QFile::link(foreign,headPath));QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);
        QCOMPARE(readBytes(foreign),QByteArray("do-not-change"));QVERIFY(QFile::remove(headPath));
        QVERIFY(QFile::link(foreign+"-missing",headPath));QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);QVERIFY(QFile::remove(headPath));
        QVERIFY(QDir().mkdir(headPath));QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);QVERIFY(QDir().rmdir(headPath));
        QVERIFY(writeBytes(headPath,goodHead));
        QVERIFY(QDir().rename(root+"/recoveries",root+"/recoveries-saved"));QTemporaryDir outside;QVERIFY(outside.isValid());
        QVERIFY(QFile::link(outside.path(),root+"/recoveries"));QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);
        QCOMPARE(readBytes(headPath),goodHead);QCOMPARE(QDir(root+"/generations").entryList(QDir::Dirs|QDir::NoDotAndDotDot),generations);
        QVERIFY(QDir(outside.path()).entryList(QDir::AllEntries|QDir::NoDotAndDotDot|QDir::Hidden).isEmpty());
        QVERIFY(QFile::remove(root+"/recoveries"));QVERIFY(QDir().rename(root+"/recoveries-saved",root+"/recoveries"));
        QVERIFY(QDir().rename(snapshotDir,snapshotDir+"-saved"));QVERIFY(QFile::link(snapshotDir+"-saved",snapshotDir));
        QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root,snapshot),std::runtime_error);QVERIFY(unchanged());
        QVERIFY(QFile::remove(snapshotDir));QVERIFY(QDir().rename(snapshotDir+"-saved",snapshotDir));
        QVERIFY(QFile::link(root,root+"-alias"));QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(root+"-alias",snapshot),std::runtime_error);QVERIFY(unchanged());QVERIFY(QFile::remove(root+"-alias"));
        // The separate process test and CLI roundtrip consume this profile.
        QVERIFY(writeBytes(config.filePath("bwm-recovery-snapshot.txt"),snapshot.toUtf8()));
    }
    void profileRecoveryFreshProcessReadback() {
        ProfileStore profile(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-ui-recovery-profile"));
        QVERIFY(!profile.info().value("activationAllowed").toBool());QCOMPARE(profile.assignments().size(),1);
        TestCorona corona;corona.loadLayout(profile.layoutFile());QCOMPARE(corona.containments().size(),1);
        const auto *panel=corona.containments().first();QCOMPARE(panel->applets().size(),1);auto *applet=panel->applets().first();
        QCOMPARE(applet->pluginMetaData().pluginId(),"org.bwm.r4.shared-config");
        QVERIFY(!applet->configScheme()->KCoreConfigSkeleton::findItem("enabled")->property().toBool());
        QCOMPARE(applet->configScheme()->KCoreConfigSkeleton::findItem("caption")->property().toString(),"recovered-native-option");
        QCOMPARE(KConfigGroup(corona.config(),"Vendor").readEntry("Keep",QString()),"layout-recovery");
        KConfig views(profile.viewSettingsFile(),KConfig::SimpleConfig);QCOMPARE(KConfigGroup(&views,"Vendor").readEntry("Keep",QString()),"views-recovery");
    }
    void profileRecoveryUsesXdgAuthorityAndChildLease() {
        const auto fixtures=QDir(QStringLiteral(BWM_SHELL_SOURCE_DIR)+"/../../../tests").canonicalPath();QVERIFY(!fixtures.isEmpty());
        QTemporaryDir state(fixtures+"/bwm-r4-recovery-state-XXXXXX");QVERIFY(state.isValid());QVERIFY(!state.path().startsWith(QDir::tempPath()+"/"));
        struct StateEnvironment {
            QByteArray previous=qgetenv("XDG_STATE_HOME");bool existed=qEnvironmentVariableIsSet("XDG_STATE_HOME");
            ~StateEnvironment(){if(existed)qputenv("XDG_STATE_HOME",previous);else qunsetenv("XDG_STATE_HOME");}
        } environment;
        qputenv("XDG_STATE_HOME",state.path().toUtf8());
        const auto readBytes=[](const QString &path){QFile file(path);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const auto writeBytes=[](const QString &path,const QByteArray &bytes){QSaveFile file(path);return file.open(QIODevice::WriteOnly) && file.write(bytes)==bytes.size() && file.commit();};
        ProfileStore source(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-ui-recovery-profile"));
        const auto exported=source.exportToState("recovery-fixture");const auto root=exported.value("directory").toString();
        QCOMPARE(exported.value("storage").toString(),"xdg-state");
        const auto snapshots=QDir(root+"/snapshots").entryList(QDir::Dirs|QDir::NoDotAndDotDot);QCOMPARE(snapshots.size(),1);
        const auto snapshot=snapshots.first(),oldGeneration=exported.value("generation").toString();
        const auto recover=[&](QProcess &child){child.start(QCoreApplication::applicationDirPath()+"/bwm-plasma-host",{"--recover-profile",root+"/snapshots/"+snapshot});return child.waitForFinished(15000);};
        {
            ProfileStore owner(root);QVERIFY(writeBytes(root+"/head.json","{broken-state-head"));
            QProcess child;QVERIFY(recover(child));QCOMPARE(child.exitStatus(),QProcess::NormalExit);QCOMPARE(child.exitCode(),7);
            QVERIFY(child.readAllStandardError().contains("Another process owns"));QCOMPARE(readBytes(root+"/head.json"),QByteArray("{broken-state-head"));
        }
        QProcess child;QVERIFY(recover(child));QCOMPARE(child.exitStatus(),QProcess::NormalExit);QCOMPARE(child.exitCode(),0);
        const auto recovered=QJsonDocument::fromJson(child.readAllStandardOutput()).object();QCOMPARE(recovered.value("storage").toString(),"xdg-state");
        QVERIFY(recovered.value("generation").toString()!=oldGeneration);QVERIFY(!recovered.value("activationAllowed").toBool());
        QCOMPARE(readBytes(recovered.value("recoveryDirectory").toString()+"/head.json"),QByteArray("{broken-state-head"));
        QCOMPARE(readBytes(recovered.value("layoutFile").toString()),readBytes(source.layoutFile()));
        QVERIFY(QFileInfo::exists(root+"/generations/"+oldGeneration+"/layout"));
        QProcess fresh;fresh.start(QCoreApplication::applicationDirPath()+"/bwm-plasma-host",{"--profile-info",root});QVERIFY(fresh.waitForFinished(15000));
        QCOMPARE(fresh.exitCode(),0);QCOMPARE(QJsonDocument::fromJson(fresh.readAllStandardOutput()).object().value("generation"),recovered.value("generation"));
        QTemporaryDir unrelated(fixtures+"/bwm-r4-recovery-unrelated-XXXXXX");QVERIFY(unrelated.isValid());
        QVERIFY_EXCEPTION_THROWN(ProfileStore::recover(unrelated.path(),snapshot),std::runtime_error);
        QVERIFY(QDir(unrelated.path()).entryList(QDir::AllEntries|QDir::NoDotAndDotDot|QDir::Hidden).isEmpty());
    }
    void profileSelectionTransactionsAndSelectedServer() {
        const auto fixtures=QDir(QStringLiteral(BWM_SHELL_SOURCE_DIR)+"/../../../tests").canonicalPath();QVERIFY(!fixtures.isEmpty());
        QTemporaryDir state(fixtures+"/bwm-r4-selection-state-XXXXXX");QVERIFY(state.isValid());QVERIFY(!state.path().startsWith(QDir::tempPath()+"/"));
        struct StateEnvironment {
            QByteArray previous=qgetenv("XDG_STATE_HOME");bool existed=qEnvironmentVariableIsSet("XDG_STATE_HOME");
            ~StateEnvironment(){if(existed)qputenv("XDG_STATE_HOME",previous);else qunsetenv("XDG_STATE_HOME");}
        } environment;
        qputenv("XDG_STATE_HOME",state.path().toUtf8());
        const auto readBytes=[](const QString &path){QFile file(path);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const auto writeBytes=[](const QString &path,const QByteArray &bytes){QSaveFile file(path);return file.open(QIODevice::WriteOnly) && file.write(bytes)==bytes.size() && file.commit();};
        const auto initial=ProfileSelection::info();QCOMPARE(initial.value("revision").toInteger(),0);QVERIFY(initial.value("selectedProfile").isNull());
        QVERIFY(!QFileInfo::exists(state.path()+"/bwm"));QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);
        for(const auto &invalid:{"../escape","/tmp/profile","",".selection","with space"})
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::select(invalid,0),std::runtime_error);
        QVERIFY(!QFileInfo::exists(state.path()+"/bwm"));
        ProfileStore source(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-ui-recovery-profile"));
        const auto first=source.exportToState("selected-a"),second=source.exportToState("selected-b");
        const auto root=first.value("directory").toString(),other=second.value("directory").toString();
        auto selected=ProfileSelection::select("selected-a",0);QCOMPARE(selected.value("revision").toInteger(),1);QVERIFY(selected.value("changed").toBool());
        QVERIFY(!selected.value("activationAllowed").toBool());QVERIFY(!selected.value("replacementReady").toBool());
        const auto selectionFile=selected.value("selectionFile").toString();const auto bytes=readBytes(selectionFile);
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::select("selected-b",0),std::runtime_error);QCOMPARE(readBytes(selectionFile),bytes);
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::select("missing-profile",1),std::runtime_error);QCOMPARE(readBytes(selectionFile),bytes);
        selected=ProfileSelection::select("selected-a",1);QVERIFY(!selected.value("changed").toBool());QCOMPARE(readBytes(selectionFile),bytes);
        QProcess fresh;fresh.start(QCoreApplication::applicationDirPath()+"/bwm-plasma-host",{"--profile-selection-info"});QVERIFY(fresh.waitForFinished(15000));QCOMPARE(fresh.exitCode(),0);
        const auto reopened=QJsonDocument::fromJson(fresh.readAllStandardOutput()).object();QCOMPARE(reopened.value("selectedProfile").toString(),"selected-a");QVERIFY(reopened.value("profileValidated").toBool());
        QJsonObject snapshot;
        {
            auto owner=ProfileSelection::openSelected();QCOMPARE(owner->info().value("directory").toString(),root);
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::select("selected-a",1),std::runtime_error);
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::select("selected-b",1),std::runtime_error);
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::clear(1),std::runtime_error);QCOMPARE(readBytes(selectionFile),bytes);
            const auto busy=ProfileSelection::info();QVERIFY(!busy.value("profileValidated").toBool());QVERIFY(busy.contains("profileError"));
            {TestCorona corona;corona.loadLayout(owner->layoutFile());auto *applet=corona.containments().first()->applets().first();
                auto *caption=applet->configScheme()->KCoreConfigSkeleton::findItem("caption");QVERIFY(caption);caption->setProperty("selected-native-option");
                applet->configScheme()->save();corona.saveLayout(owner->layoutFile());QVERIFY(corona.config()->sync());}
            snapshot=owner->checkpoint();
        }
        // Selected intent follows recovery generations; native options remain in
        // the KDE files rather than being duplicated in the selection pointer.
        const auto recovered=ProfileStore::recover(root,snapshot.value("snapshot").toString());QCOMPARE(readBytes(selectionFile),bytes);
        {auto owner=ProfileSelection::openSelected();QCOMPARE(owner->info().value("generation"),recovered.value("generation"));
            TestCorona corona;corona.loadLayout(owner->layoutFile());auto *applet=corona.containments().first()->applets().first();
            QCOMPARE(applet->configScheme()->KCoreConfigSkeleton::findItem("caption")->property().toString(),"selected-native-option");}
        auto metadata=QJsonDocument::fromJson(bytes).object();metadata["VendorKeep"]=42;QVERIFY(writeBytes(selectionFile,QJsonDocument(metadata).toJson()));
        selected=ProfileSelection::select("selected-b",1);QCOMPARE(selected.value("revision").toInteger(),2);
        QCOMPARE(QJsonDocument::fromJson(readBytes(selectionFile)).object().value("VendorKeep").toInt(),42);
        QVERIFY(writeBytes(other+"/head.json","{broken"));QVERIFY(!ProfileSelection::info().value("profileValidated").toBool());
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);
        selected=ProfileSelection::clear(2);QCOMPARE(selected.value("revision").toInteger(),3);QVERIFY(selected.value("selectedProfile").isNull());
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);ProfileSelection::select("selected-a",3);
        QVERIFY(QDir().rename(root,root+"-saved"));QVERIFY(!ProfileSelection::info().value("profileValidated").toBool());
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);selected=ProfileSelection::clear(4);QCOMPARE(selected.value("revision").toInteger(),5);
        QVERIFY(QDir().rename(root+"-saved",root));ProfileSelection::select("selected-a",5);
        metadata=QJsonDocument::fromJson(readBytes(selectionFile)).object();metadata["sourceSha256"]=QString(64,'0');QVERIFY(writeBytes(selectionFile,QJsonDocument(metadata).toJson()));
        QVERIFY(!ProfileSelection::info().value("profileValidated").toBool());QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);
        selected=ProfileSelection::select("selected-a",6);QCOMPARE(selected.value("revision").toInteger(),7);
        const auto good=readBytes(selectionFile);
        for(const auto &invalid:{QByteArray("{broken"),QByteArray("{\"version\":2}"),QByteArray("{\"version\":1,\"revision\":true,\"profile\":null}"),
                QByteArray("{\"version\":1,\"revision\":1.5,\"profile\":null}"),QByteArray("{\"version\":1,\"revision\":9007199254740992,\"profile\":null}"),
                QByteArray("{\"version\":1,\"revision\":1,\"profile\":\"../bad\"}")}) {
            QVERIFY(writeBytes(selectionFile,invalid));QVERIFY_EXCEPTION_THROWN(ProfileSelection::info(),std::runtime_error);
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::clear(7),std::runtime_error);QCOMPARE(readBytes(selectionFile),invalid);
        }
        QVERIFY(writeBytes(selectionFile,good));
        metadata=QJsonDocument::fromJson(good).object();metadata["revision"]=qint64(9007199254740991LL);QVERIFY(writeBytes(selectionFile,QJsonDocument(metadata).toJson()));
        const auto saturated=readBytes(selectionFile);QVERIFY_EXCEPTION_THROWN(ProfileSelection::clear(9007199254740991LL),std::runtime_error);
        QCOMPARE(readBytes(selectionFile),saturated);QVERIFY(writeBytes(selectionFile,good));
        {QLockFile lock(QFileInfo(selectionFile).absolutePath()+"/owner.lock");QVERIFY(lock.tryLock(0));
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::info(),std::runtime_error);QVERIFY_EXCEPTION_THROWN(ProfileSelection::clear(7),std::runtime_error);
            QVERIFY_EXCEPTION_THROWN(ProfileSelection::openSelected(),std::runtime_error);QCOMPARE(readBytes(selectionFile),good);}
        const auto outside=state.path()+"/untouched.json";QVERIFY(writeBytes(outside,"do-not-change"));QVERIFY(QFile::remove(selectionFile));QVERIFY(QFile::link(outside,selectionFile));
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::info(),std::runtime_error);QVERIFY_EXCEPTION_THROWN(ProfileSelection::clear(7),std::runtime_error);
        QCOMPARE(readBytes(outside),QByteArray("do-not-change"));QVERIFY(QFile::remove(selectionFile));QVERIFY(writeBytes(selectionFile,good));
        // Exercise the real selected-profile server, with no visible outputs.
        QTemporaryDir control;QVERIFY(control.isValid());const auto token=QString(64,'a');
        const auto command=[&](int revision,const QString &action){return writeBytes(control.path()+"/control.json",QJsonDocument(QJsonObject{
            {"version",1},{"token",token},{"revision",revision},{"command",action},{"skin","default"}}).toJson()) &&
            QFile::setPermissions(control.path()+"/control.json",QFile::ReadOwner|QFile::WriteOwner);};
        QVERIFY(command(0,"skin"));QProcess server;auto env=QProcessEnvironment::systemEnvironment();
        env.insert("BWM_R4_CONTROL_DIR",control.path());env.insert("BWM_R4_SESSION_TOKEN",token);server.setProcessEnvironment(env);
        server.start(QCoreApplication::applicationDirPath()+"/bwm-plasma-host",{"--serve-selected-profile"});
        QTRY_VERIFY_WITH_TIMEOUT(QFileInfo::exists(control.path()+"/ack.json") || server.state()==QProcess::NotRunning,5000);
        QVERIFY2(server.state()!=QProcess::NotRunning,server.readAllStandardError().constData());
        const auto ack=QJsonDocument::fromJson(readBytes(control.path()+"/ack.json")).object();QVERIFY(ack.value("ok").toBool());
        QVERIFY_EXCEPTION_THROWN(ProfileSelection::clear(7),std::runtime_error);QCOMPARE(readBytes(selectionFile),good);
        QVERIFY(command(1,"stop"));QVERIFY(server.waitForFinished(15000));QCOMPARE(server.exitStatus(),QProcess::NormalExit);QCOMPARE(server.exitCode(),0);
        QCOMPARE(QJsonDocument::fromJson(server.readAllStandardOutput()).object().value("status").toString(),"native-profile-checkpoint");
        QVERIFY(ProfileSelection::info().value("profileValidated").toBool());selected=ProfileSelection::clear(7);QCOMPARE(selected.value("revision").toInteger(),8);
        const auto cleared=readBytes(selectionFile);QVERIFY(!ProfileSelection::clear(8).value("changed").toBool());QCOMPARE(readBytes(selectionFile),cleared);
    }
    void profileExportKeepsSnapshotsInXdgStateOutsideTmp() {
        const auto fixtures=QDir(QStringLiteral(BWM_SHELL_SOURCE_DIR)+"/../../../tests").canonicalPath();QVERIFY(!fixtures.isEmpty());
        QTemporaryDir state(fixtures+"/bwm-r4-state-XXXXXX");QVERIFY(state.isValid());
        QVERIFY(!state.path().startsWith(QDir::tempPath()+"/"));
        struct StateEnvironment {
            QByteArray previous=qgetenv("XDG_STATE_HOME");bool existed=qEnvironmentVariableIsSet("XDG_STATE_HOME");
            ~StateEnvironment(){if(existed)qputenv("XDG_STATE_HOME",previous);else qunsetenv("XDG_STATE_HOME");}
        } environment;
        qputenv("XDG_STATE_HOME",state.path().toUtf8());
        QCOMPARE(QStandardPaths::writableLocation(QStandardPaths::GenericStateLocation),state.path());
        ProfileStore source(QDir(qEnvironmentVariable("XDG_CONFIG_HOME")).filePath("bwm-ui-native-profile"));
        const auto readBytes=[](const QString &path){QFile file(path);return file.open(QIODevice::ReadOnly)?file.readAll():QByteArray();};
        const auto layout=readBytes(source.layoutFile()),views=readBytes(source.viewSettingsFile());
        const auto exported=source.exportToState("kept-native");QCOMPARE(exported.value("storage").toString(),"xdg-state");
        const auto root=exported.value("directory").toString();
        QCOMPARE(root,state.path()+"/bwm/plasma/panel-profiles/kept-native");QVERIFY(!root.startsWith(QDir::tempPath()+"/"));
        QVERIFY(!exported.value("activationAllowed").toBool());QCOMPARE(exported.value("copiedSnapshots").toInt(),2);
        QCOMPARE(readBytes(exported.value("layoutFile").toString()),layout);QCOMPARE(readBytes(exported.value("viewSettingsFile").toString()),views);
        const auto sourceRoot=source.info().value("directory").toString();
        const auto snapshots=QDir(sourceRoot+"/snapshots").entryList(QDir::Dirs|QDir::NoDotAndDotDot,QDir::Name);
        QCOMPARE(QDir(root+"/snapshots").entryList(QDir::Dirs|QDir::NoDotAndDotDot,QDir::Name),snapshots);
        for(const auto &snapshot:snapshots)for(const auto &file:{"layout","plasmashellrc","legacy.json","report.json","bindings.json","snapshot.json"})
            QCOMPARE(readBytes(root+"/snapshots/"+snapshot+'/'+file),readBytes(sourceRoot+"/snapshots/"+snapshot+'/'+file));
        const auto tampered=sourceRoot+"/snapshots/"+snapshots.first()+"/plasmashellrc";const auto saved=readBytes(tampered);
        {QFile file(tampered);QVERIFY(file.open(QIODevice::Append));file.write("\n[Changed]\nInvalid=1\n");}
        QVERIFY_EXCEPTION_THROWN(source.exportToState("bad-history"),std::runtime_error);
        QVERIFY(!QFileInfo::exists(state.path()+"/bwm/plasma/panel-profiles/bad-history"));
        {QFile file(tampered);QVERIFY(file.open(QIODevice::WriteOnly));file.write(saved);}
        QVERIFY_EXCEPTION_THROWN(source.exportToState("kept-native"),std::runtime_error);
        for(const auto &invalid:{"../escape","/absolute","a/b",".hidden",""})QVERIFY_EXCEPTION_THROWN(source.exportToState(invalid),std::runtime_error);
        {
            ProfileStore persistent(root);QCOMPARE(persistent.assignments(),source.assignments());
            const auto snapshot=snapshots.first();persistent.restore(snapshot);
            QCOMPARE(readBytes(persistent.layoutFile()),readBytes(root+"/snapshots/"+snapshot+"/layout"));
            QCOMPARE(readBytes(source.layoutFile()),layout); // state restore never mutates source profile
        }
        const auto head=QJsonDocument::fromJson(readBytes(root+"/head.json")).object();QCOMPARE(head.value("VendorKeep").toString(),"head-unknown");
        QTemporaryDir unrelated(fixtures+"/bwm-r4-unrelated-XXXXXX");QVERIFY(unrelated.isValid());
        QVERIFY_EXCEPTION_THROWN((void)ProfileStore(unrelated.path()),std::runtime_error);
        QCOMPARE(QDir(unrelated.path()).entryList(QDir::Files|QDir::NoDotAndDotDot).size(),0);
        // A state authority alias must not redirect publication to another folder.
        const auto base=state.path()+"/bwm/plasma/panel-profiles";
        QVERIFY(QDir().rename(base,base+"-saved"));QVERIFY(QFile::link(unrelated.path(),base));
        QVERIFY_EXCEPTION_THROWN(source.exportToState("redirected"),std::runtime_error);
        QVERIFY(!QFileInfo::exists(unrelated.path()+"/redirected"));QVERIFY(QFile::remove(base));QVERIFY(QDir().rename(base+"-saved",base));
    }
};
QTEST_MAIN(UiTest)
#include "test-ui.moc"
