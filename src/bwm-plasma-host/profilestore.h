// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <QString>
#include <QHash>
#include <QJsonObject>
#include <memory>
class QLockFile;
// Complete native files plus BWM output-binding/provenance metadata. The caller
// keeps this lease for the entire native Corona lifetime and flushes/closes native
// owners before checkpointing. Restore always selects a new generation/path.
class ProfileStore {
public:
    explicit ProfileStore(QString root);
    ~ProfileStore();
    static QJsonObject importStage(const QString &stage,const QString &destination);
    // Explicit snapshot recovery also works with a missing/broken current head or
    // generation. Takes the same owner lease; never starts or selects a daily panel.
    static QJsonObject recover(const QString &root,const QString &snapshotId);
    QJsonObject info()const;
    QJsonObject checkpoint();
    QJsonObject restore(const QString &snapshotId);
    QJsonObject exportToState(const QString &name);
    QString layoutFile()const;
    QString viewSettingsFile()const;
    QHash<uint,QString> assignments()const;
private:
    friend class ProfileSelection;
    QString generationDirectory()const;
    void unchangedHead()const;
    QString m_root;
    QJsonObject m_head,m_bindings;
    std::unique_ptr<QLockFile> m_lock;
};

// Persistent intent only: this never installs autostart, hides another panel or
// certifies runtime backends. A consumer retains the returned ProfileStore lease.
class ProfileSelection {
public:
    static QJsonObject info();
    static QJsonObject select(const QString &name,qint64 expectedRevision);
    static QJsonObject clear(qint64 expectedRevision);
    static std::unique_ptr<ProfileStore> openSelected();
private:
    static QJsonObject update(const QString &name,qint64 expectedRevision);
};
