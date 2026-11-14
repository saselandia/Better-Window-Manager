// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <KCModule>
#include <QProcess>
#include <QTimer>
class QCheckBox;
class QSpinBox;
class QLabel;

// Native KCM; delegates to the shared BWM controller, never starts a KDE nightlight daemon.
class NightlightModule : public KCModule {
    Q_OBJECT
public:
    NightlightModule(QObject *parent, const KPluginMetaData &data);
    NightlightModule(QObject *parent, const KPluginMetaData &data, const QStringList &backend);
    void load() override;
    void save() override;
    void defaults() override;
private:
    void request(const QStringList &arguments);
    void updateChanged();
    QStringList m_backend;
    QProcess m_process;
    QTimer m_timeout;
    QCheckBox *m_enabled;
    QSpinBox *m_temperature;
    QLabel *m_error;
    bool m_savedEnabled = false;
    int m_savedTemperature = 4000;
    bool m_valid = false;
};
