// SPDX-License-Identifier: GPL-2.0-or-later
// Experimental R4 host. Never owns a Plasma D-Bus service or starts plasmashell.
#include <QApplication>
#include <QQuickWindow>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTimer>
#include <QElapsedTimer>
#include <QDir>
#include <QFileInfo>
#include <QLockFile>
#include <QAction>
#include <QScreen>
#include <QMetaProperty>
#include <QRegularExpression>
#include <KConfigLoader>
#include <KConfigPropertyMap>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/AppletQuickItem>
#include <PlasmaQuick/ConfigView>
#include <PlasmaQuick/ConfigModel>
#include <PlasmaQuick/SharedQmlEngine>
#include <cstdio>
#include <csignal>
#include "configurationsession.h"
#include "catalog.h"
#include "surfaces.h"
#include "migration.h"
#include "panelprobe.h"
#include "panelsession.h"
#include "themeinventory.h"
#include "viewcorona.h"
#include "kns.h"
#include "packagewindows.h"
#include "panelviewhost.h"
#include "panelruntime.h"
#include "taskpreview.h"
#include "tasklauncher.h"
#include "previewappearance.h"
#include "taskthumbnail.h"
#include "outputidentity.h"
#include "runtimecontrol.h"
#include "desktopsessioncheck.h"
#include "profilestore.h"
#include "trayprobe.h"
#include <memory>
#include <QtPlugin>
Q_IMPORT_PLUGIN(BwmWindowSystemPlugin)
int main(int argc, char **argv) {
    if(argc==3 && QString::fromLocal8Bit(argv[1])=="--stage-preview-appearance") {
        // This operation only reads/writes native configuration data. In
        // particular, do not initialize a platform theme against the empty store.
        QCoreApplication app(argc,argv);
        QJsonObject report;QString error;
        if(!stagePreviewAppearance(QString::fromLocal8Bit(argv[2]),&report,&error)) {
            fprintf(stderr,"%s\n",qPrintable(error));return 2;
        }
        puts(QJsonDocument(report).toJson(QJsonDocument::Compact).constData());return 0;
    }
    const bool desktopPreview=argc==3 && (QString::fromLocal8Bit(argv[1])=="--follow-panel-preview" ||
        QString::fromLocal8Bit(argv[1])=="--serve-profile");
    if(!desktopPreview){qunsetenv("BWM_R4_DESKTOP_ACTIONS");qunsetenv("BWM_R4_DESKTOP_RUNTIME");qunsetenv("BWM_R4_DESKTOP_CONFIG");}
    if(!desktopPreview){qunsetenv("BWM_R4_TASK_ACTIONS");qunsetenv("BWM_R4_TASK_RUNTIME");qunsetenv("BWM_R4_TASK_CONFIG");}
    if(!desktopPreview)qunsetenv("BWM_R4_NATIVE_DESKTOPS");
    if(!desktopPreview)qunsetenv("BWM_R4_TASK_ALL_DESKTOPS");
    if(!desktopPreview)qunsetenv("BWM_R4_TASK_THUMBNAILS");
    // Same platform setup as plasmashell 6.7.5 (shell/main.cpp): Qt Wayland otherwise moves
    // every top-level QWindow to its output origin, so mapToGlobal() and the positions that
    // packages request for their own PlasmaCore.Dialog are lost. Child processes do not inherit it.
    qputenv("QT_WAYLAND_DISABLE_FIXED_POSITIONS",{});
    QQuickWindow::setDefaultAlphaBuffer(true);
    QApplication app(argc,argv);
    qunsetenv("QT_WAYLAND_DISABLE_FIXED_POSITIONS");
    if(app.arguments().value(1)=="--check-native-desktops-session"){
        const auto status=nativeDesktopSessionSnapshot(app.arguments().mid(2));
        puts(QJsonDocument(status).toJson(QJsonDocument::Compact).constData());
        return status.value("ready").toBool()?0:2;
    }
    if(app.arguments().value(1)=="--check-native-desktops-focus-cycle"){
        const auto status=nativeDesktopFocusCycle(app.arguments().value(2),app.arguments().mid(3));
        puts(QJsonDocument(status).toJson(QJsonDocument::Compact).constData());
        return status.value("passed").toBool()?0:2;
    }
    if(app.arguments().value(1)=="--check-native-desktops-workspace-cycle"){
        const auto status=nativeDesktopWorkspaceCycle(app.arguments().value(2),app.arguments().value(3),app.arguments().mid(4));
        puts(QJsonDocument(status).toJson(QJsonDocument::Compact).constData());
        return status.value("passed").toBool()?0:2;
    }
    BwmSurface::registerTypes();
    PanelViewHost::registerTypes();
    app.setApplicationName("bwm-plasma-host");
    const auto args=app.arguments();
    if(args.size()==2 && args[1]=="--check-thumbnail-compositor"){
        const auto status=thumbnailCompositorGuardStatus();puts(QJsonDocument::fromVariant(status).toJson().constData());
        return status.value("verified").toBool()?0:2;
    }
    if(args.size()==2 && args[1]=="--launch-task-application")return runNativeTaskLauncher();
    const bool allDesktopTasks=qEnvironmentVariable("BWM_R4_TASK_ALL_DESKTOPS")=="1";
    const bool taskThumbnails=qEnvironmentVariable("BWM_R4_TASK_THUMBNAILS")=="1";
    if(taskThumbnails && !(args.size()==3 && args[1]=="--follow-panel-preview" && qEnvironmentVariable("BWM_R4_TASK_ACTIONS")=="1")){
        fprintf(stderr,"Task thumbnails require a disposable following task preview.\n");return 2;
    }
    if(allDesktopTasks && !(args.size()==3 && args[1]=="--follow-panel-preview" && qEnvironmentVariable("BWM_R4_TASK_ACTIONS")=="1")){
        fprintf(stderr,"All-desktops task mode requires a disposable following task preview, not a saved profile.\n");return 2;
    }
    if(allDesktopTasks){
        for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR"})
            if(!QFileInfo(qEnvironmentVariable(name)).canonicalFilePath().startsWith(QDir::tempPath()+"/")){
                fprintf(stderr,"All-desktops task mode requires disposable XDG directories.\n");return 2;
            }
    }
    if(args.size()==3 && args[1]=="--maximize-fixture") {
        if(!QRegularExpression("^org\\.bwm\\.r4\\.maximize\\.[a-f0-9]{32}$").match(args[2]).hasMatch())return 2;
        for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR"})
            if(!QFileInfo(qEnvironmentVariable(name)).canonicalFilePath().startsWith(QDir::tempPath()+"/"))return 2;
        app.setApplicationName(args[2]);app.setDesktopFileName(args[2]);
        QQuickWindow window;window.setTitle(QStringLiteral("BWM R4 — prueba temporal de maximizado"));
        window.setFlags(Qt::Window|Qt::WindowDoesNotAcceptFocus);window.setColor(QColor("#263238"));window.resize(640,360);
        window.show();QTimer::singleShot(60000,&app,&QCoreApplication::quit);
        return app.exec(); // No self-maximize: the runner uses the existing BWM manager.
    }
    const bool panelFrameProbe=args.size()==3 && args[1]=="--probe-panel-frame";
    const bool followPreview=args.size()==3 && args[1]=="--follow-panel-preview";
    const bool panelPreview=args.size()==3 && (args[1]=="--panel-preview" || args[1]=="--layer-panel-preview" || panelFrameProbe || followPreview);
    const bool runtimePreview=args.size()==3 && (args[1]=="--preview-stage" || args[1]=="--probe-stage-runtime");
    const bool trayProperties=args.size()==3 && args[1]=="--probe-native-tray-properties";
    const bool trayProbe=trayProperties || (args.size()==3 && args[1]=="--probe-native-tray-model");
    const bool exportProfile=args.size()==4 && args[1]=="--export-profile";
    const bool selectionTool=(args.size()==2 && args[1]=="--profile-selection-info") ||
        (args.size()==4 && args[1]=="--select-profile") || (args.size()==3 && args[1]=="--clear-profile-selection");
    const bool serveSelected=args.size()==2 && args[1]=="--serve-selected-profile";
    const bool profileTool=exportProfile || selectionTool || serveSelected || (args.size()==3 && QStringList{"--import-profile","--profile-info","--checkpoint-profile","--restore-profile","--recover-profile","--serve-profile"}.contains(args[1]));
    if(args.size()==2 && args[1]=="--theme-catalog") {
        puts(QJsonDocument(globalThemeInventory()).toJson().constData());return 0;
    }
    if(args.size()>=3 && args.size()<=4 && (args[1]=="--kns-search" || args[1]=="--kns-install" || args[1]=="--kns-uninstall")) {
        // Downloads and installs third-party packages: only into disposable XDG roots.
        for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME"})
            if(!QFileInfo(qEnvironmentVariable(name)).canonicalFilePath().startsWith(QDir::tempPath()+"/")) {
                fprintf(stderr,"KNS cycles require existing temporary XDG_CONFIG_HOME/DATA_HOME/CACHE_HOME roots.\n");return 2;
            }
        const QJsonObject result=args[1]=="--kns-search" ? BwmKns::search(args[2],args.size()==4 ? args[3].toInt() : 0)
            : args[1]=="--kns-install" ? BwmKns::install(args[2]) : BwmKns::uninstall(args[2]);
        puts(QJsonDocument(result).toJson().constData());
        return result.value("errors").toArray().isEmpty() ? 0 : 9;
    }
    if(args.size()==2 && args[1]=="--catalog") {
        Catalog catalog;
        puts(QJsonDocument(QJsonArray::fromVariantList(catalog.entries())).toJson().constData());return 0;
    }
    if((args.size()!=3 && !exportProfile && !selectionTool && !serveSelected) || (!profileTool && !runtimePreview && !panelPreview && !trayProbe && args[1]!="--probe" && args[1]!="--exercise" && args[1]!="--preview" && args[1]!="--layer-preview" && args[1]!="--stage-migration" && args[1]!="--verify-stage" && args[1]!="--probe-stage" && args[1]!="--probe-stage-frame")) { fprintf(stderr,"Usage: bwm-plasma-host --catalog | --probe PACKAGE_ID | --exercise PACKAGE_ID | --preview PACKAGE_ID | --panel-preview PACKAGE_ID | --stage-migration PLAN | --verify-stage DIR | --probe-stage DIR | --probe-stage-frame DIR | --preview-stage DIR | --probe-stage-runtime DIR | --probe-native-tray-model COUNT | --probe-native-tray-properties COUNT | --import-profile STAGE | --profile-info DIR | --checkpoint-profile DIR | --restore-profile SNAPSHOT_DIR | --recover-profile SNAPSHOT_DIR | --serve-profile DIR | --export-profile DIR NAME | --profile-selection-info | --select-profile NAME REVISION | --clear-profile-selection REVISION | --serve-selected-profile\nTests require temporary XDG roots. Profiles do not replace the active panel.\n");return 2; }
    // A probe may execute arbitrary QML. Force the caller to choose an isolated config store.
    for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_RUNTIME_DIR"}) {
        if(!QFileInfo(qEnvironmentVariable(name)).canonicalFilePath().startsWith(QDir::tempPath()+"/")) {
            fprintf(stderr,"Tests require existing temporary XDG_CONFIG_HOME/DATA_HOME/CACHE_HOME/RUNTIME_DIR roots.\n");return 2;
        }
    }
    if (trayProbe) {
        bool validCount = false;
        const int count = args[2].toInt(&validCount);
        if (!validCount || count <= 0 || count > 256 || QGuiApplication::platformName() != QStringLiteral("offscreen") ||
            qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS") != QStringLiteral("unix:path=") + qEnvironmentVariable("XDG_RUNTIME_DIR") + QStringLiteral("/tray-bus")) {
            fprintf(stderr, "Native tray model probe requires a positive count, offscreen Qt and the disposable tray bus.\n");
            return 2;
        }
        const auto result = probeNativeTray(count, trayProperties);
        puts(QJsonDocument(result).toJson(QJsonDocument::Compact).constData());
        return result.value("modelReady").toBool() ? 0 : 2;
    }
    std::unique_ptr<QLockFile> previewOwner;
    if(followPreview) {
        // The Python wrapper handles terminal Ctrl+C, sends the stop transaction,
        // waits for config.sync and removes its registration. Keep the helper in
        // that terminal's group so SIGHUP cannot orphan a detached preview.
        std::signal(SIGINT,SIG_IGN);
        previewOwner=std::make_unique<QLockFile>(qEnvironmentVariable("XDG_CONFIG_HOME")+"/bwm-follow-panel-owner.lock");
        if(!previewOwner->tryLock(0)){fprintf(stderr,"Another preview owns this native layout.\n");return 9;}
    }
    if(profileTool) {
        try {
            QJsonObject result;
            if(selectionTool) {
                if(args[1]=="--profile-selection-info")result=ProfileSelection::info();
                else {
                    bool ok=false;const auto revision=args.last().toLongLong(&ok);
                    if(!ok)throw std::runtime_error("An integer expected selection revision is required");
                    result=args[1]=="--select-profile" ? ProfileSelection::select(args[2],revision) : ProfileSelection::clear(revision);
                }
            }
            else if(exportProfile){ProfileStore profile(args[2]);result=profile.exportToState(args[3]);}
            else if(args[1]=="--import-profile")result=ProfileStore::importStage(args[2],qEnvironmentVariable("XDG_CONFIG_HOME")+"/bwm-native-profile");
            else if(args[1]=="--restore-profile" || args[1]=="--recover-profile") {
                const QFileInfo snapshot(QDir::cleanPath(args[2]));const auto snapshots=snapshot.absoluteDir();
                if(snapshots.dirName()!="snapshots")throw std::runtime_error("A profile snapshot directory is required");
                const auto root=QFileInfo(snapshots.absolutePath()).absolutePath();
                if(args[1]=="--recover-profile")result=ProfileStore::recover(root,snapshot.fileName());
                else {ProfileStore profile(root);result=profile.restore(snapshot.fileName());}
            } else {
                auto owner=serveSelected ? ProfileSelection::openSelected() : std::make_unique<ProfileStore>(args[2]);auto &profile=*owner;
                if(args[1]=="--profile-info")result=profile.info();
                else if(args[1]=="--checkpoint-profile")result=profile.checkpoint();
                else {
                    std::signal(SIGINT,SIG_IGN);app.setQuitOnLastWindowClosed(false);int code=0;
                    {
                        ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
                        corona.loadLayout(profile.layoutFile());PanelRuntime runtime(&corona,profile.viewSettingsFile(),true,nullptr,qEnvironmentVariable("BWM_R4_NATIVE_PANEL_POLICY")=="1");
                        if(!runtime.setAssignments(profile.assignments()))throw std::runtime_error(runtime.error().toStdString());
                        RuntimeControl control(&runtime,qEnvironmentVariable("BWM_R4_CONTROL_DIR"),qEnvironmentVariable("BWM_R4_SESSION_TOKEN"));
                        QObject::connect(&control,&RuntimeControl::stopRequested,&app,&QCoreApplication::quit,Qt::QueuedConnection);
                        if(!control.start())throw std::runtime_error(control.error().toStdString());
                        code=app.exec();runtime.setSkin("default");corona.saveLayout(profile.layoutFile());
                        if(!corona.config()->sync())code=7;
                    } // Release every native config owner before taking the checkpoint.
                    if(code)return code;result=profile.checkpoint();
                }
            }
            puts(QJsonDocument(result).toJson().constData());return 0;
        } catch(const std::exception &e){fprintf(stderr,"%s\n",e.what());return 7;}
    }
    if(runtimePreview) {
        try {
            const auto report=BwmMigration::verify(args[2]);
            if(!report.contains("viewSettingsContractVersion"))throw std::runtime_error("Native runtime preview requires view settings in the stage");
            ViewCorona corona;corona.setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
            corona.loadLayout(args[2]+"/layout");
            QHash<uint,QString> outputs;for(const auto &p:report.value("panels").toArray()) {
                const auto panel=p.toObject();outputs.insert(uint(panel.value("containmentId").toInt()),panel.value("outputDescription").toString());
            }
            const bool probe=args[1]=="--probe-stage-runtime";
            PanelRuntime runtime(&corona,args[2]+"/plasmashellrc",!probe);
            if(!runtime.setAssignments(outputs) || !runtime.setSkin("plasma"))throw std::runtime_error(runtime.error().toStdString());
            if(probe) {
                app.setQuitOnLastWindowClosed(false);
                QTimer::singleShot(500,&app,[&]{
                    QJsonObject result{{"panels",QJsonArray::fromVariantList(runtime.panels())},{"waylandVerified",false},{"activationAllowed",false}};
                    puts(QJsonDocument(result).toJson().constData());app.quit();
                });
            } else {
                bool visible=false;for(const auto &p:runtime.panels())visible=visible || p.toMap().value("visible").toBool();
                if(!visible){fprintf(stderr,"No native panel can be shown: %s\n",QJsonDocument(QJsonArray::fromVariantList(runtime.panels())).toJson(QJsonDocument::Compact).constData());return 8;}
            }
            const int status=app.exec();runtime.setSkin("default");
            corona.saveLayout(args[2]+"/layout");if(!corona.config()->sync())return 7;
            return status;
        } catch(const std::exception &e){fprintf(stderr,"%s\n",e.what());return 7;}
    }
    if(args[1]=="--stage-migration" || args[1]=="--verify-stage" || args[1]=="--probe-stage" || args[1]=="--probe-stage-frame") {
        try {
            const auto report=args[1]=="--stage-migration" ? BwmMigration::stage(args[2]) :
                (args[1]=="--probe-stage" || args[1]=="--probe-stage-frame") ? BwmMigration::probePanel(args[2],QStringLiteral(BWM_SHELL_SOURCE_DIR),args[1]=="--probe-stage-frame") : BwmMigration::verify(args[2]);
            puts(QJsonDocument(report).toJson().constData());return 0;
        } catch(const std::exception &e) {fprintf(stderr,"%s\n",e.what());return 7;}
    }
    auto package=KPackage::PackageLoader::self()->loadPackage("Plasma/Applet",args[2]);
    ViewCorona corona;
    auto shell=KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR));
    if(!shell.isValid()) return 5;
    corona.setKPackage(shell);
    const QString layoutName=panelPreview ? "bwm-plasma-host-panel-appletsrc" : "bwm-plasma-host-appletsrc";
    corona.loadLayout(layoutName);
    auto *containment=corona.containments().isEmpty() ? corona.createContainment(panelPreview ? "org.kde.panel" : "null") : corona.containments().first();
    if(!containment) return 3;
    containment->setFormFactor(Plasma::Types::Horizontal);
    containment->setLocation(Plasma::Types::BottomEdge);
    QList<Plasma::Applet*> existing;
    for(auto *candidate:containment->applets()) if(candidate->pluginMetaData().pluginId()==args[2]) existing.append(candidate);
    const auto instanceOption=qEnvironmentVariable("BWM_R4_PREVIEW_INSTANCES");
    if(!instanceOption.isEmpty() && (!followPreview || (instanceOption!="1" && instanceOption!="2"))){
        fprintf(stderr,"Preview instance count requires a disposable following panel and must be 1 or 2.\n");return 8;
    }
    const int instanceCount=instanceOption=="1"?1:2;
    auto *a=existing.size()>0 ? existing[0] : containment->createApplet(args[2]);
    auto *b=instanceCount==2 ? (existing.size()>1 ? existing[1] : containment->createApplet(args[2])) : nullptr;
    const QList<Plasma::Applet*> previewApplets=b?QList<Plasma::Applet*>{a,b}:QList<Plasma::Applet*>{a};
    std::unique_ptr<PlasmaQuick::SharedQmlEngine> thumbnailEngine;
    if(taskThumbnails){
        thumbnailEngine=std::make_unique<PlasmaQuick::SharedQmlEngine>();QString error;
        if(!installTaskThumbnails(thumbnailEngine->engine().get(),&error)){fprintf(stderr,"%s\n",qPrintable(error));return 8;}
    }
    if(allDesktopTasks){
        QString error;
        if(!prepareAllDesktopTaskPreview(previewApplets,&error)){fprintf(stderr,"%s\n",qPrintable(error));return 8;}
    }
    if(followPreview) {
        const auto output=qEnvironmentVariable("BWM_R4_OUTPUT");
        if(output.isEmpty()){fprintf(stderr,"A persistent output description is required for the following preview.\n");return 8;}
        app.setQuitOnLastWindowClosed(false);
        PanelRuntime runtime(&corona,"plasmashellrc",true,nullptr,qEnvironmentVariable("BWM_R4_NATIVE_PANEL_POLICY")=="1");
        runtime.setOutputMovesAllowed(true); // Disposable preview: its binding is --output itself.
        if(!runtime.setAssignments({{containment->id(),output}})){fprintf(stderr,"%s\n",qPrintable(runtime.error()));return 8;}
        RuntimeControl control(&runtime,qEnvironmentVariable("BWM_R4_CONTROL_DIR"),qEnvironmentVariable("BWM_R4_SESSION_TOKEN"));
        QObject::connect(&control,&RuntimeControl::stopRequested,&app,&QCoreApplication::quit,Qt::QueuedConnection);
        if(!control.start()){fprintf(stderr,"%s\n",qPrintable(control.error()));return 9;}
        // R5 (explicit --edit-mode): the panel's own "Enter Edit Mode" action, once shown.
        QTimer editMode;int editAttempts=0;
        if(qEnvironmentVariable("BWM_R5_EDIT_MODE")=="1"){
            editMode.setInterval(200);
            QObject::connect(&editMode,&QTimer::timeout,&app,[&]{
                auto *view=runtime.view(containment->id());
                if(view && view->isVisible() && view->isExposed()){
                    editMode.stop();if(auto *configure=containment->internalAction("configure"))configure->trigger();
                } else if(++editAttempts>50){editMode.stop();fprintf(stderr,"Edit mode: the panel view did not appear.\n");}
            });
            editMode.start();
        }
        const int code=app.exec();runtime.setSkin("default");
        corona.saveLayout(layoutName);return corona.config()->sync() ? code : 7;
    }
    std::unique_ptr<QQuickWindow> ownedWindow;
    if(panelPreview)ownedWindow=std::make_unique<PanelViewHost>(&corona);
    else ownedWindow=std::make_unique<QQuickWindow>();
    auto &window=*ownedWindow;
    window.resize(420,240);
    // Previews pick an output by its description (as Hyprland desc:), never by connector name.
    if(const QString wanted=qEnvironmentVariable("BWM_R4_OUTPUT").simplified();!wanted.isEmpty()) {
        QString reason;QScreen *match=BwmOutput::resolveScreen(wanted,&reason);
        if(!match){fprintf(stderr,"BWM_R4_OUTPUT: %s\n",qPrintable(reason));return 8;}
        window.setScreen(match);
    }
    corona.bind(containment,&window);
    if(args[1]=="--layer-preview" || args[1]=="--layer-panel-preview") {
        BwmSurface::configurePanel(&window,Qt::BottomEdge);
        if(!panelPreview)QObject::connect(containment,&Plasma::Containment::statusChanged,&window,[&window](Plasma::Types::ItemStatus status){
            BwmSurface::setPanelAcceptsInput(&window,status==Plasma::Types::AcceptingInputStatus);
        });
    }
    if(panelPreview) {
        auto *view=static_cast<PanelViewHost*>(&window);
        if(!view->load(containment)){fprintf(stderr,"%s\n",qPrintable(view->error()));return 4;}
        window.setTitle("BWM R4 — original panel, two isolated instances");window.show();
        if(panelFrameProbe)QTimer::singleShot(500,&app,[&]{
            const auto *frame=view->rootObject();
            const auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(containment);
            const bool attached=frame && frame->property("containment").value<QQuickItem*>()==item;
            QJsonObject result=QJsonObject::fromVariantMap(view->capabilities());
            result["containmentPackage"]=containment->pluginMetaData().pluginId();
            result["nativeContainmentAttached"]=attached;result["width"]=view->width();result["height"]=view->height();
            result["lengthMode"]=view->lengthMode();result["screenWidth"]=view->screen() ? view->screen()->size().width() : 0;
            result["frameReadbackAvailable"]=!view->grabWindow().isNull();
            result["error"]=view->error();puts(QJsonDocument(result).toJson().constData());app.exit(attached ? 0 : 4);
        });
        const int status=app.exec();corona.saveLayout(layoutName);corona.config()->sync();return status;
    }
    auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(a);
    if(item) { item->setParentItem(window.contentItem()); item->setSize(QSizeF(48,48)); item->setProperty("preloadFullRepresentation",true); }
    if(args[1]=="--preview" || args[1]=="--layer-preview") {
        if(!item)return 4;
        item->setPreferredRepresentation(item->compactRepresentation());
        Catalog catalog;
        ConfigurationSession config(a);
        QQmlEngine engine;
        QQmlComponent component(&engine,shell.fileUrl("views",QStringLiteral("Preview.qml")));
        QObject *object=component.createWithInitialProperties({{"appletItem",QVariant::fromValue(item)},{"applet",QVariant::fromValue(a)},{"configurationSession",QVariant::fromValue(&config)},{"catalog",QVariant::fromValue(&catalog)}});
        auto *root=qobject_cast<QQuickItem*>(object);
        if(!root){delete object;fprintf(stderr,"%s\n",qPrintable(component.errorString()));return 6;}
        root->setParentItem(window.contentItem());root->setSize(QSizeF(640,160));
        window.resize(640,160);window.setTitle("BWM R4 — isolated preview");window.show();
        const int status=app.exec();
        delete root;return status;
    }
    QTimer::singleShot(1000,&app,[&]{
        QJsonObject result{{"package",args[2]},{"firstId",int(a->id())},{"secondId",int(b->id())},{"itemLoaded",bool(item)},{"error",a->launchErrorMessage()},{"mainScript",package.fileUrl("mainscript").toString()},{"configModel",package.fileUrl("configmodel").toString()},{"translationDomain",a->translationDomain()}};
        if(item) { result["compact"]=bool(item->property("compactRepresentationItem").value<QQuickItem*>());result["full"]=bool(item->property("fullRepresentationItem").value<QQuickItem*>()); }
        ConfigurationSession config(a);
        // Probe the same native page factory and transaction used by the actual dialog.
        auto *model=config.view()->configModel();
        result["configurationError"]=config.error();
        QJsonArray categories;
        if(model) for(int i=0;i<model->rowCount();++i) categories.append(QJsonValue::fromVariant(model->get(i)));
        result["categories"]=categories;
        QJsonArray keys;
        if(a->configScheme()) for(auto *entry:a->configScheme()->items()) keys.append(entry->name());
        result["configurationKeys"]=keys;
        QJsonObject values;
        if(a->configScheme()) for(auto *entry:a->configScheme()->items()) values[entry->name()]=QJsonValue::fromVariant(entry->property());
        result["valuesBeforeExercise"]=values;
        QJsonArray actions;
        for(auto *action:a->contextualActions()) actions.append(action->text());
        result["actions"]=actions;
        result["formFactor"]=int(a->formFactor());
        result["location"]=int(a->location());
        result["width"]=item ? item->width() : 0;
        result["height"]=item ? item->height() : 0;
        QJsonArray pages;
        bool exercised=false;
        for(const auto &entry:config.pages()) {
            const auto category=entry.toMap();
            auto *page=category.value("item").value<QQuickItem*>();
            QJsonObject pageResult{{"source",category.value("source").toString()},{"loader",category.value("loader").toString()},
                {"module",category.value("configUiModule").toString()},{"component",category.value("configUiComponent").toString()},
                {"loaded",bool(page)},{"error",config.error()}};
            if(page && config.error().isEmpty() && args[1]=="--exercise" && a->configScheme()) {
                for(int j=0;j<page->metaObject()->propertyCount() && !exercised;++j) {
                    auto prop=page->metaObject()->property(j);
                    const QString name=QString::fromLatin1(prop.name());
                    if(!name.startsWith("cfg_")) continue;
                    const QString key=name.mid(4);
                    auto *entry=a->configScheme()->KCoreConfigSkeleton::findItem(key);
                    if(!entry || entry->property().metaType().id()!=QMetaType::Bool || !prop.isWritable()) continue;
                    const QVariant original=entry->property();
                    const QVariant other=b->configScheme()->KCoreConfigSkeleton::findItem(key)->property();
                    prop.write(page,original);
                    prop.write(page,!original.toBool());
                    const bool cancelIsolated=(entry->property()==original);
                    prop.write(page,original); // Cancel/revert staged page state.
                    a->configScheme()->useDefaults(true);
                    const QVariant defaultValue=entry->property();
                    a->configScheme()->useDefaults(false);
                    prop.write(page,defaultValue); // Defaults changes the page only.
                    const bool defaultsStaged=(entry->property()==original);
                    prop.write(page,!original.toBool());
                    const bool saved=config.apply();
                    a->configScheme()->load();
                    const bool independent=(b->configScheme()->KCoreConfigSkeleton::findItem(key)->property()==other);
                    ConfigurationSession again(a);
                    bool pageReopened=false;
                    if(again.error().isEmpty())for(const auto &candidate:again.pages()) {
                        const auto reopenedCategory=candidate.toMap();
                        auto *reopened=reopenedCategory.value("item").value<QQuickItem*>();
                        if(reopened && reopenedCategory.value("name")==category.value("name") &&
                            reopened->metaObject()->indexOfProperty(prop.name())>=0)
                            pageReopened=(reopened->property(prop.name())==entry->property());
                    }
                    result["exercise"]=QJsonObject{{"key",key},{"cancelDoesNotWrite",cancelIsolated},{"defaultsStaged",defaultsStaged},{"saved",saved},{"reloadedValue",QJsonValue::fromVariant(entry->property())},{"expectedValue",!original.toBool()},{"secondInstanceUnchanged",independent},{"pageReopened",pageReopened}};
                    exercised=saved && cancelIsolated && defaultsStaged && independent && pageReopened && entry->property().toBool()!=original.toBool();
                }
            }
            pages.append(pageResult);
        }
        result["pages"]=pages;
        result["configurationError"]=config.error();
        result["exercisePassed"]=exercised;
        corona.saveLayout("bwm-plasma-host-appletsrc");
        puts(QJsonDocument(result).toJson().constData());
        app.exit(item && (args[1]!="--exercise" || exercised) ? 0 : 4);
    });
    return app.exec();
}
