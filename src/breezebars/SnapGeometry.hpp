#pragma once
// BWM F10: independent geometry implementing KWin quick-tiling / snap-zone policies.
// Reference: KWin v6.7.5 workspace.cpp, tiles/{quicktile,tile}.cpp; no Qt in Hyprland.
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <vector>
namespace BwmSnap {
struct Rect { double x=0,y=0,w=0,h=0; double right()const{return x+w;} double bottom()const{return y+h;} };
struct Point {double x,y;};
struct Target { std::string direction; Rect frame; bool inner=false; };
struct Zones { double border=10,window=10,center=0; bool overlapOnly=false; };
inline bool overlaps(double a,double b,double c,double d){return a<=d&&c<=b;}
inline Rect tile(Rect area,const std::string& direction) {
    double w=std::floor(area.w/2),h=std::floor(area.h/2);
    if(direction=="maximize"||direction=="top")return area;
    Rect result=area;
    if(direction.find("left")!=std::string::npos)result.w=w;
    if(direction.find("right")!=std::string::npos){result.x+=w;result.w=area.w-w;}
    if(direction.find("top-")!=std::string::npos)result.h=h;
    if(direction.find("bottom")!=std::string::npos){result.y+=h;result.h=area.h-h;}
    return result;
}
// KWin 6.7.5 Window::checkQuickTilingMaximizationZones: only the left and right edges of the
// maximize area quick-tile (20 px), the top of each half becomes a quarter by the corner ratio of
// the area height, and the top edge (5 px) maximizes. The bottom edge does nothing. An edge shared
// with another output (`inner`) still tiles, but only after the pointer rests there (250 ms).
inline bool insideAny(Point p,const std::vector<Rect>& rects) {
    for(const auto& r:rects)if(p.x>=r.x&&p.x<r.right()&&p.y>=r.y&&p.y<r.bottom())return true;
    return false;
}
inline std::optional<Target> edge(Point p,Rect area,const std::vector<Rect>& otherOutputs={},double cornerRatio=.25,
                                  bool tiling=true,bool maximize=true) {
    std::string d;bool inner=false;
    if(tiling) {
        if(p.x<=area.x+20){d="left";inner=insideAny({area.x-1,p.y},otherOutputs);}
        else if(p.x>=area.right()-20){d="right";inner=insideAny({area.right()+1,p.y},otherOutputs);}
    }
    if(!d.empty()) {
        const double c=std::clamp(cornerRatio,0.,.5)*area.h;
        if(p.y<=area.y+c)d="top-"+d;
        else if(p.y>=area.bottom()-c)d="bottom-"+d;
    } else if(maximize&&p.y<=area.y+5) {
        d="maximize";inner=insideAny({p.x,area.y-1},otherOutputs);
    } else return {};
    return Target{d,tile(area,d),inner};
}
inline Rect magnet(Rect frame,Rect area,const std::vector<Rect>& others,Zones zones) {
    auto result=frame;double dx=1e30,dy=1e30;
    auto x=[&](double target,double zone,bool allowed=true){double delta=std::abs(target-frame.x);if(allowed&&zone>0&&delta<zone&&delta<dx){result.x=target;dx=delta;}};
    auto y=[&](double target,double zone,bool allowed=true){double delta=std::abs(target-frame.y);if(allowed&&zone>0&&delta<zone&&delta<dy){result.y=target;dy=delta;}};
    x(area.x,zones.border,!zones.overlapOnly||frame.x<area.x);
    x(area.right()-frame.w,zones.border,!zones.overlapOnly||frame.right()>area.right());
    y(area.y,zones.border,!zones.overlapOnly||frame.y<area.y);
    y(area.bottom()-frame.h,zones.border,!zones.overlapOnly||frame.bottom()>area.bottom());
    for(auto& other:others) {
        if(overlaps(frame.y,frame.bottom(),other.y,other.bottom())) {
            x(other.right(),zones.window,!zones.overlapOnly||frame.x<other.right());
            x(other.x-frame.w,zones.window,!zones.overlapOnly||frame.right()>other.x);
        }
        if(overlaps(frame.x,frame.right(),other.x,other.right())) {
            y(other.bottom(),zones.window,!zones.overlapOnly||frame.y<other.bottom());
            y(other.y-frame.h,zones.window,!zones.overlapOnly||frame.bottom()>other.y);
        }
        // Align adjacent corners once one axis has snapped, as workspace.cpp does.
        if(std::abs(result.x-other.right())<.1||std::abs(result.right()-other.x)<.1){y(other.y,zones.window);y(other.bottom()-frame.h,zones.window);}
        if(std::abs(result.y-other.bottom())<.1||std::abs(result.bottom()-other.y)<.1){x(other.x,zones.window);x(other.right()-frame.w,zones.window);}
    }
    // KWin center snapping requires the whole center to be close, or the other axis at a border.
    double cx=area.x+(area.w-frame.w)/2,cy=area.y+(area.h-frame.h)/2;
    bool nearX=std::abs(cx-frame.x)<zones.center,nearY=std::abs(cy-frame.y)<zones.center;
    bool borderX=result.x==area.x||result.right()==area.right();
    bool borderY=result.y==area.y||result.bottom()==area.bottom();
    if(nearX&&(nearY||borderY))x(cx,zones.center);
    if(nearY&&(nearX||borderX))y(cy,zones.center);
    return result;
}
inline Rect padded(Rect normalized,Rect area,double padding) {
    double l=normalized.x>0?padding/2:padding,t=normalized.y>0?padding/2:padding;
    double r=normalized.right()<1?padding/2:padding,b=normalized.bottom()<1?padding/2:padding;
    // Round shared boundaries first: odd dimensions cannot leave uncovered pixels.
    double x=std::round(area.x+normalized.x*area.w),y=std::round(area.y+normalized.y*area.h);
    double right=std::round(area.x+normalized.right()*area.w),bottom=std::round(area.y+normalized.bottom()*area.h);
    return {x+l,y+t,std::max(1.,right-x-l-r),std::max(1.,bottom-y-t-b)};
}
// Resize neighbours sharing the moved boundary, leaving their far edge fixed.
inline std::optional<Rect> adjacent(Rect before,Rect after,Rect neighbour,double tolerance=2) {
    auto n=neighbour;bool changed=false;
    if(overlaps(before.y,before.bottom(),n.y,n.bottom())) {
        if(std::abs(before.right()-n.x)<=tolerance&&std::abs(after.right()-before.right())>.1){double gap=n.x-before.right();double end=n.right();n.x=after.right()+gap;n.w=end-n.x;changed=true;}
        else if(std::abs(before.x-n.right())<=tolerance&&std::abs(after.x-before.x)>.1){n.w=after.x-(before.x-n.right())-n.x;changed=true;}
    }
    if(overlaps(before.x,before.right(),neighbour.x,neighbour.right())) {
        if(std::abs(before.bottom()-n.y)<=tolerance&&std::abs(after.bottom()-before.bottom())>.1){double gap=n.y-before.bottom();double end=n.bottom();n.y=after.bottom()+gap;n.h=end-n.y;changed=true;}
        else if(std::abs(before.y-n.bottom())<=tolerance&&std::abs(after.y-before.y)>.1){n.h=after.y-(before.y-n.bottom())-n.y;changed=true;}
    }
    if(!changed||n.w<100||n.h<60)return {};
    return n;
}
}
