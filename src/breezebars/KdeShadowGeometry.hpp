/*
 * SPDX-FileCopyrightText: 2021 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
 * SPDX-FileCopyrightText: 2026 BWM contributors
 * SPDX-License-Identifier: GPL-2.0-or-later
 * Adapted from KWin 6.7.5 scene/shadowitem.cpp::buildQuads. Native eight-tile
 * protocol shadows, including absent borders, asymmetric tiles and fractional seams.
 */
#pragma once
#include "DecoWire.hpp"
#include <algorithm>
namespace BwmKde {
using BwmDeco::SRectD;
using BwmDeco::SExtents;
struct Size { double w=0,h=0; };
struct Quad {size_t tile;SRectD src,dst;};
inline std::vector<Quad> tileQuads(const SRectD &frame,const SExtents &offset,const std::array<Size,8> &sizes) {
    if(frame.w<5 || frame.h<5)return {};
    const auto &[t,tr,r,br,b,bl,l,tl]=sizes;
    const double ml=std::max({tl.w,l.w,bl.w}),mt=std::max({tl.h,t.h,tr.h}),
                 mr=std::max({tr.w,r.w,br.w}),mb=std::max({br.h,b.h,bl.h});
    const SRectD outer{frame.x-offset.left,frame.y-offset.top,frame.w+offset.left+offset.right,frame.h+offset.top+offset.bottom};
    auto corner=[](double x,double y,Size s,double ex,double ey){return s.w>0 && s.h>0 ? std::array<double,4>{x,y,x+s.w,y+s.h}:std::array<double,4>{ex,ey,ex,ey};};
    auto TL=corner(outer.x,outer.y,tl,outer.x+ml,outer.y+mt);
    auto TR=corner(outer.x+outer.w-tr.w,outer.y,tr,outer.x+outer.w-mr,outer.y+mt);
    auto BR=corner(outer.x+outer.w-br.w,outer.y+outer.h-br.h,br,outer.x+outer.w-mr,outer.y+outer.h-mb);
    auto BL=corner(outer.x,outer.y+outer.h-bl.h,bl,outer.x+ml,outer.y+outer.h-mb);
    auto split=[](auto &a,auto &b,int axis){if(a[axis+2]>b[axis]){double end=std::min(a[axis+2],b[axis+2]),start=std::max(a[axis],b[axis]);a[axis+2]=b[axis]=(end+start)/2;}};
    split(TL,TR,0);split(BL,BR,0);split(TL,BL,1);split(TR,BR,1);
    std::vector<Quad> result;
    auto rect=[](const auto &a){return SRectD{a[0],a[1],a[2]-a[0],a[3]-a[1]};};
    auto append=[&](size_t i,const auto &a,bool right,bool bottom,bool side=false){
        const auto dst=rect(a);const auto s=sizes[i];
        if(dst.w<=0 || dst.h<=0 || s.w<=0 || s.h<=0)return;
        const bool horizontal=i==0 || i==4;
        SRectD src{right?s.w-dst.w:0,bottom?s.h-dst.h:0,side && horizontal?s.w:dst.w,side && !horizontal?s.h:dst.h};
        result.push_back({i,src,dst});
    };
    append(7,TL,false,false);append(1,TR,true,false);append(3,BR,true,true);append(5,BL,false,true);
    std::array<double,4> T{TL[2],outer.y,TR[0],outer.y+t.h},R{outer.x+outer.w-r.w,TR[3],outer.x+outer.w,BR[1]},
        B{BL[2],outer.y+outer.h-b.h,BR[0],outer.y+outer.h},L{outer.x,TL[3],outer.x+l.w,BL[1]};
    split(L,R,0);split(T,B,1);
    append(0,T,false,false,true);append(2,R,true,false,true);append(4,B,false,true,true);append(6,L,false,false,true);
    return result;
}
}
