/* SPDX-FileCopyrightText: 2021 Kai Uwe Broulik <kde@broulik.de>
   SPDX-License-Identifier: LGPL-2.1-only OR LGPL-3.0-only OR LicenseRef-KDE-Accepted-LGPL */
// BWM: port of src/qml/listitemmenu.cpp to PC3, because QMenu cannot open from layer-shell.
import QtQuick
import org.kde.plasma.components as PC3
import org.kde.kitemmodels as KItemModels
PC3.Menu {
    id:menu
    enum ItemType { None, Sink, SinkInput, Source, SourceOutput }
    property int itemType:0
    property var pulseObject:null
    property var sourceModel:null
    property var cardModel:null
    property var visualParent:null
    parent:visualParent
    readonly property bool hasContent:entries.length>0
    function openRelative() { popup(); }
    function objects(model) {
        if(!model)return [];
        const result=[],role=model.KItemModels.KRoleNames.role("PulseObject");
        for(let i=0;i<model.rowCount();i++)result.push(model.data(model.index(i,0),role));
        return result.filter(p=>p);
    }
    readonly property var entries: {
        const result=[],obj=pulseObject;
        if(!obj)return result;
        if(itemType===BwmListItemMenu.SinkInput||itemType===BwmListItemMenu.SourceOutput) {
            objects(sourceModel).forEach(d=>result.push({text:d.description,checked:d.index===obj.deviceIndex,run:()=>obj.deviceIndex=d.index}));
        } else {
            if((sourceModel?.count??0)>1)result.push({text:qsTr("Use this device for all streams"),run:()=>obj.switchStreams()});
            const ports=obj.ports??[];
            if(ports.length>1)ports.forEach((p,i)=>result.push({text:p.description,checked:obj.activePortIndex===i,run:()=>obj.activePortIndex=i}));
            const card=objects(cardModel).find(c=>c.index===obj.cardIndex);
            if(card)(card.profiles??[]).forEach((p,i)=>{if(p.name!=="off"&&p.availability!==2)result.push({text:p.description,checked:card.activeProfileIndex===i,run:()=>card.activeProfileIndex=i});});
        }
        return result;
    }
    Repeater {
        model:menu.entries
        PC3.MenuItem { required property var modelData;text:modelData.text;checkable:modelData.checked!==undefined;checked:modelData.checked??false;onTriggered:modelData.run() }
    }
}
