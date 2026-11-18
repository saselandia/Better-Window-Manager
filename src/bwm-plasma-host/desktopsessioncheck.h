// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonObject>
#include <QStringList>

// Original KDE consumer on Qt's connection. No windows or activation requests.
QJsonObject nativeDesktopSessionSnapshot(const QStringList &descriptions, int timeoutMs=2500);

// Explicit opt-in test: focus already-active desktops on other outputs, then
// the original output. Never requests relocation or a new desktop.
QJsonObject nativeDesktopFocusCycle(const QString &originalOutput, const QStringList &descriptions);

// Explicit same-output navigation to an existing projected, non-visible ID.
QJsonObject nativeDesktopWorkspaceCycle(const QString &originalOutput, const QString &target, const QStringList &descriptions);
