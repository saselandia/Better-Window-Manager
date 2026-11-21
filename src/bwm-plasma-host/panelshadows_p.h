/*
    SPDX-FileCopyrightText: 2011 Aaron Seigo <aseigo@kde.org>
    SPDX-FileCopyrightText: 2026 BWM contributors

    SPDX-License-Identifier: LGPL-2.0-or-later
*/

#pragma once

#include <QSet>
#include <QVariantMap>

#include <KSvg/FrameSvg>
#include <KSvg/Svg>

class PanelShadows : public KSvg::Svg
{
    Q_OBJECT

public:
    explicit PanelShadows(QObject *parent = nullptr, const QString &prefix = QStringLiteral("widgets/panel-background"));
    ~PanelShadows() override;

    static PanelShadows *self();

    void addWindow(QWindow *window, KSvg::FrameSvg::EnabledBorders enabledBorders = KSvg::FrameSvg::AllBorders, const QMargins &extraPadding = {});
    void removeWindow(QWindow *window);

    void setEnabledBorders(QWindow *window, KSvg::FrameSvg::EnabledBorders enabledBorders = KSvg::FrameSvg::AllBorders);
    QMargins extraPadding(QWindow *window) const;
    QVariantMap windowState(QWindow *window) const; // BWM: request state, not proof of presentation.

private:
    class Private;
    Private *const d;
};
