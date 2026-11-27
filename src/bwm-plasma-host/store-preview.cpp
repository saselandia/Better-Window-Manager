// SPDX-License-Identifier: GPL-2.0-or-later
// T7 visual fixture: original resources rendered by KDE, only in a disposable compositor.
#include "viewcorona.h"
#include "panelruntime.h"
#include "lookandfeellayout.h"
#include "sessionui.h"
#include "outputidentity.h"
#include "panelviewhost.h"
#include "surfaces.h"
#include "panelviewsettings.h"
#include <QApplication>
#include <QLabel>
#include <QVBoxLayout>
#include <QPushButton>
#include <QLineEdit>
#include <QSlider>
#include <QTimer>
#include <QFile>
#include <QDir>
#include <QJsonDocument>
#include <QJsonArray>
#include <QScreen>
#include <QQuickView>
#include <QQuickItem>
#include <KConfigGroup>
#include <KSharedConfig>
#include <KColorScheme>
#include <KIconTheme>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <KSvg/FrameSvg>
#include <KSvg/ImageSet>
#include <Plasma/Theme>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <memory>

int main(int argc,char **argv) {
    QApplication app(argc,argv);
    if(qEnvironmentVariable("BWM_FOCUS_NESTED")!="1")return 2;
    for(const auto *name:{"XDG_CONFIG_HOME","XDG_DATA_HOME","XDG_CACHE_HOME","XDG_STATE_HOME"})
        if(!QFileInfo(qEnvironmentVariable(name)).canonicalFilePath().startsWith(QDir::tempPath()+"/"))return 2;
    const auto args=app.arguments();if(args.size()!=4)return 2;
    const auto mode=args[1],id=args[2],report=args[3];
    QJsonObject result{{"mode",mode},{"id",id}};
    QWidget window;window.setWindowTitle("BWM Store compatibility fixture");window.resize(800,500);
    auto *layout=new QVBoxLayout(&window);layout->addWidget(new QLabel(mode+": "+id));
    const auto image=[&](const QPixmap &pixmap){auto *label=new QLabel;label->setPixmap(pixmap);layout->addWidget(label);return !pixmap.isNull();};
    std::unique_ptr<ViewCorona> corona;
    std::unique_ptr<PanelRuntime> runtime;
    std::vector<std::unique_ptr<PanelViewHost>> panels;
    std::unique_ptr<SessionUi> logout;
    std::unique_ptr<QQuickView> splash;
    Plasma::Applet *applet=nullptr;
    if(mode=="colors") {
        auto config=KSharedConfig::openConfig(id,KConfig::SimpleConfig);
        auto palette=KColorScheme::createApplicationPalette(config);app.setPalette(palette);
        result["background"]=palette.color(QPalette::Window).name();
        result["foreground"]=palette.color(QPalette::WindowText).name();
        result["loaded"]=QFile::exists(id)&&palette.color(QPalette::Window)!=palette.color(QPalette::WindowText);
        layout->addWidget(new QLineEdit("Texto y selección del esquema original"));
        layout->addWidget(new QPushButton("Botón de Breeze"));
        auto *slider=new QSlider(Qt::Horizontal);slider->setValue(60);layout->addWidget(slider);window.show();
    } else if(mode=="icons") {
        KIconTheme theme(id);QJsonArray paths;bool loaded=theme.isValid();
        for(const auto &name:{"folder","user-home","text-x-generic","application-x-executable"}) {
            const auto path=theme.iconPathByName(name,48,KIconLoader::MatchBest);
            paths.append(path);loaded=image(QPixmap(path))&&loaded;
        }
        result["paths"]=paths;result["loaded"]=loaded;window.show();
    } else if(mode=="cursor") {
        result["loaded"]=image(QPixmap(id));window.setCursor(QCursor(QPixmap(id),0,0));window.show();
    } else if(mode=="desktoptheme") {
        Plasma::Theme theme(id);KSvg::ImageSet set(id,"plasma/desktoptheme");QJsonArray paths;bool loaded=true;
        for(const auto &name:{"widgets/panel-background","dialogs/background","widgets/tooltip"}) {
            KSvg::FrameSvg svg;svg.setImageSet(&set);svg.setImagePath(name);svg.resizeFrame(QSize(600,100));
            const auto path=set.imagePath(name);paths.append(path);loaded=image(svg.framePixmap())&&loaded&&!path.isEmpty();
        }
        result["paths"]=paths;result["themeName"]=theme.themeName();result["loaded"]=loaded;window.show();
    } else if(mode=="decoration") {
        result["loaded"]=image(QPixmap(id));window.show();
    } else if(mode=="widget") {
        BwmSurface::registerTypes();
        corona=std::make_unique<ViewCorona>();
        corona->setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
        corona->loadLayout("store-preview-appletsrc");
        auto *containment=corona->createContainment("null");applet=containment->createApplet(id);
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet);
        splash=std::make_unique<QQuickView>();splash->resize(1000,650);
        if(item){item->setParentItem(splash->contentItem());item->setSize(QSizeF(1000,650));
            item->setPreferredRepresentation(item->fullRepresentation());item->setProperty("preloadFullRepresentation",true);}
        result["loaded"]=item&&!applet->failedToLaunch();splash->show();
    } else if(mode=="layout") {
        BwmSurface::registerTypes();PanelViewHost::registerTypes();
        const auto legacy=qEnvironmentVariable("XDG_CONFIG_HOME")+"/bwm-plasma-host";QDir().mkpath(legacy);
        try {
            const auto generation=LookAndFeelLayout::prepare(id,legacy,QStringLiteral(BWM_SHELL_SOURCE_DIR));
            corona=std::make_unique<ViewCorona>();
            corona->setKPackage(KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",QStringLiteral(BWM_SHELL_SOURCE_DIR)));
            corona->loadLayout(generation+"/appletsrc");
            // Virtual outputs have no EDID: production PanelRuntime correctly
            // refuses a persistent binding. Preview the prepared containments
            // directly on the only disposable QScreen; never weaken that guard.
            bool loaded=true;
            for(auto *c:corona->containments())if(c->containmentType()==Plasma::Containment::Panel){
                auto panel=std::make_unique<PanelViewHost>(corona.get(),generation+"/plasmashellrc");
                BwmSurface::configurePanel(panel.get(),c->location()==Plasma::Types::TopEdge?Qt::TopEdge:Qt::BottomEdge,0,true);
                panel->setScreenToFollow(app.primaryScreen());corona->bind(c,panel.get());
                loaded=panel->load(c)&&loaded;panel->show();panels.push_back(std::move(panel));
            }
            result["panelCount"]=int(panels.size());result["loaded"]=loaded&&!panels.empty();
            result["persistentOutputBindingTested"]=false;
        }catch(const std::exception &e){result["loaded"]=false;result["error"]=QString::fromUtf8(e.what());window.show();}
    } else if(mode=="splash") {
        const auto package=KPackage::PackageLoader::self()->loadPackage("Plasma/LookAndFeel",id);
        const auto path=package.filePath("splashmainscript");
        splash=std::make_unique<QQuickView>();splash->setResizeMode(QQuickView::SizeRootObjectToView);splash->resize(1000,650);
        splash->setSource(QUrl::fromLocalFile(path));splash->show();
        if(splash->rootObject())splash->rootObject()->setProperty("stage",1);
        result["source"]=path;result["loaded"]=splash->status()==QQuickView::Ready;
    } else if(mode=="logout") {
        auto config=KSharedConfig::openConfig("kdeglobals");config->group("KDE").writeEntry("LookAndFeelPackage",id);config->sync();
        logout=std::make_unique<SessionUi>("/bin/false");result["loaded"]=logout->prompt("all");result["source"]=SessionUi::logoutSource(id);
    } else return 2;
    QTimer::singleShot(1600,&app,[&]{
        if(runtime){result["panels"]=QJsonArray::fromVariantList(runtime->panels());result["readiness"]=QJsonObject::fromVariantMap(runtime->readiness());}
        if(!panels.empty()){QJsonArray status;for(const auto &panel:panels){auto state=QJsonObject::fromVariantMap(panel->capabilities());state["error"]=panel->error();status.append(state);}result["panels"]=status;}
        if(logout)result["status"]=logout->status();
        if(applet){result["error"]=applet->launchErrorMessage();auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(applet);
            result["full"]=item&&item->property("fullRepresentationItem").value<QQuickItem*>();}
        QFile file(report);if(file.open(QIODevice::WriteOnly))file.write(QJsonDocument(result).toJson());
    });
    QTimer::singleShot(7000,&app,&QCoreApplication::quit);
    return app.exec();
}
