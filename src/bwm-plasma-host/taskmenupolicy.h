// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QActionGroup>
#include <QHash>
#include <QPersistentModelIndex>
#include <QSet>
#include <QVariantMap>
#include <QJsonObject>
class QMenu;
class TaskMenuPolicy:public QObject {
    Q_OBJECT
public:
    explicit TaskMenuPolicy(QObject *parent=nullptr);
    ~TaskMenuPolicy()override;
    void attach(QObject *root);
    void setSuspended(bool suspended);
    bool apply(QMenu *menu);
    QVariantMap state()const;
Q_SIGNALS:
    void launchRequested(QJsonObject request);
protected:
    bool eventFilter(QObject *watched,QEvent *event)override;
private:
    bool owned(QObject *object)const;
    QObject *contextFor(QMenu *menu)const;
    bool allowed(const QModelIndex &index,const QString &operation)const;
    bool managed(const QModelIndex &index)const;
    void release(QMenu *menu);
    void unmask(QAction *action);
    bool mask(QAction *action);
    void routeLaunchActions(QMenu *menu,QObject *context,const QModelIndex &index);
    struct Bound {
        QPointer<QMenu> menu;
        QPersistentModelIndex index;
        QList<QMetaObject::Connection> connections;
        QList<QPointer<QAction>> actions;
        QHash<QAction*,QMetaObject::Connection> routed;
        bool blocked=false,previouslyEnabled=true;
    };
    QList<QPointer<QObject>> m_roots;
    QHash<QMenu*,Bound> m_bound;
    struct Mask{QPointer<QAction> action;QPointer<QActionGroup> group;};
    QHash<QAction*,Mask> m_masks;
    QSet<QMenu*> m_applying;
    bool m_suspended=false;
    QString m_error;
    int m_routedActions=0,m_maskedLaunchActions=0;
};
