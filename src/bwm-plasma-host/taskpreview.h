// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QList>
#include <QString>
namespace Plasma { class Applet; }
// Explicit disposable-preview option; not a replacement for desktop protocols.
bool prepareAllDesktopTaskPreview(const QList<Plasma::Applet*> &applets,QString *error);
