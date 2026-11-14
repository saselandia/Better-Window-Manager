// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <KCModule>
#include <QJsonObject>
#include <QMap>
#include <functional>
class QFormLayout;
class QLabel;
class ManagerModule : public KCModule {
    Q_OBJECT
public:
    ManagerModule(QObject *, const KPluginMetaData &);
    ManagerModule(QObject *, const KPluginMetaData &, const QStringList &backend);
    void load() override;
    void save() override;
private:
    bool request(const QString &, const QJsonObject &, QJsonObject &);
    void populate(const QJsonObject &);
    void updateChanged();
    QJsonObject changes() const;
    QStringList m_backend;
    QFormLayout *m_form;
    QLabel *m_error;
    QWidget *m_fields;
    QJsonObject m_values;
    QString m_revision;
    QMap<QString, std::function<QJsonValue()>> m_readers;
};
