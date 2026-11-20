// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: GPL-2.0-or-later
// The oracle body is read verbatim from the selected KWin release by check-r6-shadows.py.
#include "DecoLogic.hpp"
#include "ShadowBuffer.hpp"
#include "shadowstate.h"
#include <QCoreApplication>
#include <QFile>
#include <QImage>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMarginsF>
#include <QPainter>
#include <QRectF>
#include <QSizeF>
#include <cassert>
#include <fcntl.h>
#include <iostream>
#include <limits>
#include <sys/mman.h>

namespace KWin {
using RectF = QRectF;
struct WindowVertex { double x, y, u, v; };
using WindowQuad = std::array<WindowVertex, 4>;
using WindowQuadList = QList<WindowQuad>;
struct Window { double w, h; double width() const {return w;} double height() const {return h;} };
struct Shadow {
    enum ShadowElements { ShadowElementTop, ShadowElementTopRight, ShadowElementRight,
        ShadowElementBottomRight, ShadowElementBottom, ShadowElementBottomLeft, ShadowElementLeft, ShadowElementTopLeft };
    KDecoration3::DecorationShadow deco;
    QSizeF elementSize(ShadowElements e) const {
        switch (e) {
        case ShadowElementTop: return deco.topGeometry().size();
        case ShadowElementTopRight: return deco.topRightGeometry().size();
        case ShadowElementRight: return deco.rightGeometry().size();
        case ShadowElementBottomRight: return deco.bottomRightGeometry().size();
        case ShadowElementBottom: return deco.bottomGeometry().size();
        case ShadowElementBottomLeft: return deco.bottomLeftGeometry().size();
        case ShadowElementLeft: return deco.leftGeometry().size();
        default: return deco.topLeftGeometry().size();
        }
    }
};
struct ShadowItem {
    Window* m_window;
    Shadow* m_shadow;
    RectF outer;
    RectF rect() const {return outer;}
    WindowQuadList buildQuads() const;
};
#include "kwin-shadow-reference.inc"
}

using namespace BwmDeco;
static bool near(double a, double b) {return std::abs(a-b)<1e-8;}
static QRectF rect(const SRectD& r) {return {r.x,r.y,r.w,r.h};}

static QJsonObject compare(const SShadow& s, const QImage& image, const SRectD& frame, double scale) {
    KWin::Window window{frame.w,frame.h};
    KWin::Shadow shadow;
    shadow.deco.setShadow(image);
    shadow.deco.setInnerShadowRect(rect(s.inner));
    shadow.deco.setPadding({s.padding.left,s.padding.top,s.padding.right,s.padding.bottom});
    QRectF outer(frame.x-s.padding.left,frame.y-s.padding.top,frame.w+s.padding.left+s.padding.right,
        frame.h+s.padding.top+s.padding.bottom);
    KWin::ShadowItem item{&window,&shadow,outer};
    const auto expected = item.buildQuads();
    const auto actual = shadowQuads(frame,s);
    assert(expected.size()==static_cast<qsizetype>(actual.size()));
    for (size_t i=0;i<actual.size();++i) {
        const auto& e=expected[i]; const auto& a=actual[i];
        assert(near(a.dst.x,e[0].x) && near(a.dst.y,e[0].y));
        assert(near(a.dst.w,e[2].x-e[0].x) && near(a.dst.h,e[2].y-e[0].y));
        assert(near(a.src.x,e[0].u) && near(a.src.y,e[0].v));
        assert(near(a.src.w,e[2].u-e[0].u) && near(a.src.h,e[2].v-e[0].v));
    }
    QSize size(std::ceil(outer.width()*scale)+4,std::ceil(outer.height()*scale)+4);
    QImage a(size,QImage::Format_ARGB32_Premultiplied), b(size,QImage::Format_ARGB32_Premultiplied);
    a.fill(Qt::transparent); b.fill(Qt::transparent);
    QImage source=image; source.setDevicePixelRatio(1); // KWin's raw image coordinates.
    {
        QPainter pa(&a), pb(&b);
        for (auto* painter : {&pa,&pb}) {
            painter->setRenderHint(QPainter::SmoothPixmapTransform);
            painter->translate(2-outer.x()*scale,2-outer.y()*scale); painter->scale(scale,scale);
        }
        for (const auto& q : actual) pa.drawImage(rect(q.dst),source,rect(q.src));
        for (const auto& q : expected) pb.drawImage(QRectF(QPointF(q[0].x,q[0].y),QPointF(q[2].x,q[2].y)),source,
            QRectF(QPointF(q[0].u,q[0].v),QPointF(q[2].u,q[2].v)));
    }
    int maxAlpha=0, maxColor=0;
    for (int y=0;y<a.height();++y) for (int x=0;x<a.width();++x) {
        const auto aa=a.pixel(x,y), bb=b.pixel(x,y);
        maxAlpha=std::max(maxAlpha,std::abs(qAlpha(aa)-qAlpha(bb)));
        maxColor=std::max({maxColor,std::abs(qRed(aa)-qRed(bb)),std::abs(qGreen(aa)-qGreen(bb)),std::abs(qBlue(aa)-qBlue(bb))});
    }
    assert(maxAlpha==0 && maxColor==0);
    return {{"quads",int(actual.size())},{"scale",scale},{"maxAlphaError",maxAlpha},{"maxColorError",maxColor}};
}

static void stateAndBuffers() {
    ShadowState state;
    int changes=0; state.changed=[&] {++changes;};
    auto first=std::make_unique<KDecoration3::DecorationShadow>();
    KDecoration3::DecorationShadow second;
    state.follow(first.get()); state.sent();
    first->setPadding({1,2,3,4}); assert(state.pending()); state.sent();
    first->setInnerShadowRect({4,5,1,1}); assert(state.pending()); state.sent();
    QImage image(16,16,QImage::Format_ARGB32_Premultiplied); image.fill(QColor(100,50,10,90));
    first->setShadow(image); assert(state.pending()); state.sent();
    state.follow(&second); state.sent();
    int previous=changes;
    first->setPadding({2,3,4,5}); assert(!state.pending() && changes==previous);
    first.reset(); assert(!state.pending()); // disconnected former owner
    state.follow(nullptr); assert(state.pending()); state.sent();
    auto dying=std::make_unique<KDecoration3::DecorationShadow>();
    state.follow(dying.get()); state.sent(); dying.reset(); assert(state.pending());

    SShadow s; s.width=s.height=16; s.stride=64; s.inner={4,4,1,1};
    const int fd=memfd_create("r6-shadow-test",MFD_CLOEXEC);
    assert(fd>=0 && ftruncate(fd,1024)==0);
    assert(pwrite(fd,image.constBits(),1024,0)==1024);
    const auto pixels=readShadowPixels(s,fd); assert(pixels && pixels->size()==1024);
    assert(std::memcmp(pixels->data(),image.constBits(),1024)==0);
    assert(ftruncate(fd,1)==0 && !readShadowPixels(s,fd));
    close(fd); assert(!readShadowPixels(s,fd));
    for (int field=0;field<6;++field) {
        auto bad=s;
        if (field==0) bad.dpr=std::numeric_limits<double>::quiet_NaN();
        if (field==1) bad.inner.w=std::numeric_limits<double>::infinity();
        if (field==2) bad.padding.left=std::numeric_limits<double>::quiet_NaN();
        if (field==3) bad.stride=UINT32_MAX;
        if (field==4) bad.inner={15,15,2,2};
        if (field==5) bad.height=0;
        assert(!shadowIsSane(bad,1024)); assert(shadowQuads({0,0,100,100},bad).empty());
    }
}

int main(int argc,char** argv) {
    QCoreApplication app(argc,argv);
    stateAndBuffers();
    QJsonArray cases;
    // Odd fractional overlaps, fully contained asymmetric corners, zero-sized edges,
    // tiny windows and image DPR independent of output scale.
    for (auto inner : {SRectD{16.5,17.5,1,1},SRectD{30,2,1,1},SRectD{0,2,1,1}})
    for (auto frame : {SRectD{10.25,20.5,800,528},SRectD{10.25,20.5,17.5,11.25},SRectD{0,0,5,5},SRectD{0,0,4,40}})
    for (double dpr : {1.,1.25,1.5,2.}) for (double scale : {1.,1.25,1.5,2.}) {
        SShadow s; s.width=37; s.height=39; s.stride=37*4; s.inner=inner; s.dpr=dpr; s.padding={3,4,5,6};
        QImage image(s.width,s.height,QImage::Format_ARGB32_Premultiplied); image.setDevicePixelRatio(dpr);
        for (int y=0;y<image.height();++y) for (int x=0;x<image.width();++x)
            image.setPixel(x,y,qPremultiply(qRgba(100,50,10,(x*3+y*5)%256)));
        cases.append(compare(s,image,frame,scale));
    }
    QJsonArray samples;
    if (argc>1) {
        QFile file(QString::fromLocal8Bit(argv[1])); assert(file.open(QIODevice::ReadOnly));
        for (const auto& value : QJsonDocument::fromJson(file.readAll()).array()) {
            auto v=value.toObject(); auto sizes=v["size"].toArray(), pad=v["padding"].toArray(), in=v["inner"].toArray();
            SShadow s; s.width=sizes[0].toInt(); s.height=sizes[1].toInt(); s.stride=v["stride"].toInt(); s.dpr=v["dpr"].toDouble();
            s.padding={pad[0].toDouble(),pad[1].toDouble(),pad[2].toDouble(),pad[3].toDouble()};
            s.inner={in[0].toDouble(),in[1].toDouble(),in[2].toDouble(),in[3].toDouble()};
            const auto bytes=QByteArray::fromBase64(v["pixels"].toString().toLatin1());
            assert(shadowIsSane(s,bytes.size()));
            QImage image(reinterpret_cast<const uchar*>(bytes.constData()),s.width,s.height,s.stride,QImage::Format_ARGB32_Premultiplied);
            auto result=compare(s,image,{0,0,180,125},v["scale"].toDouble());
            result["name"]=v["name"]; samples.append(result);
        }
    }
    std::cout << QJsonDocument(QJsonObject{{"syntheticCases",cases.size()},{"nativeSamples",samples},
        {"maxAlphaError",0},{"maxColorError",0},{"mutableShadowAndShortBuffer",true}}).toJson().constData();
}
