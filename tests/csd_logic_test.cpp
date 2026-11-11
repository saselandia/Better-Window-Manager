#include "CSDLogic.hpp"
#include <cassert>
#include <array>
#include <iostream>
using namespace BwmCsd;
int main() {
    Input i;assert(!decide(i).bar); // No negotiation: CSD, without any class/title input.
    i.xdg=true;i.applied=Server;assert(decide(i).bar);
    for(uint32_t request:{0u,1u,2u}) {
        assert(desiredXdg(request)==(request==Client?Client:Server));
        i.requested=request;i.applied=desiredXdg(request);assert(decide(i).bar==(request!=Client));
    }
    i.noBar=true;assert(!decide(i).bar);assert(desiredXdg(Client,true)==Server);
    i.noBar=false;i.decorate=false;assert(!decide(i).bar);
    i.decorate=true;i.fullscreen=true;assert(!decide(i).bar);
    i.fullscreen=false;i.applied=0;assert(!decide(i).ready&&!decide(i).bar);
    i.xdg=false;i.kde=true;
    assert(desiredKde(0,false)==Server);assert(desiredKde(0,true)==0);
    assert(desiredKde(Client,true)==Client);assert(desiredKde(Server,true)==Server);
    assert(desiredKde(Client,true,true)==0);i.applied=0;assert(!decide(i).bar);
    i.kde=false;i.x11=true;i.applied=Server;
    assert(decide(i).bar);i.x11Ready=false;assert(!decide(i).bar&&!decide(i).ready);
    i.x11Ready=true;i.gtkFrameExtents=true;assert(!decide(i).bar);
    i.gtkFrameExtents=false;i.motifNoBorder=true;assert(!decide(i).bar);
    i.motifNoBorder=false;i.overrideRedirect=true;assert(!decide(i).bar);
    i.overrideRedirect=false;i.x11Special=true;assert(!decide(i).bar);
    std::array<uint32_t,5> motif{2,0,0,0,0};assert(motifHasNoFrame(motif,32));
    motif[0]=0;assert(!motifHasNoFrame(motif,32));motif[0]=2;motif[2]=1;assert(!motifHasNoFrame(motif,32));
    motif[2]=0;assert(!motifHasNoFrame({motif.data(),2},32));assert(!motifHasNoFrame(motif,8));
    assert(gtkHasFrameHint(true,32,4));assert(!gtkHasFrameHint(true,32,3));assert(!gtkHasFrameHint(false,32,4));assert(!gtkHasFrameHint(true,8,4));
    ModeState initial;initial.deferInitial(Server);initial.deferInitial(Client);
    assert(initial.pending.empty());initial.initialCommit(8);assert(initial.pending.back().second==Client);
    initial.ack(8);initial.commit();assert(initial.applied==Client);
    ModeState s;s.applied=Client;s.configure(10,Server);
    s.commit();assert(s.applied==Client); // No dual bars before ack.
    s.ack(9);s.commit();assert(s.applied==Client);
    s.ack(10);assert(s.applied==Client);s.commit();assert(s.applied==Server);
    s.configure(11,Client);s.ack(12);assert(s.applied==Server);s.commit();assert(s.applied==Client);
    s.configure(20,Server);s.configure(20,Client);s.ack(20);s.commit();assert(s.applied==Client); // coalesced configure
    s.configure(0xfffffff0,Server);s.ack(0xfffffff0);s.commit();assert(s.applied==Server);
    s.configure(2,Client);s.ack(2);s.commit();assert(s.applied==Client);
    for(uint32_t n=100;n<220;n++)s.configure(n,n%2?Client:Server);
    assert(s.pending.size()<=64);s.ack(219);s.commit();assert(s.applied==Client);
    LegacyModeState legacy;
    for(int n=0;n<30;n++){auto mode=n%2?Client:Server;legacy.configure(mode);assert(legacy.waiting);legacy.commit();assert(legacy.applied==mode);}
    std::cout<<"ok policy, X11 properties, ack/commit, legacy toggles, serial wrap\n";
}
