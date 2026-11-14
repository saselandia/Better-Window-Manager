// SPDX-License-Identifier: GPL-2.0-or-later
#include "panelviewsettings.h"
#include <KConfig>
#include <KConfigGroup>
#include <QCryptographicHash>
#include <QDir>
#include <QFileInfo>
#include <QLockFile>
#include <QStandardPaths>
#include <cmath>

namespace {
KConfigGroup group(KConfig &config,const QStringList &path) {
    KConfigGroup result(&config,path.first());for(int i=1;i<path.size();++i)result=result.group(path[i]);return result;
}
}
PanelViewSettings::PanelViewSettings(QString fileName,uint id,bool vertical,int extent,QVariantMap defaults,bool nativeVisibility)
    :m_fileName(std::move(fileName)),m_panel(QStringLiteral("Panel %1").arg(id)),
     m_resolution((vertical ? QStringLiteral("Vertical") : QStringLiteral("Horizontal"))+QString::number(extent)),m_defaults(std::move(defaults)),
     m_nativeVisibility(nativeVisibility),m_screenExtent(extent) {
    // Keep the relative native filename for KConfig's XDG/kdedefaults cascade.
    // The absolute destination is only the identity of our serialization lock.
    m_filePath=QDir::isRelativePath(m_fileName) ? QDir(QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation)).filePath(m_fileName) : m_fileName;
}
QStringList PanelViewSettings::keys()const {
    QStringList result={"floating","floatingApplets","panelOpacity","thickness","minLength","maxLength"};
    if(m_nativeVisibility)result.append("panelVisibility");return result;
}
QList<PanelViewSettings::Target> PanelViewSettings::targets(const QString &key,bool readFallback)const {
    const QStringList base={"PlasmaViews",m_panel};
    if(key=="thickness")return {{base+QStringList{"Defaults"},key}};
    if(key=="minLength" || key=="maxLength")return {{base+QStringList{m_resolution},key},{base+QStringList{"Defaults"},key}};
    if(key=="panelVisibility" && readFallback)return {{base,key},{base+QStringList{m_resolution},key}};
    return {{base,key}};
}
QString PanelViewSettings::lockPath()const {
    const auto digest=QCryptographicHash::hash(m_filePath.toUtf8(),QCryptographicHash::Sha256).toHex();
    return QDir(QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation)).filePath("bwm-panel-view-"+QString::fromLatin1(digest)+".lock");
}
bool PanelViewSettings::validate(QVariantMap &values)const {
    for(const auto &key:keys()) {
        if(!values.contains(key)){m_error=QStringLiteral("Missing native panel setting: %1").arg(key);return false;}
        const auto value=values.value(key);bool ok=false;double number=value.toDouble(&ok);
        const bool flag=key=="floating" || key=="floatingApplets";
        if(value.metaType().id()==QMetaType::Bool && flag){number=value.toBool()?1:0;ok=true;}
        else if(value.metaType().id()==QMetaType::QString || value.metaType().id()==QMetaType::Bool)ok=false;
        if(!ok || !std::isfinite(number) || std::floor(number)!=number || number<0 || number>8192) {
            m_error=QStringLiteral("Invalid native panel value: %1").arg(key);return false;
        }
        const int n=int(number);
        if((flag && n>1) || (key=="panelOpacity" && n!=1 && n!=2) || (key=="panelVisibility" && n!=0 && n!=3) ||
           (key=="thickness" && (n<16 || n>256)) || ((key=="minLength" || key=="maxLength") && n<64)) {
            m_error=key=="panelOpacity" ? QStringLiteral("Adaptive or unknown panel opacity is not supported by this host.") : QStringLiteral("Panel setting outside supported range: %1").arg(key);return false;
        }
        values.insert(key,n);
    }
    if(values.value("minLength").toInt()>values.value("maxLength").toInt()) {m_error=QStringLiteral("Panel minimum length exceeds maximum length.");return false;}
    if(m_nativeVisibility && values.value("maxLength").toInt()>m_screenExtent){m_error=QStringLiteral("Native panel length exceeds its output.");return false;}
    return true;
}
bool PanelViewSettings::read(KConfig &config,QVariantMap &values)const {
    const auto base=group(config,{"PlasmaViews",m_panel});
    // These original settings have no controller in the preview host. Preserve
    // them, but do not open a view that silently ignores an explicitly different policy.
    QMap<QString,int> fixed={{"panelLengthMode",2},{"alignment",1}};
    for(auto it=fixed.cbegin();it!=fixed.cend();++it)if(base.hasKey(it.key())) {
        bool ok=false;const int value=base.readEntry(it.key(),QString()).toInt(&ok);
        if(!ok || value!=it.value()){m_error=QStringLiteral("Native panel policy needs an unavailable controller: %1").arg(it.key());return false;}
    }
    if(!m_nativeVisibility)for(const auto &target:targets("panelVisibility",true)) {
        const auto g=group(config,target.groups);if(!g.hasKey(target.key))continue;
        bool ok=false;const int policy=g.readEntry(target.key,QString()).toInt(&ok);
        if(!ok || policy!=3){m_error=QStringLiteral("Native panel policy needs an unavailable controller: panelVisibility");return false;}
        break;
    }
    for(const auto &path:{QStringList{"PlasmaViews",m_panel,m_resolution},QStringList{"PlasmaViews",m_panel,"Defaults"}}) {
        const auto g=group(config,path);if(!g.hasKey("offset"))continue;
        bool ok=false;const int value=g.readEntry("offset",QString()).toInt(&ok);
        if(!ok || value!=0){m_error=QStringLiteral("Native panel offset needs an unavailable positioning controller.");return false;}
        break;
    }
    values=m_defaults;
    for(const auto &key:keys())for(const auto &target:targets(key,true)) {
        auto g=group(config,target.groups);
        if(!g.hasKey(key))continue;
        bool ok=false;const int value=g.readEntry(key,QString()).toInt(&ok);
        if(!ok){m_error=QStringLiteral("Malformed native panel setting: %1").arg(key);return false;}
        values.insert(key,value);break; // Resolution-specific min/max precede Defaults.
    }
    return validate(values);
}
QVariantList PanelViewSettings::signature(KConfig &config,const QString &key)const {
    QVariantList result;
    for(const auto &target:targets(key,true)){auto g=group(config,target.groups);result.append(g.hasKey(key));result.append(g.readEntry(key,QString()));}
    return result;
}
bool PanelViewSettings::reload() {
    m_error.clear();m_ready=false;
    KConfig config(m_fileName,KConfig::FullConfig);QVariantMap values;
    if(!read(config,values))return false;
    m_values=values;m_baseline.clear();
    for(const auto &key:keys())m_baseline.insert(key,signature(config,key));
    m_ready=true;return true;
}
bool PanelViewSettings::apply(const QVariantMap &changes) {
    m_error.clear();if(!m_ready){m_error=QStringLiteral("Reload panel preferences before applying.");return false;}
    auto candidate=m_values;
    for(auto it=changes.cbegin();it!=changes.cend();++it) {
        if(!keys().contains(it.key())){m_error=QStringLiteral("No native panel adapter for key: %1").arg(it.key());return false;}
        candidate.insert(it.key(),it.value());
    }
    if(!validate(candidate))return false;
    QLockFile lock(lockPath());
    if(!lock.tryLock(0)){m_error=QStringLiteral("Another BWM panel preference transaction is running.");return false;}
    // Private KConfig owner: a failed sync must never be retried on destruction.
    // KConfig itself serializes/merges the single native file under its backend lock.
    KConfig writer(m_fileName,KConfig::FullConfig);QVariantMap current;
    if(!read(writer,current))return false;
    QStringList changed;
    for(const auto &key:keys())if(candidate.value(key)!=m_values.value(key))changed.append(key);
    for(const auto &key:changed) {
        if(signature(writer,key)!=m_baseline.value(key)){m_error=QStringLiteral("Panel setting changed elsewhere; reload before applying: %1").arg(key);return false;}
        for(const auto &target:targets(key,true)) {
            auto g=group(writer,target.groups);
            if(g.isImmutable() || g.isEntryImmutable(key)){m_error=QStringLiteral("Panel setting is locked by KDE policy: %1").arg(key);return false;}
        }
        current.insert(key,candidate.value(key));
    }
    if(!validate(current))return false;
    if(changed.isEmpty())return reload();
    if(!writer.isConfigWritable(false)){m_error=QStringLiteral("Native panel preferences are not writable.");return false;}
    for(const auto &key:changed)for(const auto &target:targets(key))group(writer,target.groups).writeEntry(key,candidate.value(key).toInt());
    if(!writer.sync()){writer.markAsClean();m_error=QStringLiteral("Could not sync native panel preferences.");return false;}
    if(!reload())return false;
    for(const auto &key:changed)if(m_values.value(key)!=candidate.value(key)){m_error=QStringLiteral("Native panel preference readback failed: %1").arg(key);return false;}
    return true;
}
