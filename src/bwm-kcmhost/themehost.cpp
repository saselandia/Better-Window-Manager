// SPDX-License-Identifier: GPL-2.0-or-later
#include "themehost.h"
#include <QQmlComponent>
#include <QQmlContext>
#include <KLocalizedQmlContext>
ThemeHost::~ThemeHost(){clear();}
void ThemeHost::clear(){delete m_item;m_item=nullptr;m_engine.reset();}
void ThemeHost::setSource(const QUrl &s){if(s==m_source)return;m_source=s;emit sourceChanged();if(isComponentComplete())reload();}
void ThemeHost::setContextProperties(const QVariantMap &p){if(p==m_properties)return;m_properties=p;emit sourceChanged();
    if(m_engine && m_item){
        for(auto i=p.cbegin();i!=p.cend();++i){
            m_engine->rootContext()->setContextProperty(i.key(),i.value());
            if(m_item->metaObject()->indexOfProperty(i.key().toUtf8())>=0)m_item->setProperty(i.key().toUtf8(),i.value());
        }
    } else if(isComponentComplete())reload();}
void ThemeHost::componentComplete(){QQuickItem::componentComplete();reload();}
void ThemeHost::geometryChange(const QRectF &a,const QRectF &b){QQuickItem::geometryChange(a,b);if(m_item)m_item->setSize(a.size());}
void ThemeHost::reload(){
    clear();m_error.clear();
    if(!m_source.isEmpty()){
        m_engine=std::make_unique<QQmlEngine>();
        if(auto *outer=qmlEngine(this))m_engine->setImportPathList(outer->importPathList());
        m_engine->rootContext()->setContextObject(new KLocalizedQmlContext(m_engine.get()));
        connect(m_engine.get(),&QQmlEngine::quit,this,&ThemeHost::quitRequested);
        for(auto i=m_properties.cbegin();i!=m_properties.cend();++i)m_engine->rootContext()->setContextProperty(i.key(),i.value());
        QQmlComponent component(m_engine.get(),m_source,QQmlComponent::PreferSynchronous);
        QObject *object=component.beginCreate(m_engine->rootContext());
        if(object){
            QVariantMap initial;
            for(auto i=m_properties.cbegin();i!=m_properties.cend();++i)
                if(object->metaObject()->indexOfProperty(i.key().toUtf8())>=0)initial.insert(i.key(),i.value());
            component.setInitialProperties(object,initial);
            component.completeCreate();
            m_item=qobject_cast<QQuickItem*>(object);
            if(m_item && !component.isError()){m_item->setParent(this);m_item->setParentItem(this);m_item->setSize(size());}
            else {delete object;m_item=nullptr;}
        }
        if(!m_item)m_error=component.errorString().isEmpty()?QStringLiteral("Theme root must be an Item"):component.errorString();
    }
    emit statusChanged();
}
