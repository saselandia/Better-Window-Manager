// SPDX-License-Identifier: GPL-2.0-or-later
#include "kcmhost.h"
#include <QQmlEngineExtensionPlugin>
#include <qqml.h>

class BwmKcmPlugin : public QQmlExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char *uri) override { qmlRegisterType<KcmHost>(uri, 1, 0, "KcmHost"); }
};
#include "plugin.moc"
