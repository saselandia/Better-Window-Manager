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
    QJsonObject info()const;
    QJsonObject checkpoint();
    QJsonObject restore(const QString &snapshotId);
    QJsonObject exportToState(const QString &name);
    QString layoutFile()const;
    QString viewSettingsFile()const;
    QHash<uint,QString> assignments()const;
private:
    QString generationDirectory()const;
    void unchangedHead()const;
    QString m_root;
    QJsonObject m_head,m_bindings;
    std::unique_ptr<QLockFile> m_lock;
};
