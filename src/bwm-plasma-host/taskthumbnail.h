// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QQuickPaintedItem>
#include <QImage>
#include <QVariantMap>
#include <memory>
class QJsonObject;
class QQmlEngine;
class BwmTaskBridge;
class TaskThumbnail:public QQuickPaintedItem {
    Q_OBJECT
    Q_PROPERTY(QString uuid READ uuid WRITE setUuid NOTIFY uuidChanged)
    Q_PROPERTY(bool ready READ ready NOTIFY readyChanged)
public:
    explicit TaskThumbnail(QQuickItem *parent=nullptr);
    ~TaskThumbnail()override;
    QString uuid()const{return m_uuid;}
    void setUuid(const QString &uuid);
    bool ready()const{return !m_image.isNull();}
    void paint(QPainter *painter)override;
    void acceptFrame(const QImage &image);
    void captureFailed(const QString &reason);
    static bool validBufferSize(quint32 width,quint32 height);
    static QImage::Format pixelFormat(quint32 shmFormat);
    static QImage transformed(const QImage &image,quint32 transform);
Q_SIGNALS:
    void uuidChanged();
    void readyChanged();
private:
    void reconsider();
    void watchWindow(QQuickWindow *window);
    void resetCapture();
    struct State;
    std::unique_ptr<State> m_state;
    QString m_uuid,m_failedIdentity;
    QImage m_image;
};
bool installTaskThumbnails(QQmlEngine *engine,QString *error);
QVariantMap taskThumbnailDiagnostics();
QVariantMap thumbnailCompositorGuardStatus();
bool thumbnailGuardReportMatches(const QJsonObject &report,int expectedPeerPid);
QVariantMap thumbnailGuardIpcStatus(int expectedPeerPid,const QString &runtime);
// Only the private native-test executable calls this. The production entry
// point requires proof from the compositor process serving its Wayland socket.
void allowSyntheticThumbnailFixtureForTest();
