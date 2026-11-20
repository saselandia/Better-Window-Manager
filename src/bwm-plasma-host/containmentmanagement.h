/*
 * SPDX-FileCopyrightText: 2021 Cyril Rossi <cyril.rossi@enioka.com>
 * SPDX-FileCopyrightText: 2026 BWM contributors
 * SPDX-License-Identifier: LGPL-2.0-or-later
 * Host models adapted from plasma-workspace 6.7.5 shell/shellcontainmentconfig.
 * The installed ShellContainmentConfiguration.qml and its delegates stay unchanged.
 */
#pragma once
#include <QAbstractListModel>
#include <QQmlApplicationEngine>
#include <QPointer>
#include <QTimer>
class ViewCorona;
class QWindow;
namespace Plasma {class Containment;}
class ScreenContainmentModel;

class ContainmentListModel : public QAbstractListModel {
    Q_OBJECT
public:
    enum Roles {ContainmentIdRole=Qt::UserRole+1,ScreenRole,EdgeRole,EdgePositionRole,
        PanelCountAtRightRole,PanelCountAtTopRole,PanelCountAtLeftRole,PanelCountAtBottomRole,
        ActivityRole,IsActiveRole,ImageSourceRole,DestroyedRole};
    ContainmentListModel(ViewCorona *corona,int screen,ScreenContainmentModel *parent);
    int rowCount(const QModelIndex &parent={})const override;
    QVariant data(const QModelIndex &index,int role)const override;
    QHash<int,QByteArray> roleNames()const override;
    Q_INVOKABLE void remove(int id);
    Q_INVOKABLE void moveContainementToScreen(uint id,int screen);
private:
    QPointer<ViewCorona> m_corona;
    int m_screen;
    QList<QPointer<Plasma::Containment>> m_rows;
};
class ScreenContainmentModel : public QAbstractListModel {
    Q_OBJECT
public:
    enum Roles {ScreenIdRole=Qt::UserRole+1,ScreenNameRole,ContainmentsRole,PrimaryRole,EnabledRole};
    explicit ScreenContainmentModel(ViewCorona *corona,QObject *parent=nullptr);
    int rowCount(const QModelIndex &parent={})const override;
    QVariant data(const QModelIndex &index,int role)const override;
    QHash<int,QByteArray> roleNames()const override;
    Q_INVOKABLE void remove(int screen);
    void load();
private:
    void observe(Plasma::Containment *c);
    QPointer<ViewCorona> m_corona;
    struct Screen {int id;QString name;bool primary,enabled;ContainmentListModel *containments;};
    QList<Screen> m_rows;
    QTimer m_reload;
};
class ContainmentManagement : public QQmlApplicationEngine {
    Q_OBJECT
public:
    explicit ContainmentManagement(ViewCorona *corona);
    bool init();
    QWindow *window()const;
    ScreenContainmentModel *model()const{return m_model;}
private:
    QPointer<ViewCorona> m_corona;
    ScreenContainmentModel *m_model=nullptr;
};
