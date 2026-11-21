// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: GPL-2.0-or-later
// Native KWindowShadow client used only by the disposable R6 compositor driver.
#include <QApplication>
#include <QQuickWindow>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QQuickItem>
#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QCryptographicHash>
#include <QTimer>
#include <KWindowShadow>
#include <KWindowEffects>
#include <Plasma/Theme>
#include <PlasmaQuick/Dialog>
#include <KSvg/Svg>
#include <KSvg/ImageSet>
#include <LayerShellQt/Window>
#include <wayland-client.h>
#include <sys/socket.h>
#include <unistd.h>
#include <memory>
#include <array>
#include "surfaces.h"
#include "r6-alpha-client.h"
#include <qpa/qplatformnativeinterface.h>
#include <QGuiApplication>
#include <limits>
#include <cstring>

static void require(bool ok,const char *why){if(!ok)qFatal("%s",why);}
int main(int argc,char **argv){
    const auto root=QFileInfo(qEnvironmentVariable("BWM_R6_TEST_ROOT")).canonicalFilePath();
    require(root.startsWith(QDir::tempPath()+"/bwm-r6-surface-"),"Not a disposable R6 root");
    for(const auto *key:{"XDG_CONFIG_HOME","XDG_CACHE_HOME","XDG_DATA_HOME"})require(QFileInfo(qEnvironmentVariable(key)).canonicalFilePath().startsWith(root+"/"),key);
    require(qEnvironmentVariable("DBUS_SESSION_BUS_ADDRESS").startsWith("unix:path="+root+"/"),"Not a private bus");
    require(qEnvironmentVariable("WAYLAND_DISPLAY")==qEnvironmentVariable("BWM_R6_WAYLAND_DISPLAY"),"Wrong test display");
    auto *peer=wl_display_connect(qPrintable(qEnvironmentVariable("WAYLAND_DISPLAY")));require(peer,"Cannot connect test peer");
    ucred credentials{};socklen_t length=sizeof(credentials);
    require(getsockopt(wl_display_get_fd(peer),SOL_SOCKET,SO_PEERCRED,&credentials,&length)==0 && credentials.uid==getuid() &&
        credentials.pid==qEnvironmentVariableIntValue("BWM_R6_COMPOSITOR_PID"),"The display is not the fresh compositor");wl_display_disconnect(peer);
    QApplication app(argc,argv);app.setQuitOnLastWindowClosed(false);
    auto *display=qGuiApp->nativeInterface<QNativeInterface::QWaylandApplication>()->display();
    wp_alpha_modifier_v1 *alphaManager=nullptr;wp_alpha_modifier_surface_v1 *alphaSurface=nullptr;double opacity=1;
    auto *registry=wl_display_get_registry(display);
    const wl_registry_listener globals{[](void *data,wl_registry *registry,uint32_t name,const char *interface,uint32_t){
        if(!std::strcmp(interface,wp_alpha_modifier_v1_interface.name))*static_cast<wp_alpha_modifier_v1**>(data)=static_cast<wp_alpha_modifier_v1*>(wl_registry_bind(registry,name,&wp_alpha_modifier_v1_interface,1));
    },[](void*,wl_registry*,uint32_t){}};
    wl_registry_add_listener(registry,&globals,&alphaManager);require(wl_display_roundtrip(display)>=0,"Cannot read private globals");
    Plasma::Theme theme;
    QQmlEngine engine;QQmlComponent component(&engine);component.setData("import QtQuick\nRectangle { color: \"#707070\" }",QUrl());
    QQuickWindow backdrop;backdrop.setColor(QColor("#808080"));backdrop.resize(1280,800);
    const bool effects=qEnvironmentVariableIsSet("BWM_R6_EFFECTS");
    std::unique_ptr<QObject> pattern;
    if(effects) {
        QQmlComponent checker(&engine);checker.setData("import QtQuick\nItem { width: 1280; height: 800; Repeater { model: 640; Rectangle { required property int index; x: (index % 32)*40; y: Math.floor(index / 32)*40; width: 40; height: 40; color: (index % 32 + Math.floor(index / 32)) % 2 ? '#404040' : '#c0c0c0' } } }",QUrl());
        pattern.reset(checker.create());auto *p=qobject_cast<QQuickItem*>(pattern.get());require(p,"Checkerboard fixture did not load");p->setParentItem(backdrop.contentItem());
    }
    auto *background=LayerShellQt::Window::get(&backdrop);
    background->setLayer(LayerShellQt::Window::LayerBackground);
    background->setAnchors(LayerShellQt::Window::Anchors::fromInt(LayerShellQt::Window::AnchorTop|LayerShellQt::Window::AnchorBottom|LayerShellQt::Window::AnchorLeft|LayerShellQt::Window::AnchorRight));
    background->setExclusiveZone(-1);background->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);background->setScope("bwm-r6-background");backdrop.show();
    const bool dialogMode=qEnvironmentVariable("BWM_R6_CLIENT_KIND")=="dialog";
    std::unique_ptr<QQuickWindow> holder;
    if(dialogMode)holder=std::make_unique<PlasmaQuick::Dialog>();else holder=std::make_unique<QQuickWindow>();
    auto &window=*holder;window.setColor(Qt::transparent);window.resize(180,120);
    auto *layer=LayerShellQt::Window::get(&window);layer->setLayer(LayerShellQt::Window::LayerTop);
    layer->setAnchors(LayerShellQt::Window::Anchors::fromInt(LayerShellQt::Window::AnchorTop|LayerShellQt::Window::AnchorLeft));
    layer->setMargins(QMargins(320,220,0,0));layer->setExclusiveZone(-1);layer->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);layer->setScope("bwm-r6-shadow-client");
    std::unique_ptr<QObject> object(component.create());auto *item=qobject_cast<QQuickItem*>(object.get());require(item,"Fixture QML did not load");
    item->setSize(window.size());item->setImplicitWidth(180);item->setImplicitHeight(120);
    if(dialogMode) {
        BwmSurface::ensureNativeEffectsCommit(&window);
        auto *dialog=static_cast<PlasmaQuick::Dialog*>(&window);
        dialog->setLocation(Plasma::Types::Floating);dialog->setHideOnWindowDeactivate(false);dialog->setMainItem(item);
    } else item->setParentItem(window.contentItem());
    if(effects)item->setProperty("color",QColor("#80707070"));
    if(!dialogMode) {
        QObject::connect(&window,&QWindow::widthChanged,&window,[&]{item->setWidth(window.width());});QObject::connect(&window,&QWindow::heightChanged,&window,[&]{item->setHeight(window.height());});
    }
    KSvg::Svg svg;svg.setImagePath("dialogs/background");
    std::array<KWindowShadowTile::Ptr,8> tiles;
    const QStringList names{"top","topright","right","bottomright","bottom","bottomleft","left","topleft"};
    const auto reloadTiles=[&]{for(int i=0;i<8;++i){tiles[i]=KWindowShadowTile::Ptr::create();tiles[i]->setImage(svg.pixmap("shadow-"+names[i]).toImage());}};
    reloadTiles();
    KWindowShadow shadow;shadow.setWindow(&window);int borders=15;bool wantsShadow=true;
    const auto applyShadow=[&]{
        if(dialogMode)return true; // libplasma's original DialogShadows owns all requests.
        shadow.destroy();
        shadow.setTopTile(borders&1?tiles[0]:nullptr);shadow.setTopRightTile((borders&3)==3?tiles[1]:nullptr);
        shadow.setRightTile(borders&2?tiles[2]:nullptr);shadow.setBottomRightTile((borders&6)==6?tiles[3]:nullptr);
        shadow.setBottomTile(borders&4?tiles[4]:nullptr);shadow.setBottomLeftTile((borders&12)==12?tiles[5]:nullptr);
        shadow.setLeftTile(borders&8?tiles[6]:nullptr);shadow.setTopLeftTile((borders&9)==9?tiles[7]:nullptr);
        const auto margin=[&](QString edge,int fallback,bool width){const auto size=svg.elementSize("shadow-hint-"+edge+"-margin").toSize();return size.isValid()?(width?size.width():size.height()):fallback;};
        const QMargins padding(borders&8?margin("left",tiles[6]->image().width(),true):0,borders&1?margin("top",tiles[0]->image().height(),false):0,
            borders&2?margin("right",tiles[2]->image().width(),true):0,borders&4?margin("bottom",tiles[4]->image().height(),false):0);
        shadow.setPadding(padding);return !wantsShadow || shadow.create();
    };
    window.show();
    int sequence=-1;QTimer timer;timer.setInterval(50);
    QObject::connect(&timer,&QTimer::timeout,&app,[&]{
        if(!window.isExposed() && sequence<0)return;
        QFile command(root+"/command.json");if(!command.open(QIODevice::ReadOnly))return;
        const auto doc=QJsonDocument::fromJson(command.readAll()).object();const int next=doc["sequence"].toInt(-1);if(next<=sequence)return;
        if(doc["quit"].toBool()){app.quit();return;}
        sequence=next;
        if(doc.contains("size")){auto size=doc["size"].toArray();
            if(dialogMode){item->setImplicitWidth(size[0].toInt());item->setImplicitHeight(size[1].toInt());item->setSize({double(size[0].toInt()),double(size[1].toInt())});}
            else window.resize(size[0].toInt(),size[1].toInt());}
        if(doc.contains("borders"))borders=doc["borders"].toInt()&15;
        if(doc.contains("prefix")){svg.setImagePath(doc["prefix"].toString());reloadTiles();}
        if(doc.contains("shadow"))wantsShadow=doc["shadow"].toBool();
        if(doc.contains("opacity")) {
            require(alphaManager,"Native alpha-modifier protocol unavailable");
            auto *surface=static_cast<wl_surface*>(QGuiApplication::platformNativeInterface()->nativeResourceForWindow("surface",&window));require(surface,"No fixture surface for alpha modifier");
            if(!alphaSurface)alphaSurface=wp_alpha_modifier_v1_get_surface(alphaManager,surface);
            opacity=qBound(0.0,doc["opacity"].toDouble(),1.0);
            wp_alpha_modifier_surface_v1_set_multiplier(alphaSurface,uint32_t(std::numeric_limits<uint32_t>::max()*opacity));
        }
        if(doc["recreate"].toBool()){shadow.destroy();window.hide();window.destroy();window.show();}
        if(doc.contains("visible"))window.setVisible(doc["visible"].toBool());
        if(doc.contains("blur"))KWindowEffects::enableBlurBehind(&window,doc["blur"].toBool(),QRegion(0,0,window.width()/2,window.height()));
        const bool created=applyShadow();window.update();
        QTimer::singleShot(250,&app,[&,created,next]{
            QJsonArray sizes;for(const auto &tile:tiles)sizes.append(QJsonArray{tile->image().width(),tile->image().height()});
            const auto p=shadow.padding();
            const auto source=svg.imageSet()->imagePath(svg.imagePath());QFile svgFile(source);
            const auto hash=svgFile.open(QIODevice::ReadOnly)?QCryptographicHash::hash(svgFile.readAll(),QCryptographicHash::Sha256).toHex():QByteArray();
            QFile output(root+"/state.json");require(output.open(QIODevice::WriteOnly|QIODevice::Truncate),"Cannot write fixture state");
            output.write(QJsonDocument(QJsonObject{{"sequence",next},{"created",created},{"shadow",shadow.isCreated()},{"borders",borders},{"theme",theme.themeName()},
                {"svgImageSet",svg.imageSet()->imageSetName()},{"svgSource",QDir(root).relativeFilePath(source)},{"svgSha256",QString::fromLatin1(hash)},
                {"size",QJsonArray{window.width(),window.height()}},{"dpr",window.devicePixelRatio()},{"tiles",sizes},
                {"padding",QJsonArray{p.left(),p.top(),p.right(),p.bottom()}},{"position",QJsonArray{window.x(),window.y()}},
                {"blurAvailable",KWindowEffects::isEffectAvailable(KWindowEffects::BlurBehind)},
                {"nativeOpacity",opacity},{"alphaModifierAvailable",bool(alphaManager)},
                {"contrastAvailable",KWindowEffects::isEffectAvailable(KWindowEffects::BackgroundContrast)}}).toJson());
        });
    });timer.start();QTimer::singleShot(90000,&app,&QCoreApplication::quit);
    const int result=app.exec();
    if(alphaSurface)wp_alpha_modifier_surface_v1_destroy(alphaSurface);
    if(alphaManager)wp_alpha_modifier_v1_destroy(alphaManager);wl_registry_destroy(registry);
    return result;
}
