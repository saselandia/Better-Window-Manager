/*
    SPDX-FileCopyrightText: 2009 Aaron Seigo <aseigo@kde.org>
    SPDX-FileCopyrightText: 2023 Harald Sitter <sitter@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    "Add Panel" of the original desktop edit mode (ShellCorona::addPanel and
    ShellCorona::addPanel(QAction*) of plasma-workspace 6.7.5). Panel layout
    templates (Plasma/LayoutTemplate) run unchanged in a QJSEngine exposing the
    subset of the Plasma scripting API (shell/scripting) that panel templates use.
    Any other call throws, so an unsupported template fails visibly instead of
    being silently reinterpreted.
*/
#pragma once

#include <QHash>
#include <QJSValue>
#include <QObject>
#include <QPointer>
#include <QVariantMap>

class QJSEngine;
class QScreen;
class ViewCorona;
namespace Plasma
{
class Containment;
}

class LayoutTemplatePanel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(int id READ id CONSTANT)
    Q_PROPERTY(int screen READ screen CONSTANT)
    Q_PROPERTY(QString type READ type CONSTANT)
    Q_PROPERTY(QString formFactor READ formFactor)
    Q_PROPERTY(QString location READ location WRITE setLocation)
    Q_PROPERTY(int height READ height WRITE setHeight)
    Q_PROPERTY(QString alignment READ alignment WRITE setAlignment)
    Q_PROPERTY(int offset READ offset WRITE setOffset)
    Q_PROPERTY(int minimumLength READ minimumLength WRITE setMinimumLength)
    Q_PROPERTY(int maximumLength READ maximumLength WRITE setMaximumLength)
    Q_PROPERTY(QList<int> widgetIds READ widgetIds)
public:
    LayoutTemplatePanel(Plasma::Containment *containment, int screen, const QVariantMap &current, QObject *parent);
    int id() const;
    int screen() const { return m_screen; }
    QString type() const;
    QString formFactor() const;
    QString location() const;
    void setLocation(const QString &location);
    int height() const;
    void setHeight(int height);
    QString alignment() const;
    void setAlignment(const QString &alignment);
    int offset() const;
    void setOffset(int offset);
    int minimumLength() const;
    void setMinimumLength(int pixels);
    int maximumLength() const;
    void setMaximumLength(int pixels);
    QList<int> widgetIds() const;
    Q_INVOKABLE QVariant addWidget(const QString &plugin);
    QVariantMap pendingViewSettings() const { return m_pending; }
    Plasma::Containment *containment() const { return m_containment.data(); }

private:
    QPointer<Plasma::Containment> m_containment;
    int m_screen = 0;
    QVariantMap m_current;
    QVariantMap m_pending;
};

class LayoutTemplateRunner : public QObject
{
    Q_OBJECT
public:
    // existingPanels: live panel containment -> its current view settings (thickness, ...).
    LayoutTemplateRunner(ViewCorona *corona, QScreen *target, const QHash<Plasma::Containment *, QVariantMap> &existingPanels,
                         QObject *parent = nullptr);
    ~LayoutTemplateRunner() override;
    // "plasma-desktop-template:<id>" runs the template; any other value is a Panel containment
    // plugin and creates an empty one on the first free edge, as ShellCorona::addPanel.
    bool run(const QString &actionData);
    QString error() const { return m_error; }
    QList<LayoutTemplatePanel *> createdPanels() const { return m_created; }

    // Script API (ScriptEngine::V1 of plasma-workspace 6.7.5).
    Q_INVOKABLE QJSValue newPanel(const QString &plugin = QString());
    Q_INVOKABLE QJSValue panelById(int id);
    Q_INVOKABLE QVariantMap screenGeometry(int screen) const;
    Q_INVOKABLE QList<int> panelIds() const;
    Q_INVOKABLE void print(const QString &message) const;

private:
    LayoutTemplatePanel *createPanel(const QString &plugin);
    int screenIndex() const;
    QPointer<ViewCorona> m_corona;
    QPointer<QScreen> m_target;
    QHash<Plasma::Containment *, QVariantMap> m_existing;
    QJSEngine *m_engine = nullptr;
    QList<LayoutTemplatePanel *> m_created;
    QString m_error;
};
