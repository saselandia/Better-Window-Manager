/*
    SPDX-FileCopyrightText: 2009 Aaron Seigo <aseigo@kde.org>
    SPDX-FileCopyrightText: 2023 Harald Sitter <sitter@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted subset of plasma-workspace 6.7.5 shell/scripting (ScriptEngine::V1,
    Panel, Containment::addWidget) and ShellCorona::addPanel; see layouttemplate.h.
*/
#include "layouttemplate.h"
#include "viewcorona.h"

#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <Plasma/Applet>
#include <Plasma/Containment>
#include <Plasma/PluginLoader>
#include <QFile>
#include <QFontMetrics>
#include <QGuiApplication>
#include <QJSEngine>
#include <QLocale>
#include <QScreen>
#include <QDebug>
#include <KConfigGroup>
#include <KConfigLoader>
#include <QJSValueIterator>
#include <condition_variable>
#include <thread>

using namespace Qt::StringLiterals;

namespace {
QString locationName(Plasma::Types::Location location)
{
    switch (location) {
    case Plasma::Types::TopEdge: return u"top"_s;
    case Plasma::Types::BottomEdge: return u"bottom"_s;
    case Plasma::Types::LeftEdge: return u"left"_s;
    case Plasma::Types::RightEdge: return u"right"_s;
    case Plasma::Types::Desktop: return u"desktop"_s;
    case Plasma::Types::FullScreen: return u"fullscreen"_s;
    default: return u"floating"_s;
    }
}
// ScriptEngine::V1::gridUnit (plasma-workspace 6.7.5).
int gridUnit()
{
    int unit = QFontMetrics(QGuiApplication::font()).boundingRect(QStringLiteral("M")).height();
    if (unit % 2 != 0) {
        unit++;
    }
    return unit;
}
}

LayoutTemplatePanel::LayoutTemplatePanel(Plasma::Containment *containment, int screen, const QVariantMap &current, QObject *parent)
    : LayoutTemplateWidget(containment, parent), m_containment(containment), m_screen(screen), m_current(current)
{
}
int LayoutTemplatePanel::id() const { return m_containment ? int(m_containment->id()) : 0; }
QString LayoutTemplatePanel::type() const { return m_containment ? m_containment->pluginMetaData().pluginId() : QString(); }
QString LayoutTemplatePanel::formFactor() const
{
    if (!m_containment) return {};
    switch (m_containment->formFactor()) {
    case Plasma::Types::Horizontal: return u"horizontal"_s;
    case Plasma::Types::Vertical: return u"vertical"_s;
    case Plasma::Types::MediaCenter: return u"mediacenter"_s;
    case Plasma::Types::Application: return u"application"_s;
    default: return u"planar"_s;
    }
}
QString LayoutTemplatePanel::location() const { return m_containment ? locationName(m_containment->location()) : QString(); }
void LayoutTemplatePanel::setLocation(const QString &locationString)
{
    // Panel::setLocation (plasma-workspace 6.7.5 shell/scripting/panel.cpp).
    if (!m_containment) return;
    const QString lower = locationString.toLower();
    Plasma::Types::Location loc = Plasma::Types::Floating;
    Plasma::Types::FormFactor ff = Plasma::Types::Planar;
    if (lower == u"desktop") {
        loc = Plasma::Types::Desktop;
    } else if (lower == u"fullscreen") {
        loc = Plasma::Types::FullScreen;
    } else if (lower == u"top") {
        loc = Plasma::Types::TopEdge;
        ff = Plasma::Types::Horizontal;
    } else if (lower == u"bottom") {
        loc = Plasma::Types::BottomEdge;
        ff = Plasma::Types::Horizontal;
    } else if (lower == u"left") {
        loc = Plasma::Types::LeftEdge;
        ff = Plasma::Types::Vertical;
    } else if (lower == u"right") {
        loc = Plasma::Types::RightEdge;
        ff = Plasma::Types::Vertical;
    }
    m_containment->setLocation(loc);
    m_containment->setFormFactor(ff);
    m_containment->flushPendingConstraintsEvents();
}
int LayoutTemplatePanel::height() const { return m_pending.value(u"thickness"_s, m_current.value(u"thickness"_s, 0)).toInt(); }
void LayoutTemplatePanel::setHeight(int height) { m_pending.insert(u"thickness"_s, height); }
QString LayoutTemplatePanel::alignment() const
{
    const int a = m_pending.value(u"alignment"_s, m_current.value(u"alignment"_s, int(Qt::AlignCenter))).toInt();
    return a == Qt::AlignLeft ? u"left"_s : a == Qt::AlignRight ? u"right"_s : u"center"_s;
}
void LayoutTemplatePanel::setAlignment(const QString &alignment)
{
    int a = Qt::AlignCenter;
    if (alignment.compare(u"left", Qt::CaseInsensitive) == 0) {
        a = Qt::AlignLeft;
    } else if (alignment.compare(u"right", Qt::CaseInsensitive) == 0) {
        a = Qt::AlignRight;
    }
    m_pending.insert(u"alignment"_s, a);
}
int LayoutTemplatePanel::offset() const { return m_pending.value(u"offset"_s, m_current.value(u"offset"_s, 0)).toInt(); }
void LayoutTemplatePanel::setOffset(int offset) { m_pending.insert(u"offset"_s, offset); }
int LayoutTemplatePanel::minimumLength() const { return m_pending.value(u"minLength"_s, m_current.value(u"minLength"_s, 0)).toInt(); }
void LayoutTemplatePanel::setMinimumLength(int pixels) { m_pending.insert(u"minLength"_s, pixels); }
int LayoutTemplatePanel::maximumLength() const { return m_pending.value(u"maxLength"_s, m_current.value(u"maxLength"_s, 0)).toInt(); }
void LayoutTemplatePanel::setMaximumLength(int pixels) { m_pending.insert(u"maxLength"_s, pixels); }
QList<int> LayoutTemplatePanel::widgetIds() const
{
    QList<int> ids;
    if (m_containment)
        for (auto *applet : m_containment->applets())
            ids.append(int(applet->id()));
    return ids;
}
QVariant LayoutTemplatePanel::addWidget(const QString &plugin)
{
    // Containment::addWidget (scripting) without geometry: createApplet appends it in order.
    if (!m_containment || plugin.isEmpty()) return {};
    auto *applet = m_containment->createApplet(plugin);
    if (!applet) return {};
    QStringList order;
    for (auto *a : m_containment->applets()) order.append(QString::number(a->id()));
    m_containment->config().group(u"General"_s).writeEntry(u"AppletOrder"_s, order);
    return QVariant::fromValue<QObject *>(new LayoutTemplateWidget(applet, this));
}

LayoutTemplateRunner::LayoutTemplateRunner(ViewCorona *corona, QScreen *target, const QHash<Plasma::Containment *, QVariantMap> &existing, QObject *parent)
    : QObject(parent), m_corona(corona), m_target(target), m_existing(existing), m_engine(new QJSEngine(this))
{
}
LayoutTemplateRunner::~LayoutTemplateRunner() = default;

int LayoutTemplateRunner::screenIndex() const { return std::max(0, int(QGuiApplication::screens().indexOf(m_target.data()))); }

void LayoutTemplateRunner::print(const QString &message) const { qInfo().noquote() << message; }

QVariantMap LayoutTemplateRunner::screenGeometry(int screen) const
{
    const QRect r = m_corona ? m_corona->screenGeometry(screen) : QRect();
    return {{u"x"_s, r.x()}, {u"y"_s, r.y()}, {u"width"_s, r.width()}, {u"height"_s, r.height()}};
}

QList<int> LayoutTemplateRunner::panelIds() const
{
    QList<int> ids;
    for (auto it = m_existing.constBegin(); it != m_existing.constEnd(); ++it)
        if (it.key()) ids.append(int(it.key()->id()));
    for (auto *panel : m_created)
        if (panel->containment()) ids.append(panel->id());
    std::sort(ids.begin(), ids.end());
    return ids;
}

QJSValue LayoutTemplateRunner::panelById(int id)
{
    for (auto *panel : m_created)
        if (panel->id() == id) return m_engine->newQObject(panel);
    for (auto it = m_existing.constBegin(); it != m_existing.constEnd(); ++it) {
        if (it.key() && int(it.key()->id()) == id) {
            auto *wrapper = new LayoutTemplatePanel(it.key(), it.value().value(u"screen"_s, -1).toInt(), it.value(), this);
            QJSEngine::setObjectOwnership(wrapper, QJSEngine::CppOwnership);
            return m_engine->newQObject(wrapper);
        }
    }
    return QJSValue();
}

LayoutTemplatePanel *LayoutTemplateRunner::createPanel(const QString &plugin)
{
    // ScriptEngine::createContainment("Panel", plugin) + ShellCorona::addPanel(plugin).
    if (!m_corona || !m_target) {
        m_error = tr("A live output is required to add a panel.");
        return nullptr;
    }
    bool exists = false;
    for (const KPluginMetaData &info : Plasma::PluginLoader::listContainmentsMetaDataOfType(u"Panel"_s))
        exists = exists || info.pluginId() == plugin;
    if (!exists) {
        m_error = tr("The panel containment %1 is not installed.").arg(plugin);
        return nullptr;
    }
    auto *c = m_corona->createContainment(plugin);
    if (!c || c->failedToLaunch()) {
        m_error = tr("Cannot create the panel containment %1.").arg(plugin);
        delete c;
        return nullptr;
    }
    QList<Plasma::Types::Location> available{Plasma::Types::BottomEdge, Plasma::Types::TopEdge, Plasma::Types::LeftEdge, Plasma::Types::RightEdge};
    const int screen = screenIndex();
    for (auto it = m_existing.constBegin(); it != m_existing.constEnd(); ++it)
        if (it.key() && it.value().value(u"screen"_s, -1).toInt() == screen) available.removeAll(it.key()->location());
    for (auto *panel : std::as_const(m_created))
        if (panel->containment()) available.removeAll(panel->containment()->location());
    const auto loc = available.isEmpty() ? Plasma::Types::TopEdge : available.constFirst();
    c->setLocation(loc);
    c->setFormFactor(loc == Plasma::Types::LeftEdge || loc == Plasma::Types::RightEdge ? Plasma::Types::Vertical : Plasma::Types::Horizontal);
    c->updateConstraints(Plasma::Applet::AllConstraints | Plasma::Applet::StartupCompletedConstraint);
    c->flushPendingConstraintsEvents();
    auto *wrapper = new LayoutTemplatePanel(c, screen, {}, this);
    m_created.append(wrapper);
    return wrapper;
}

QJSValue LayoutTemplateRunner::newPanel(const QString &plugin)
{
    auto *panel = createPanel(plugin.isEmpty() ? u"org.kde.panel"_s : plugin);
    if (!panel) {
        return m_engine->newErrorObject(QJSValue::GenericError, m_error);
    }
    QJSEngine::setObjectOwnership(panel, QJSEngine::CppOwnership);
    return m_engine->newQObject(panel);
}

bool LayoutTemplateRunner::run(const QString &actionData)
{
    m_error.clear();
    if (actionData.isEmpty()) {
        m_error = tr("No panel template was chosen.");
        return false;
    }
    if (!actionData.startsWith(u"plasma-desktop-template:"_s)) {
        return createPanel(actionData) != nullptr;
    }
    const QString name = actionData.mid(int(qstrlen("plasma-desktop-template:")));
    KPackage::Package package = KPackage::PackageLoader::self()->loadPackage(u"Plasma/LayoutTemplate"_s);
    package.setPath(name);
    const QString scriptFile = package.filePath("mainscript");
    QFile file(scriptFile);
    if (!package.isValid() || scriptFile.isEmpty() || !file.open(QIODevice::ReadOnly)) {
        m_error = tr("The layout template %1 is not installed.").arg(name);
        return false;
    }
    const QString script = QString::fromUtf8(file.readAll());
    return evaluate(script, scriptFile);
}

bool LayoutTemplateRunner::evaluate(const QString &script, const QString &scriptFile)
{
    if (++m_depth > 16 || script.size() > 1024*1024) { --m_depth; m_error = "Layout exceeds execution limits"; return false; }
    if (m_depth == 1) installApi();
    std::mutex mutex; std::condition_variable_any done;
    std::jthread deadline([&](std::stop_token stop) {
        std::unique_lock lock(mutex);
        done.wait_for(lock, stop, std::chrono::seconds(3), [] { return false; });
        if (!stop.stop_requested()) m_engine->setInterrupted(true);
    });
    const QJSValue result = m_engine->evaluate(script, scriptFile);
    deadline.request_stop(); done.notify_all(); --m_depth;
    if (result.isError()) {
        m_error = tr("Layout %1: %2 (line %3)").arg(scriptFile, result.toString(), result.property(u"lineNumber"_s).toString());
        return false;
    }
    return true;
}


LayoutTemplateWidget::LayoutTemplateWidget(Plasma::Applet *applet, QObject *parent)
    : QObject(parent), m_applet(applet) {}
QVariant LayoutTemplateWidget::readConfig(const QString &key, const QVariant &fallback) const {
    if (!m_applet) return fallback;
    auto group=m_applet->config(); for(const auto &part:m_group) group=group.group(part);
    return group.readEntry(key,fallback);
}
void LayoutTemplateWidget::writeConfig(const QString &key,const QJSValue &value) {
    if(!m_applet || key.isEmpty()) return;
    auto group=m_applet->config();for(const auto &part:m_group)group=group.group(part);
    if(group.isEntryImmutable(key))return;
    // Plasma's scripting::Applet takes QJSValue, converts JS arrays, and updates
    // the original schema before writing the group. Passing QVariant directly
    // left a QJSValue in KConfig and silently dropped WhiteSur's launcher list.
    const auto converted=value.toVariant();
    if(auto *scheme=m_applet->configScheme())if(auto *item=scheme->findItemByName(key)){
        item->setProperty(converted);scheme->blockSignals(true);scheme->save();scheme->read();scheme->blockSignals(false);
        Q_EMIT scheme->configChanged();
    }
    group.writeEntry(key,converted);m_applet->configChanged();
}
QString LayoutTemplatePanel::wallpaperPlugin()const{return m_containment?m_containment->wallpaperPlugin():QString();}
void LayoutTemplatePanel::setWallpaperPlugin(const QString &v){if(m_containment)m_containment->setWallpaperPlugin(v);}
QString LayoutTemplatePanel::hiding()const{return QStringList{"normal","autohide","dodgewindows","windowsgobelow"}.value(m_pending.value("panelVisibility",0).toInt());}
void LayoutTemplatePanel::setHiding(const QString &v){const int i=QStringList{"normal","autohide","dodgewindows","windowsgobelow"}.indexOf(v);m_pending.insert("panelVisibility",i);}
QString LayoutTemplatePanel::lengthMode()const{return QStringList{"fill","fit","custom"}.value(m_pending.value("panelLengthMode",0).toInt());}
void LayoutTemplatePanel::setLengthMode(const QString &v){const int i=QStringList{"fill","fit","custom"}.indexOf(v);m_pending.insert("panelLengthMode",i);}
QString LayoutTemplatePanel::opacity()const{return m_pending.value("panelOpacity",2).toInt()==1?"opaque":"translucent";}
void LayoutTemplatePanel::setOpacity(const QString &v){m_pending.insert("panelOpacity",v=="opaque"?1:v=="translucent"?2:0);}
QJSValue LayoutTemplateRunner::desktopsForActivity(const QString &) {
    auto array=m_engine->newArray();int n=0;
    if(m_corona)for(auto *c:m_corona->containments())if(c->containmentType()==Plasma::Containment::Desktop)
        array.setProperty(n++,desktopById(c->id()));
    return array;
}
QJSValue LayoutTemplateRunner::desktopById(int id) {
    if(m_corona)for(auto *c:m_corona->containments())if(c->id()==uint(id)&&c->containmentType()==Plasma::Containment::Desktop) {
        auto *wrapper=new LayoutTemplatePanel(c,c->screen(),{},this);
        QJSEngine::setObjectOwnership(wrapper,QJSEngine::CppOwnership);return m_engine->newQObject(wrapper);
    }
    return QJSValue();
}
QJSValue LayoutTemplateRunner::loadTemplate(const QString &id) {
    if(!run("plasma-desktop-template:"+id)) return m_engine->throwError(m_error), QJSValue();
    return m_engine->newObject();
}
bool LayoutTemplateRunner::runLookAndFeel(const QString &id) {
    auto package=KPackage::PackageLoader::self()->loadPackage("Plasma/LookAndFeel",id);
    if(!package.isValid()){m_error="Invalid look-and-feel package";return false;}
    auto path=package.filePath("layouts","org.kde.plasma.desktop-layout.js");
    if(path.isEmpty()) {
        auto fallback=KPackage::PackageLoader::self()->loadPackage("Plasma/LookAndFeel","org.kde.breeze.desktop");
        path=fallback.filePath("layouts","org.kde.plasma.desktop-layout.js");
    }
    QFile file(path);if(!file.open(QIODevice::ReadOnly)){m_error="Missing native look-and-feel layout";return false;}
    return evaluate(QString::fromUtf8(file.readAll()),path);
}
void LayoutTemplateRunner::installApi() {
    auto global=m_engine->globalObject();QJSEngine::setObjectOwnership(this,QJSEngine::CppOwnership);
    global.setProperty("__bwm",m_engine->newQObject(this));global.setProperty("gridUnit",gridUnit());
    global.setProperty("languageId",QLocale::system().bcp47Name().section('-',0,0));
    m_engine->evaluate(QStringLiteral(R"JS(
function Panel(plugin){var p=__bwm.newPanel(plugin===undefined?'':plugin);if(p instanceof Error)throw p;return p;}
function panelById(id){return __bwm.panelById(id);}
function screenGeometry(s){return __bwm.screenGeometry(s);}
function print(m){__bwm.print(String(m));}
function loadTemplate(id){return __bwm.loadTemplate(id);}
function currentActivity(){return 'bwm';}
function desktopsForActivity(a){return __bwm.desktopsForActivity(a);}
function desktopById(id){return __bwm.desktopById(id);}
function activities(){return ['bwm'];}
var __plasmaApi=this;
function getApiVersion(v){if(v!==1)throw Error('Only Plasma scripting API 1 is supported');return __plasmaApi;}
Object.defineProperty(this,'panelIds',{get:function(){return __bwm.panelIds();}});
function __configs(object,configs){Object.keys(configs||{}).forEach(function(g){
 object.currentConfigGroup=g.split('/').filter(Boolean).map(decodeURIComponent);
 Object.keys(configs[g]).forEach(function(k){object.writeConfig(k,configs[g][k]);});});}
function loadSerializedLayout(data){
 if(Number(data.serializationFormatVersion)!==1)throw Error('Unsupported Plasma serialization version');
 var desktops=desktopsForActivity(currentActivity());
 (data.desktops||[]).slice(0,desktops.length).forEach(function(d,i){
  var target=desktops[i];target.wallpaperPlugin=d.wallpaperPlugin;__configs(target,d.config);
  (d.applets||[]).forEach(function(a){__configs(target.addWidget(a.plugin),a.config);});});
 (data.panels||[]).forEach(function(p){var target=new Panel();
  ['location','alignment','hiding','opacity','lengthMode','floating'].forEach(function(k){if(p[k]!==undefined)target[k]=p[k];});
  ['height','minimumLength','maximumLength','offset'].forEach(function(k){if(p[k]!==undefined)target[k]=Math.round(p[k]*gridUnit);});
  __configs(target,p.config);(p.applets||[]).forEach(function(a){__configs(target.addWidget(a.plugin),a.config);});});
}
)JS"));
}
