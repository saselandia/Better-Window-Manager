/*
 * SPDX-FileCopyrightText: 2021 Cyril Rossi <cyril.rossi@enioka.com>
 * SPDX-FileCopyrightText: 2026 BWM contributors
 * SPDX-License-Identifier: LGPL-2.0-or-later
 */
#include "containmentmanagement.h"
#include "viewcorona.h"
#include <Plasma/Containment>
#include <KLocalizedContext>
#include <KLocalizedString>
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <QAction>
#include <QGuiApplication>
#include <QQmlContext>
#include <QScreen>
#include <QWindow>
#include <algorithm>

namespace {
bool panel(const Plasma::Containment *c) {
    return c->containmentType()==Plasma::Containment::Panel || c->containmentType()==Plasma::Containment::CustomPanel;
}
int screenId(const Plasma::Containment *c) {return c->screen()>=0 ? c->screen() : c->lastScreen();}
QString edge(const Plasma::Containment *c) {
    switch(c->location()) {
    case Plasma::Types::TopEdge:return QStringLiteral("top");
    case Plasma::Types::BottomEdge:return QStringLiteral("bottom");
    case Plasma::Types::LeftEdge:return QStringLiteral("left");
    case Plasma::Types::RightEdge:return QStringLiteral("right");
    default:return QStringLiteral("floating");
    }
}
}
ContainmentListModel::ContainmentListModel(ViewCorona *corona,int screen,ScreenContainmentModel *parent)
    :QAbstractListModel(parent),m_corona(corona),m_screen(screen) {
    for(auto *c:corona->containments()) {
        // Embedded tray containments belong to their applet, not to another screen card.
        if(qobject_cast<Plasma::Applet*>(c->parent()) || screenId(c)!=screen)continue;
        m_rows.append(c);
        corona->grabContainmentPreview(c);
    }
    connect(corona,&ViewCorona::containmentPreviewReady,this,[this](Plasma::Containment *c){
        const auto row=m_rows.indexOf(c);if(row>=0)emit dataChanged(index(row),index(row),{ImageSourceRole});
    });
}
int ContainmentListModel::rowCount(const QModelIndex &parent)const{return parent.isValid()?0:m_rows.size();}
QVariant ContainmentListModel::data(const QModelIndex &index,int role)const {
    if(!index.isValid() || index.column()!=0 || index.row()<0 || index.row()>=m_rows.size())return {};
    auto *c=m_rows[index.row()].data();if(!c)return role==DestroyedRole ? QVariant(true) : QVariant();
    const auto edgeCount=[this](Plasma::Types::Location location) {
        int count=0;if(m_corona)for(auto *other:m_corona->containments())
            if(!other->destroyed() && panel(other) && screenId(other)==m_screen && other->location()==location)++count;
        return count;
    };
    switch(role) {
    case ContainmentIdRole:return c->id();
    case ScreenRole:return screenId(c);
    case EdgeRole:return edge(c);
    case EdgePositionRole:{int position=0;for(const auto &other:m_rows){if(other==c)break;if(other && !other->destroyed() && other->location()==c->location())++position;}return position;}
    case PanelCountAtRightRole:return edgeCount(Plasma::Types::RightEdge);
    case PanelCountAtTopRole:return edgeCount(Plasma::Types::TopEdge);
    case PanelCountAtLeftRole:return edgeCount(Plasma::Types::LeftEdge);
    case PanelCountAtBottomRole:return edgeCount(Plasma::Types::BottomEdge);
    case ActivityRole:return c->activityName();
    case IsActiveRole:return c->screen()>=0;
    case ImageSourceRole:return m_corona ? m_corona->containmentPreviewPath(c) : QString();
    case DestroyedRole:return c->destroyed();
    }
    return {};
}
QHash<int,QByteArray> ContainmentListModel::roleNames()const {
    return {{ContainmentIdRole,"containmentId"},{ScreenRole,"screen"},{EdgeRole,"edge"},{EdgePositionRole,"edgePosition"},
        {PanelCountAtRightRole,"panelCountAtRight"},{PanelCountAtTopRole,"panelCountAtTop"},
        {PanelCountAtLeftRole,"panelCountAtLeft"},{PanelCountAtBottomRole,"panelCountAtBottom"},
        {ActivityRole,"activity"},{IsActiveRole,"active"},{ImageSourceRole,"imageSource"},{DestroyedRole,"isDestroyed"}};
}
void ContainmentListModel::remove(int id) {
    if(!m_corona || m_corona->immutability()!=Plasma::Types::Mutable)return;
    for(const auto &c:m_rows)if(c && int(c->id())==id && !c->immutable())
        if(auto *action=c->internalAction(QStringLiteral("remove")))action->trigger();
}
void ContainmentListModel::moveContainementToScreen(uint id,int screen) {
    if(!m_corona)return;
    for(const auto &c:m_rows)if(c && c->id()==id && !c->destroyed()) {
        m_corona->moveContainmentToScreen(c,screen);return;
    }
}
ScreenContainmentModel::ScreenContainmentModel(ViewCorona *corona,QObject *parent):QAbstractListModel(parent),m_corona(corona) {
    m_reload.setSingleShot(true);m_reload.setInterval(200);
    connect(&m_reload,&QTimer::timeout,this,&ScreenContainmentModel::load);
    connect(corona,&Plasma::Corona::screenAdded,&m_reload,qOverload<>(&QTimer::start));
    connect(corona,&Plasma::Corona::screenRemoved,&m_reload,qOverload<>(&QTimer::start));
    connect(corona,&Plasma::Corona::containmentAdded,this,[this](Plasma::Containment *c){observe(c);m_reload.start();});
    for(auto *c:corona->containments())observe(c);
}
void ScreenContainmentModel::observe(Plasma::Containment *c) {
    connect(c,&Plasma::Containment::screenChanged,&m_reload,qOverload<>(&QTimer::start));
    connect(c,&Plasma::Containment::locationChanged,&m_reload,qOverload<>(&QTimer::start));
    connect(c,&Plasma::Applet::destroyedChanged,&m_reload,qOverload<>(&QTimer::start));
    connect(c,&QObject::destroyed,&m_reload,qOverload<>(&QTimer::start));
}
void ScreenContainmentModel::load() {
    if(!m_corona)return;
    beginResetModel();
    for(const auto &row:m_rows)delete row.containments;
    m_rows.clear();
    QSet<int> unknown;
    for(auto *c:m_corona->containments())if(!c->destroyed() && !qobject_cast<Plasma::Applet*>(c->parent()))unknown.insert(screenId(c));
    const auto screens=QGuiApplication::screens();
    for(int i=0;i<screens.size();++i) {
        unknown.remove(i);auto *screen=screens[i];
        auto *containments=new ContainmentListModel(m_corona,i,this);
        // Match Plasma: cards without any assigned containments are omitted.
        if(containments->rowCount()==0){delete containments;continue;}
        QString name;
        if(screen->name().contains(QLatin1String("eDP")))name=i18nd("plasmashell","Internal Screen on %1",screen->name());
        else if(screen->model().contains(screen->name()))name=screen->model();
        else name=i18ndc("plasmashell","Screen manufacturer and model on connector","%1 %2 on %3",screen->manufacturer(),screen->model(),screen->name());
        m_rows.append({i,name,screen==QGuiApplication::primaryScreen(),true,containments});
    }
    auto disconnected=unknown.values();std::sort(disconnected.begin(),disconnected.end());
    for(int id:disconnected)m_rows.append({id,i18nd("plasmashell","Disconnected Screen %1",id+1),false,false,new ContainmentListModel(m_corona,id,this)});
    endResetModel();
}
int ScreenContainmentModel::rowCount(const QModelIndex &parent)const{return parent.isValid()?0:m_rows.size();}
QVariant ScreenContainmentModel::data(const QModelIndex &index,int role)const {
    if(!index.isValid() || index.column()!=0 || index.row()<0 || index.row()>=m_rows.size())return {};
    const auto &row=m_rows[index.row()];
    switch(role){case ScreenIdRole:return row.id;case ScreenNameRole:return row.name;
        case ContainmentsRole:return QVariant::fromValue<QObject*>(row.containments);
        case PrimaryRole:return row.primary;case EnabledRole:return row.enabled;}
    return {};
}
QHash<int,QByteArray> ScreenContainmentModel::roleNames()const {
    return {{ScreenIdRole,"screenId"},{ScreenNameRole,"screenName"},{ContainmentsRole,"containments"},{PrimaryRole,"isPrimary"},{EnabledRole,"isEnabled"}};
}
void ScreenContainmentModel::remove(int screen) {
    if(!m_corona || m_corona->immutability()!=Plasma::Types::Mutable || (screen>=0 && screen<QGuiApplication::screens().size()))return;
    for(auto *c:m_corona->containments())if(screenId(c)==screen && !c->immutable())
        if(auto *action=c->internalAction(QStringLiteral("remove")))action->trigger();
}
ContainmentManagement::ContainmentManagement(ViewCorona *corona):QQmlApplicationEngine(corona),m_corona(corona) {}
bool ContainmentManagement::init() {
    m_model=new ScreenContainmentModel(m_corona,this);m_model->load();
    auto *localized=new KLocalizedContext(this);localized->setTranslationDomain(QStringLiteral("plasma_shell_org.kde.plasma.desktop"));
    rootContext()->setContextObject(localized);
    rootContext()->setContextProperty(QStringLiteral("ShellContainmentModel"),m_model);
    const auto package=KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/Shell"),QStringLiteral("org.kde.plasma.desktop"));
    if(!package.isValid() || package.fileUrl("containmentmanagementui").isEmpty())return false;
    load(package.fileUrl("containmentmanagementui"));
    auto *view=window();if(!view)return false;
    connect(view,&QWindow::visibleChanged,this,[this](bool visible){if(!visible)deleteLater();});
    return true;
}
QWindow *ContainmentManagement::window()const{return rootObjects().isEmpty()?nullptr:qobject_cast<QWindow*>(rootObjects().first());}
