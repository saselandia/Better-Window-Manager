// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelprobe.h"
#include "migration.h"
#include "panelviewhost.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <PlasmaQuick/AppletQuickItem>
#include <KPackage/PackageLoader>
#include <KPackage/Package>
#include <QCoreApplication>
#include <QElapsedTimer>
#include <QEventLoop>
#include <QJsonArray>
#include <QQuickWindow>
#include <QQmlContext>
#include <KSharedConfig>
#include <memory>
#include <vector>
#include <stdexcept>

namespace {
class ProbeCorona : public Plasma::Corona {
public:
    QRect screenGeometry(int) const override {return QRect(0,0,1024,768);}
};
}

QJsonObject BwmMigration::probePanel(const QString &directory, const QString &shellPath,bool nativeFrame) {
    const auto verified=verify(directory);
    if(nativeFrame && !verified.contains("viewSettingsContractVersion"))throw std::runtime_error("Native frame readback requires a view-settings migration contract");
    ProbeCorona corona;
    auto shell=KPackage::PackageLoader::self()->loadPackage("Plasma/Shell",shellPath);
    if(!shell.isValid())throw std::runtime_error("Missing host shell package");
    corona.setKPackage(shell);
    corona.loadLayout(directory+"/layout");
    std::vector<std::unique_ptr<QQuickWindow>> windows;
    for(auto *c:corona.containments()) {
        const QSize size=c->formFactor()==Plasma::Types::Vertical ? QSize(48,640) : QSize(640,48);
        std::unique_ptr<QQuickWindow> window;
        if(nativeFrame) {
            auto frame=std::make_unique<PanelViewHost>(&corona,directory+"/plasmashellrc");
            if(!frame->load(c))throw std::runtime_error(frame->error().toStdString());
            window=std::move(frame);
        } else {window=std::make_unique<QQuickWindow>();window->resize(size);}
        auto *item=PlasmaQuick::AppletQuickItem::itemForApplet(c);
        if(!item || c->failedToLaunch())throw std::runtime_error("Original panel QML did not load");
        if(!nativeFrame){item->setParentItem(window->contentItem());item->setSize(size);}
        window->show();windows.push_back(std::move(window));
    }
    QElapsedTimer timer;timer.start();
    while(timer.elapsed()<500)QCoreApplication::processEvents(QEventLoop::AllEvents,20);
    QJsonArray panels;
    bool passed=true;
    for(const auto &p:verified.value("panels").toArray()) {
        const auto expected=p.toObject();Plasma::Containment *c=nullptr;
        for(auto *candidate:corona.containments())if(int(candidate->id())==expected.value("containmentId").toInt())c=candidate;
        if(!c)throw std::runtime_error("Panel disappeared during probe");
        auto *root=PlasmaQuick::AppletQuickItem::itemForApplet(c);
        QJsonArray widgets;
        const bool vertical=c->formFactor()==Plasma::Types::Vertical;
        qreal previousEnd=-1;
        for(const auto &w:expected.value("widgets").toArray()) {
            const auto expectedWidget=w.toObject();Plasma::Applet *a=nullptr;
            for(auto *candidate:c->applets())if(int(candidate->id())==expectedWidget.value("appletId").toInt())a=candidate;
            auto *item=a ? PlasmaQuick::AppletQuickItem::itemForApplet(a) : nullptr;
            const bool inOriginalContainer=item && item->parentItem() && item->parentItem()->property("isAppletContainer").toBool();
            const QPointF point=item ? item->mapToItem(root,QPointF()) : QPointF();
            const qreal start=vertical ? point.y() : point.x();
            const bool ordered=inOriginalContainer && item->width()>0 && item->height()>0 && start>=previousEnd-0.5;
            if(item)previousEnd=start+(vertical ? item->height() : item->width());
            passed=passed && ordered && !a->failedToLaunch();
            widgets.append(QJsonObject{{"id",expectedWidget.value("appletId")},{"package",expectedWidget.value("package")},
                {"nativeContainer",inOriginalContainer},{"ordered",ordered},{"x",point.x()},{"y",point.y()},
                {"width",item ? item->width() : 0},{"height",item ? item->height() : 0},
                {"error",a ? a->launchErrorMessage() : QStringLiteral("Missing applet")}});
        }
        QJsonObject result{{"containmentId",int(c->id())},{"qmlBaseUrl",qmlContext(root)->baseUrl().toString()},
            {"location",int(c->location())},{"formFactor",int(c->formFactor())},{"orderAxis",vertical ? "y" : "x"},
            {"rootType",QString::fromLatin1(root->metaObject()->className())},{"widgets",widgets}};
        if(nativeFrame) {
            auto *frame=qobject_cast<PanelViewHost*>(root->window());
            if(!frame || !frame->rootObject())throw std::runtime_error("Native frame disappeared during migration probe");
            const auto settings=expected.value("nativeViewSettings").toObject();
            if(frame->viewSettings().value("thickness").toInt()!=settings.value("thickness").toInt() ||
               frame->thickness()<settings.value("thickness").toInt() ||
               frame->floating()!=(settings.value("floating").toInt()!=0) || frame->opacityMode()!=settings.value("panelOpacity").toInt())
                throw std::runtime_error("Staged preferences did not reach the native frame");
            if(frame->grabWindow().isNull())throw std::runtime_error("Native migrated frame render readback unavailable");
            result["nativeFrameLoaded"]=true;result["nativeViewSettings"]=QJsonObject::fromVariantMap(frame->viewSettings());
            result["effectiveThickness"]=frame->thickness();result["floatingness"]=frame->rootObject()->property("floatingness").toDouble();
            result["isOpaque"]=frame->rootObject()->property("isOpaque").toBool();result["frameSource"]=frame->source().toString();
        }
        panels.append(result);
    }
    // Read the native order again: loading the original LayoutManager must not corrupt it.
    corona.saveLayout(directory+"/layout");corona.config()->sync();
    if(!passed)throw std::runtime_error("Original panel failed to place widgets in the staged order");
    return QJsonObject{{"status",nativeFrame ? "original-panel-frame-passed" : "original-panel-qml-passed"},{"waylandVerified",false},{"panels",panels}};
}
