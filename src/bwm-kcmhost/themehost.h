// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QQuickItem>
#include <QQmlEngine>
#include <QVariantMap>
#include <memory>
// Native KDE theme QML runs in its own engine: Qt.quit() cannot terminate BWM's shell.
class ThemeHost : public QQuickItem {
    Q_OBJECT
    Q_PROPERTY(QUrl source READ source WRITE setSource NOTIFY sourceChanged)
    Q_PROPERTY(QVariantMap contextProperties READ contextProperties WRITE setContextProperties NOTIFY sourceChanged)
    Q_PROPERTY(QString error READ error NOTIFY statusChanged)
    Q_PROPERTY(bool ready READ ready NOTIFY statusChanged)
public:
    ThemeHost(QQuickItem *parent=nullptr):QQuickItem(parent){}
    ~ThemeHost() override;
    QUrl source() const {return m_source;}
    QVariantMap contextProperties() const {return m_properties;}
    QString error() const {return m_error;}
    bool ready() const {return m_item;}
    void setSource(const QUrl &source);
    void setContextProperties(const QVariantMap &properties);
signals:
    void sourceChanged();
    void statusChanged();
    void quitRequested();
protected:
    void componentComplete() override;
    void geometryChange(const QRectF &a,const QRectF &b) override;
private:
    void reload();
    void clear();
    QUrl m_source;
    QVariantMap m_properties;
    QString m_error;
    QQuickItem *m_item=nullptr;
    std::unique_ptr<QQmlEngine> m_engine;
};
class LockAuthenticatorTypes : public QObject {
    Q_OBJECT
public:
    enum Type {Fingerprint=1,Smartcard=2};
    Q_ENUM(Type)
};
