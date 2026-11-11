// SPDX-License-Identifier: GPL-2.0-or-later
// BWM F11: loads a real Plasma KCM (KQuickConfigModule) in the window's own QML engine, as
// systemsettings does, so its pages can be shown there. The pages go into a Kirigami PageRow in
// QML (KcmPage.qml, as kcmutils' KCModuleQml); this item only loads and owns the module.
#pragma once
#include <QPointer>
#include <QQuickItem>
#include <QString>
#include <QVariantMap>

class KQuickConfigModule;

class KcmHost : public QQuickItem {
    Q_OBJECT
    Q_PROPERTY(QString module READ module WRITE setModule NOTIFY moduleChanged)
    Q_PROPERTY(QObject *kcm READ kcm NOTIFY kcmChanged)
    Q_PROPERTY(QString error READ error NOTIFY errorChanged)
    Q_PROPERTY(QString name READ name NOTIFY kcmChanged)
    Q_PROPERTY(QString description READ description NOTIFY kcmChanged)
    Q_PROPERTY(QString iconName READ iconName NOTIFY kcmChanged)
    Q_PROPERTY(int depth READ depth NOTIFY depthChanged)
    Q_PROPERTY(QQuickItem *mainUi READ mainUi NOTIFY kcmChanged)
public:
    explicit KcmHost(QQuickItem *parent = nullptr);
    ~KcmHost() override;

    QString module() const { return m_module; }
    void setModule(const QString &module);
    QObject *kcm() const;
    QString error() const { return m_error; }
    QString name() const { return m_name; }
    QString description() const { return m_description; }
    QString iconName() const { return m_icon; }
    int depth() const;
    QQuickItem *mainUi() const;
    Q_INVOKABLE QQuickItem *subPage(int index) const;

    // Is the plugin installed as a QML KCM? (QWidget KCMs open with kcmshell6)
    Q_INVOKABLE static bool available(const QString &module);
    // Name, description and icon from the plugin metadata (localized), without loading it
    Q_INVOKABLE static QVariantMap info(const QString &module);
    Q_INVOKABLE void pop();

Q_SIGNALS:
    void moduleChanged();
    void kcmChanged();
    void errorChanged();
    void depthChanged();

protected:
    void componentComplete() override;

private:
    void reload();
    void unload();

    QString m_module;
    QString m_error;
    QString m_name;
    QString m_description;
    QString m_icon;
    QPointer<KQuickConfigModule> m_kcm;
};
