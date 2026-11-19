/*
    SPDX-FileCopyrightText: 2014 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/alternativeshelper.h for the
    installed, unmodified explorer/AppletAlternatives.qml.
*/
#pragma once

#include <Plasma/Applet>
#include <QPointer>
#include <QQuickItem>

class AlternativesHelper : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QStringList appletProvides READ appletProvides CONSTANT)
    Q_PROPERTY(QString currentPlugin READ currentPlugin CONSTANT)
    Q_PROPERTY(QQuickItem *applet READ applet CONSTANT)

public:
    explicit AlternativesHelper(Plasma::Applet *applet, QObject *parent = nullptr);
    ~AlternativesHelper() override;

    static void registerTypes();

    QQuickItem *applet() const;
    QStringList appletProvides() const;
    QString currentPlugin() const;

    Q_INVOKABLE void loadAlternative(const QString &plugin);

private:
    QPointer<Plasma::Applet> m_applet;
};
