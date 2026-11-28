// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QJsonArray>
#include <QJsonObject>
#include <QList>
#include <QObject>
#include <QPointer>
#include <QVariantList>

class QQuickView;
class QScreen;

class OverviewHost : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString mode READ mode NOTIFY stateChanged)
    Q_PROPERTY(bool active READ isActive NOTIFY stateChanged)
    Q_PROPERTY(int activeWorkspaceId READ activeWorkspaceId NOTIFY stateChanged)
    Q_PROPERTY(bool magicOpen READ magicOpen NOTIFY stateChanged)
    Q_PROPERTY(QVariantList windows READ windows NOTIFY stateChanged)
    Q_PROPERTY(QVariantList workspaces READ workspaces NOTIFY stateChanged)
    Q_PROPERTY(QString searchText READ searchText WRITE setSearchText NOTIFY searchTextChanged)
public:
    struct Snapshot {
        int activeWorkspaceId = 1;
        bool magicOpen = false;
        QString activeMonitorName;
        QVariantList windows;
        QVariantList workspaces;
    };

    explicit OverviewHost(QString windowHelper, QString minimizeHelper, QObject *parent = nullptr);
    ~OverviewHost() override;

    bool isActive() const { return !m_views.isEmpty(); }
    QString mode() const { return m_mode; }
    int activeWorkspaceId() const { return m_snapshot.activeWorkspaceId; }
    bool magicOpen() const { return m_snapshot.magicOpen; }
    QVariantList windows() const { return m_snapshot.windows; }
    QVariantList workspaces() const { return m_snapshot.workspaces; }
    QString searchText() const { return m_searchText; }
    void setSearchText(const QString &text);

    bool toggle(const QString &mode = QStringLiteral("overview"));
    bool open(const QString &mode = QStringLiteral("overview"));
    Q_INVOKABLE void close();
    Q_INVOKABLE void refresh();

    Q_INVOKABLE QVariantList windowsFor(const QString &monitorName, int workspaceId, bool allWorkspaces, bool includeMinimized) const;
    Q_INVOKABLE void activateWindow(const QString &address, int workspaceId, bool minimized, bool special);
    Q_INVOKABLE void closeWindow(const QString &address);
    Q_INVOKABLE void moveWindowToWorkspace(const QString &address, int workspaceId);
    Q_INVOKABLE void switchToWorkspace(int workspaceId);
    Q_INVOKABLE void addWorkspace();
    Q_INVOKABLE void setMode(const QString &mode);

    QJsonObject status() const;

    // Pure snapshot parser exposed for CTest regression tests.
    static Snapshot parseSnapshot(const QJsonArray &clients,
                                  const QJsonArray &workspaces,
                                  const QJsonArray &monitors,
                                  const QJsonObject &activeWorkspace,
                                  const std::function<QString(const QString &)> &uuidLookup = {});

Q_SIGNALS:
    void stateChanged();
    void searchTextChanged();
    void closed();

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    Snapshot captureLiveSnapshot() const;
    bool runHyprctlDispatch(const QStringList &args) const;
    static QString normalizeMode(const QString &mode);
    static QString resolveIconName(const QString &appClass);

    QString m_windowHelper;
    QString m_minimizeHelper;
    QString m_mode = QStringLiteral("overview");
    QString m_searchText;
    QString m_error;
    Snapshot m_snapshot;
    QList<QPointer<QQuickView>> m_views;
    bool m_qmlTypesRegistered = false;
};
