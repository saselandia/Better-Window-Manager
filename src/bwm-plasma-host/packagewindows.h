// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QObject>
#include <QPointer>
#include <QVariantList>
#include <QHash>
#include <QSet>
namespace Plasma {class Containment;}
class QQuickWindow;
class PackageWindows : public QObject {
    Q_OBJECT
    Q_PROPERTY(QVariantList capabilities READ capabilities NOTIFY changed)
public:
    explicit PackageWindows(Plasma::Containment *containment,QObject *parent=nullptr);
    QVariantList capabilities()const;
    Q_INVOKABLE void refresh();
    // Suspend only this containment's windows before its panel view is withdrawn.
    void suspend();
Q_SIGNALS:
    void changed();
protected:
    bool eventFilter(QObject *,QEvent *)override;
private:
    void schedule();
    void prepare(QQuickWindow *window,bool creatingSurface=false);
    QPointer<Plasma::Containment> m_containment;
    QHash<QQuickWindow*,QVariantMap> m_records;
    QSet<QQuickWindow*> m_observedPopups,m_trackedWindows;
    bool m_scheduled=false;
};
