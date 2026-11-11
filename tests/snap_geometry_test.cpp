#include "SnapGeometry.hpp"
#include <cassert>
#include <iostream>
using namespace BwmSnap;
int main(){
    // KWin 6.7.5 checkQuickTilingMaximizationZones, on the maximize area (panel excluded)
    Rect area{-2520,760,2520,1400}; // right edge (x=0) touches another output
    std::vector<Rect> others{{0,0,3840,2160}};
    auto left=edge({-2505,1400},area,others);assert(left&&left->direction=="left"&&!left->inner);
    assert(left->frame.x==-2520&&left->frame.w==1260);
    assert(edge({-1000,762},area,others)->direction=="maximize");
    assert(!edge({-1000,766},area,others));                      // top strip is 5 px
    assert(edge({-2520,2140},area,others)->direction=="bottom-left");
    assert(edge({-2520,1100},area,others)->direction=="top-left"); // 760+1400*.25=1110
    assert(edge({-2520,1120},area,others)->direction=="left");
    assert(!edge({-1200,2159},area,others));                     // bottom edge does nothing
    assert(!edge({-1200,1400},area,others));
    auto right=edge({-5,1400},area,others);assert(right&&right->direction=="right"&&right->inner);
    assert(!edge({-5,1400},area,others,.25,false,true));          // ElectricBorderTiling off
    assert(!edge({-1000,762},area,others,.25,true,false));        // ElectricBorderMaximize off
    assert(edge({-5,770},area,others)->direction=="top-right");   // top of a side edge = quarter
    Rect odd{0,40,1001,601};auto a=tile(odd,"bottom-left"),b=tile(odd,"bottom-right");
    assert(a.w+b.w==1001&&a.h==301&&a.y==340&&b.x==500);
    auto r=magnet({7,300,400,300},{0,0,1000,1000},{},{10,0,0,false});assert(r.x==0&&r.y==300);
    r=magnet({-7,300,400,300},{0,0,1000,1000},{},{10,0,0,true});assert(r.x==0);
    r=magnet({7,300,400,300},{0,0,1000,1000},{},{10,0,0,true});assert(r.x==7);
    r=magnet({301,302,400,400},{0,0,1000,1000},{},{0,0,10,false});assert(r.x==300&&r.y==300);
    r=magnet({301,500,400,400},{0,0,1000,1000},{},{0,0,10,false});assert(r.x==301); // no center on only one axis
    r=magnet({493,101,400,300},{0,0,1600,1000},{{0,100,500,300}},{0,10,0,false});assert(r.x==500&&r.y==100);
    r=magnet({493,700,400,100},{0,0,1600,1000},{{0,100,500,300}},{0,10,0,false});assert(r.x==493); // no snap to unrelated row
    auto n=adjacent({0,0,500,1000},{0,0,600,1000},{500,0,500,1000});assert(n&&n->x==600&&n->w==400);
    n=adjacent({0,0,500,1000},{0,0,600,1000},{504,0,496,1000},8);assert(n&&n->x==604&&n->w==396);
    assert(!adjacent({0,0,500,1000},{0,0,950,1000},{500,0,500,1000}));
    auto p=padded({.5,0,.5,1},{0,40,1001,601},4);assert(p.x==503&&p.w==494&&p.y==44&&p.h==593);
    std::cout<<"ok KWin zones (sides, top, inner edges), logical reserved geometry, quarters, magnets, adjacency, KWin padding\n";
}
