/*
    SPDX-FileCopyrightText: 2014 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later

    Adapted from plasma-workspace 6.7.5 shell/alternativeshelper.cpp.
    Replaces a panel applet with a chosen alternative providing the same
    X-Plasma-Provides contract, preserving its native configuration,
    global shortcut and panel slot.
*/
#include "alternativeshelper.h"

#include <KConfigGroup>
#include <KConfigLoader>
#include <Plasma/Containment>
#include <PlasmaQuick/AppletQuickItem>
#include <QVariantList>
#include <qqml.h>

namespace {
QStringList storedAppletOrder(Plasma::Containment *containment)
{
    if (!containment) return {};
    if (auto *scheme = containment->configScheme()) {
        if (auto *entry = scheme->KCoreConfigSkeleton::findItem(QStringLiteral("AppletOrder")))
            return entry->property().toString().split(u';', Qt::SkipEmptyParts);
    }
    return containment->config().group(QStringLiteral("General")).readEntry(QStringLiteral("AppletOrder"), QString()).split(u';', Qt::SkipEmptyParts);
}
}

void AlternativesHelper::registerTypes()
{
    static const int v2 = qmlRegisterUncreatableType<AlternativesHelper>(
        "org.kde.plasma.shell", 2, 0, "AlternativesHelper", QStringLiteral("Created by the shell"));
    static const int v1 = qmlRegisterUncreatableType<AlternativesHelper>(
        "org.kde.plasma.shell", 1, 0, "AlternativesHelper", QStringLiteral("Created by the shell"));
    Q_UNUSED(v2);
    Q_UNUSED(v1);
}

AlternativesHelper::AlternativesHelper(Plasma::Applet *applet, QObject *parent)
    : QObject(parent)
    , m_applet(applet)
{
}

AlternativesHelper::~AlternativesHelper() = default;

QStringList AlternativesHelper::appletProvides() const
{
    if (!m_applet) return {};
    return m_applet->pluginMetaData().value(QStringLiteral("X-Plasma-Provides"), QStringList());
}

QString AlternativesHelper::currentPlugin() const
{
    if (!m_applet) return {};
    return m_applet->pluginMetaData().pluginId();
}

QQuickItem *AlternativesHelper::applet() const
{
    return m_applet ? PlasmaQuick::AppletQuickItem::itemForApplet(m_applet) : nullptr;
}

void AlternativesHelper::loadAlternative(const QString &plugin)
{
    if (!m_applet || m_applet->destroyed() || plugin.isEmpty()
        || plugin == m_applet->pluginMetaData().pluginId() || m_applet->isContainment()) {
        return;
    }

    Plasma::Containment *cont = m_applet->containment();
    if (!cont || cont->immutable() || m_applet->immutable()) {
        return;
    }

    QQuickItem *appletItem = PlasmaQuick::AppletQuickItem::itemForApplet(m_applet);
    QQuickItem *contItem = PlasmaQuick::AppletQuickItem::itemForApplet(cont);
    if (!appletItem || !contItem) {
        return;
    }

    const uint oldId = m_applet->id();
    QStringList expectedOrder = storedAppletOrder(cont);
    const int oldIndex = expectedOrder.indexOf(QString::number(oldId));

    // Ensure the global shortcut is moved to the new applet.
    const QKeySequence shortcut = m_applet->globalShortcut();
    m_applet->setGlobalShortcut(QKeySequence()); // Need to unmap the old one first.

    const QPoint newPos = appletItem->mapToItem(contItem, QPointF(0, 0)).toPoint();
    Plasma::Applet *newApplet = cont->createApplet(plugin, {}, QRectF(newPos, QSizeF()));
    if (!newApplet || newApplet->failedToLaunch()) {
        if (newApplet) newApplet->destroy();
        m_applet->setGlobalShortcut(shortcut);
        return;
    }

    newApplet->setGlobalShortcut(shortcut);
    KConfigGroup oldCg(m_applet->config());
    m_applet->save(oldCg);
    KConfigGroup newCg(newApplet->config());
    oldCg.copyTo(&newCg);
    newCg.sync();
    if (auto *scheme = newApplet->configScheme()) {
        scheme->load();
        Q_EMIT scheme->configChanged();
    }
    newApplet->configChanged();

    const uint newId = newApplet->id();
    m_applet->destroy();

    // If the panel layout was not yet geometrically polished (e.g. offscreen),
    // coordinate insertion may have appended the replacement instead of keeping
    // the replaced widget's slot. Reconcile through the native reorderApplets
    // contract when the stored slot was known.
    if (oldIndex >= 0 && contItem->metaObject()->indexOfMethod("reorderApplets(QVariant)") >= 0) {
        expectedOrder[oldIndex] = QString::number(newId);
        if (storedAppletOrder(cont) != expectedOrder) {
            QVariantList ids;
            for (const auto &entry : expectedOrder) {
                bool ok = false;
                const uint id = entry.toUInt(&ok);
                if (ok) ids.append(id);
            }
            QMetaObject::invokeMethod(contItem, "reorderApplets", Q_ARG(QVariant, QVariant(ids)));
        }
    }
}
