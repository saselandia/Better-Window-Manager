// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QString>
#include <QList>
class QScreen;
namespace BwmOutput {
struct Identity {QString manufacturer,model,serial;};
struct Match {int index=-1;QString status;};
QString normalized(QString description);
Identity identity(QScreen *screen);
Match resolve(const QString &description,const QList<Identity> &outputs);
QScreen *resolveScreen(const QString &description,QString *status=nullptr);
}
