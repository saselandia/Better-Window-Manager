// SPDX-License-Identifier: GPL-2.0-or-later
#include "migration.h"
#include <Plasma/Corona>
#include <Plasma/Containment>
#include <Plasma/Applet>
#include <Plasma/PluginLoader>
#include <KPluginMetaData>
#include <KConfigLoader>
#include <KSharedConfig>
#include <KConfig>
#include <KConfigGroup>
#include <QTemporaryDir>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QSet>
#include <QSaveFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QCryptographicHash>
#include <stdexcept>
#include <algorithm>
#include <cmath>
namespace {
class MigrationCorona:public Plasma::Corona {public:QRect screenGeometry(int)const override{return QRect(0,0,1024,768);}};
QByteArray read(const QString &path){QFile f(path);if(!f.open(QIODevice::ReadOnly))throw std::runtime_error("Cannot read staged migration input");return f.readAll();}
QJsonObject json(const QString &path){QJsonParseError e;const auto d=QJsonDocument::fromJson(read(path),&e);if(e.error!=QJsonParseError::NoError||!d.isObject())throw std::runtime_error("Invalid migration JSON");return d.object();}
void write(const QString &path,const QByteArray &data){QSaveFile f(path);if(!f.open(QIODevice::WriteOnly)||f.write(data)!=data.size()||!f.commit())throw std::runtime_error("Cannot save migration staging file");}
QString sha(const QByteArray &data){return QString::fromLatin1(QCryptographicHash::hash(data,QCryptographicHash::Sha256).toHex());}
void require(bool condition,const char *message){if(!condition)throw std::runtime_error(message);}
Plasma::Types::Location locationFor(const QString &edge) {
    if(edge=="top")return Plasma::Types::TopEdge;
    if(edge=="bottom")return Plasma::Types::BottomEdge;
    if(edge=="left")return Plasma::Types::LeftEdge;
    if(edge=="right")return Plasma::Types::RightEdge;
    throw std::runtime_error("Unrecognized panel edge");
}
Plasma::Types::FormFactor formFactorFor(Plasma::Types::Location location) {
    return location==Plasma::Types::LeftEdge || location==Plasma::Types::RightEdge ? Plasma::Types::Vertical : Plasma::Types::Horizontal;
}
QJsonObject archivedBar(const QByteArray &legacy) {
    QJsonParseError error;const auto source=QJsonDocument::fromJson(legacy,&error);
    require(error.error==QJsonParseError::NoError && source.isObject(),"Archived configuration must be a JSON object");
    const auto object=source.object();
    require(!object.contains("bar") || object.value("bar").isObject(),"Archived bar must be an object");
    const auto bar=object.value("bar").toObject();
    require(!bar.contains("plasma") || bar.value("plasma").isObject(),"Archived bar.plasma must be an object");
    return bar;
}
QString archivedEdge(const QByteArray &legacy) {
    const auto bar=archivedBar(legacy);const auto plasma=bar.value("plasma").toObject();
    require(!plasma.contains("edge") || plasma.value("edge").isString(),"Archived panel edge must be a string");
    const auto edge=plasma.value("edge").toString();
    if(!edge.isEmpty()){locationFor(edge);return edge;}
    require(!bar.contains("bottom") || bar.value("bottom").isBool(),"Archived bar.bottom must be boolean");
    return bar.value("bottom").toBool(false) ? "bottom" : "top";
}
QJsonObject archivedViewSettings(const QByteArray &legacy) {
    const auto plasma=archivedBar(legacy).value("plasma").toObject();
    const auto stored=plasma.value("thickness");const double thickness=stored.isUndefined() ? 44 : stored.toDouble(NAN);
    require(std::isfinite(thickness) && std::floor(thickness)==thickness,"Archived thickness must be a finite integer");
    const auto floating=plasma.value("floating");require(floating.isUndefined() || floating.isBool(),"Archived floating must be boolean");
    const auto styleValue=plasma.value("style");require(styleValue.isUndefined() || styleValue.isString(),"Archived opacity style must be a string");
    const auto style=styleValue.toString("translucent");
    require(QStringList{"adaptive","opaque","translucent","floating"}.contains(style),"Unrecognized archived opacity style");
    return {{"thickness",int(std::clamp(thickness==0 ? 44 : thickness,24.0,128.0))},
        {"floating",int(floating.toBool(false) || style=="floating")},
        {"panelOpacity",style=="opaque" ? 1 : style=="translucent" ? 2 : 0}};
}
QJsonArray deferredViewSettings(const QByteArray &legacy,const QJsonObject &view) {
    const auto plasma=archivedBar(legacy).value("plasma").toObject();QJsonArray deferred;
    const auto add=[&](const QString &key,const QJsonValue &fallback,const QString &reason) {
        deferred.append(QJsonObject{{"legacyKey",key},{"value",plasma.value(key).isUndefined()?fallback:plasma.value(key)},
            {"reason",reason},{"operationalVerified",false}});
    };
    add("visibility","always","Reservations/autohide/window avoidance require the panel controller; not mapped to a false preview policy.");
    add("alignment","center","Native positioning controller not connected.");
    add("length",1,"Legacy length is a screen-relative fraction; output geometry must be resolved before converting to native lengths.");
    add("floatingGap",8,"The native gap comes from the SVG theme, with no equivalent per-panel key.");
    if(view.value("floating").toInt())add("floating",false,"Native floating flag staged; docking in response to touching windows is not connected.");
    if(view.value("panelOpacity").toInt()==0)add("style","translucent","Native Adaptive enum preserved; frame host rejects it until the window backend is connected.");
    for(const auto &key:{"color","opacity","centerTasks","trayItems","taskOrder"})if(plasma.contains(key))
        add(key,QJsonValue(),"Archived without an established native destination/equivalence; not silently applied.");
    return deferred;
}
void writeViewSettings(KConfig &config,uint id,const QJsonObject &view) {
    auto base=KConfigGroup(&config,"PlasmaViews").group(QString("Panel %1").arg(id));
    base.writeEntry("floating",view.value("floating").toInt());base.writeEntry("panelOpacity",view.value("panelOpacity").toInt());
    base.group("Defaults").writeEntry("thickness",view.value("thickness").toInt());
}
void verifyViewSettings(KConfig &config,uint id,const QJsonObject &view) {
    const auto base=KConfigGroup(&config,"PlasmaViews").group(QString("Panel %1").arg(id));
    for(const auto &key:{"floating","panelOpacity","thickness"}) {
        const auto g=QString(key)=="thickness" ? base.group("Defaults") : base;
        require(g.hasKey(key) && g.readEntry(key,-1)==view.value(key).toInt(),"Native panel-view setting did not persist");
    }
}
}
namespace BwmMigration {
QJsonObject stage(const QString &proposalPath) {
    const auto plan=json(proposalPath);
    const QByteArray legacy=plan.value("legacyJson").toString().toUtf8();
    require(sha(legacy)==plan.value("sourceSha256").toString(),"Legacy archive hash mismatch");
    const QString edge=archivedEdge(legacy);
    const auto view=archivedViewSettings(legacy);const auto deferred=deferredViewSettings(legacy,view);
    const auto location=locationFor(edge);const auto formFactor=formFactorFor(location);
    require(plan.value("version").toInt()==1 && plan.value("panels").isArray(),"Unsupported migration proposal");
    const auto panels=plan.value("panels").toArray();require(!panels.isEmpty(),"No panels in proposal");
    QSet<QString> packages;
    for(const auto &m:Plasma::PluginLoader::self()->listAppletMetaData(QString()))packages.insert(m.pluginId());
    for(const auto &p:panels) {
        require(!p.toObject().contains("nativeViewSettings") || p.toObject().value("nativeViewSettings").toObject()==view,"Proposed view settings differ from archived configuration");
        require(!p.toObject().contains("edge") || p.toObject().value("edge").toString()==edge,"Proposed panel edge differs from archived configuration");
        require(!p.toObject().value("outputDescription").toString().isEmpty(),"Missing output identity");
        require(p.toObject().value("containmentPackage").toString()=="org.kde.panel" && packages.contains("org.kde.panel"),"The original panel containment is required");
        require(!p.toObject().value("widgets").toArray().isEmpty(),"Empty widget list");
        for(const auto &w:p.toObject().value("widgets").toArray())
            require(packages.contains(w.toObject().value("package").toString()),"A required widget is missing; no partial migration is published");
    }
    const QString destination=qEnvironmentVariable("XDG_CONFIG_HOME")+"/bwm-native-staged";
    require(!QFileInfo::exists(destination),"Staging destination exists; refusing to overwrite it");
    QTemporaryDir work(qEnvironmentVariable("XDG_CONFIG_HOME")+"/.bwm-migration-XXXXXX");require(work.isValid(),"Cannot create migration staging directory");
    QJsonArray nativePanels;
    {
    MigrationCorona corona;corona.loadLayout(work.path()+"/layout");
    // Native format in a separate staging artifact, never replace the user's
    // complete plasmashellrc. A later activation must merge the selected panel IDs.
    KConfig viewConfig(work.path()+"/plasmashellrc",KConfig::SimpleConfig);
    for(const auto &p:panels) {
        const auto panel=p.toObject();auto *c=corona.createContainment("org.kde.panel");require(c && !c->failedToLaunch(),"Cannot create original panel containment");
        c->setFormFactor(formFactor);c->setLocation(location);
        QJsonArray widgets;
        QStringList order;
        for(const auto &w:panel.value("widgets").toArray()) {
            auto widget=w.toObject();auto *a=c->createApplet(widget.value("package").toString());
            require(a && !a->failedToLaunch(),"Cannot create native applet");
            const auto settings=widget.value("nativeSettings").toObject();
            for(auto it=settings.begin();it!=settings.end();++it) {
                require(a->configScheme(),"Destination widget has no configuration schema");
                auto *entry=a->configScheme()->KCoreConfigSkeleton::findItem(it.key());require(entry,"Unmapped setting; refusing to silently ignore it");
                auto value=it.value().toVariant();require(value.convert(entry->property().metaType()),"Setting has incompatible type");
                require(!a->configScheme()->isImmutable(it.key()),"Destination setting is locked");entry->setProperty(value);
            }
            if(!settings.isEmpty())require(a->configScheme()->save(),"Cannot save applet settings");
            widget["appletId"]=int(a->id());widget["status"]="native-instance-staged";widgets.append(widget);
            order.append(QString::number(a->id()));
        }
        // The original panel's LayoutManager restores General/AppletOrder. Let its
        // KConfigLoader serialize the real schema rather than writing appletsrc text.
        require(c->configScheme(),"Original panel schema is missing");
        auto *orderEntry=c->configScheme()->KCoreConfigSkeleton::findItem("AppletOrder");
        require(orderEntry && !c->configScheme()->isImmutable("AppletOrder"),"Original panel order cannot be saved");
        orderEntry->setProperty(order.join(';'));require(c->configScheme()->save(),"Cannot save original panel order");
        writeViewSettings(viewConfig,c->id(),view);
        nativePanels.append(QJsonObject{{"outputDescription",panel.value("outputDescription")},{"containmentPackage",c->pluginMetaData().pluginId()},
            {"edge",edge},{"location",int(location)},{"formFactor",int(formFactor)},
            {"nativeViewSettings",view},{"deferredViewSettings",deferred},{"viewRuntimeVerified",false},
            {"containmentId",int(c->id())},{"appletOrder",order.join(';')},{"widgets",widgets}});
    }
    corona.saveLayout(work.path()+"/layout");
    require(corona.config()->sync(),"Cannot flush native layout to disk");
    if(!viewConfig.sync()){viewConfig.markAsClean();throw std::runtime_error("Cannot flush native panel-view staging file");}
    } // Release every native config owner before renaming its directory.
    require(QFileInfo::exists(work.path()+"/layout"),"Corona did not serialize the layout");
    write(work.path()+"/legacy.json",legacy);
    QJsonObject report{{"status","staged-native-layout"},{"sourceSha256",sha(legacy)},{"activationAllowed",false},{"orientationContractVersion",1},
        {"viewSettingsContractVersion",1},{"viewSettingsFile","plasmashellrc"},{"panels",nativePanels},
        {"limitations","Native thickness/floating/opacity values staged, not full behavior equivalence. Deferred view settings, runtime capabilities, activation and rollback still require adapters."}};
    write(work.path()+"/report.json",QJsonDocument(report).toJson());
    require(QDir().rename(work.path(),destination),"Cannot publish staged migration atomically");work.setAutoRemove(false);
    report["directory"]=destination;return report;
}
QJsonObject verify(const QString &directory) {
    require(QFileInfo(directory).canonicalFilePath().startsWith(QFileInfo(qEnvironmentVariable("XDG_CONFIG_HOME")).canonicalFilePath()+"/"),"Stage directory must be inside isolated configuration root");
    auto report=json(directory+"/report.json");const auto archived=read(directory+"/legacy.json");
    require(sha(archived)==report.value("sourceSha256").toString(),"Archived source was modified");
    const bool orientationContract=report.contains("orientationContractVersion");
    require(!orientationContract || report.value("orientationContractVersion").toInt(-1)==1,"Unsupported orientation report contract");
    if(orientationContract) {
        const auto edge=archivedEdge(archived);
        for(const auto &p:report.value("panels").toArray()) {
            const auto panel=p.toObject();
            require(panel.contains("edge") && panel.contains("location") && panel.contains("formFactor"),"Orientation report fields missing");
            require(panel.value("edge").toString()==edge,"Staged edge differs from archived configuration");
        }
    }
    const bool viewContract=report.contains("viewSettingsContractVersion");
    if(!viewContract) {
        require(!report.contains("viewSettingsFile") && !QFileInfo::exists(directory+"/plasmashellrc"),"Native view staging artifact has no report contract");
        for(const auto &p:report.value("panels").toArray())require(!p.toObject().contains("nativeViewSettings"),"Native view settings have no report contract");
    }
    if(viewContract) {
        require(report.value("viewSettingsContractVersion").toInt(-1)==1 && report.value("viewSettingsFile").toString()=="plasmashellrc","Unsupported native panel-view report contract");
        const auto expected=archivedViewSettings(archived);const auto deferred=deferredViewSettings(archived,expected);
        require(QFileInfo::exists(directory+"/plasmashellrc"),"Native panel-view staging file missing");
        KConfig viewConfig(directory+"/plasmashellrc",KConfig::SimpleConfig);
        for(const auto &p:report.value("panels").toArray()) {
            const auto panel=p.toObject();
            require(panel.contains("nativeViewSettings") && panel.value("nativeViewSettings").toObject()==expected,"View report differs from archived configuration");
            require(panel.contains("deferredViewSettings") && panel.value("deferredViewSettings").toArray()==deferred,"Deferred view capabilities differ from archived configuration");
            require(panel.value("viewRuntimeVerified").isBool() && !panel.value("viewRuntimeVerified").toBool(),"Staging cannot certify view runtime behavior");
            verifyViewSettings(viewConfig,uint(panel.value("containmentId").toInt()),expected);
        }
    }
    MigrationCorona corona;corona.loadLayout(directory+"/layout");
    for(const auto &p:report.value("panels").toArray()) {
        const auto panel=p.toObject();Plasma::Containment *containment=nullptr;
        for(auto *c:corona.containments())if(int(c->id())==panel.value("containmentId").toInt())containment=c;
        require(containment,"Missing native containment after reopening");
        require(containment->pluginMetaData().pluginId()=="org.kde.panel","Original panel identity did not persist");
        // Pre-orientation reports only staged bottom/horizontal panels. Keep their
        // readback contract instead of reinterpreting an existing layout on upgrade.
        const QString edge=panel.value("edge").toString("bottom");
        const auto location=locationFor(edge);const auto formFactor=formFactorFor(location);
        require(containment->formFactor()==formFactor && containment->location()==location,"Containment orientation did not persist");
        require(!panel.contains("location") || panel.value("location").toInt(-1)==int(location),"Inconsistent report location");
        require(!panel.contains("formFactor") || panel.value("formFactor").toInt(-1)==int(formFactor),"Inconsistent report form factor");
        require(containment->configScheme(),"Panel schema missing after reopening");
        auto *order=containment->configScheme()->KCoreConfigSkeleton::findItem("AppletOrder");
        require(order && order->property().toString()==panel.value("appletOrder").toString(),"Original panel order did not persist");
        for(const auto &w:panel.value("widgets").toArray()) {
            const auto widget=w.toObject();Plasma::Applet *applet=nullptr;
            for(auto *a:containment->applets())if(int(a->id())==widget.value("appletId").toInt())applet=a;
            require(applet && applet->pluginMetaData().pluginId()==widget.value("package").toString(),"Native applet identity changed");
            const auto settings=widget.value("nativeSettings").toObject();
            for(auto it=settings.begin();it!=settings.end();++it) {
                require(applet->configScheme(),"Schema missing after reopening");auto *entry=applet->configScheme()->KCoreConfigSkeleton::findItem(it.key());require(entry,"Key missing after reopening");
                auto value=it.value().toVariant();require(value.convert(entry->property().metaType()) && value==entry->property(),"Native setting did not persist");
            }
        }
    }
    report["status"]="verified-native-stage";return report;
}
}
