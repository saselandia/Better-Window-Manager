/*
 * SPDX-FileCopyrightText: 2026 BWM contributors
 * SPDX-FileCopyrightText: 2026 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
 * SPDX-License-Identifier: GPL-2.0-or-later
 * org_kde_kwin_shadow_manager v2: installed KDE clients supply their original
 * eight premultiplied tiles. No theme, Gaussian approximation or second CSD bar.
 */
#include <algorithm>
#include <array>
#include <map>
#include <set>
#include <memory>
#include <vector>
#include <optional>
#include <ranges>
#include <functional>
#include <sstream>
#include <fstream>
#include <iostream>
#include <any>
#include <filesystem>
#include <regex>
#include <chrono>
#include <mutex>
#include <span>
#include <expected>
#define private public
#include <hyprland/src/render/pass/Pass.hpp>
#undef private
#include <hyprland/src/render/pass/SurfacePassElement.hpp>
#include <hyprland/src/render/Renderer.hpp>
#include <hyprland/src/render/OpenGL.hpp>
#include <hyprland/src/Compositor.hpp>
#include <hyprland/src/output/Monitor.hpp>
#include <hyprland/src/protocols/core/Compositor.hpp>
#include <hyprland/src/protocols/core/Shm.hpp>
#include <hyprland/src/desktop/view/Window.hpp>
#include <hyprland/src/desktop/view/WLSurface.hpp>
#include <hyprland/src/desktop/state/WindowState.hpp>
#include <hyprland/src/managers/fullscreen/FullscreenController.hpp>
#include <hyprland/src/desktop/rule/windowRule/WindowRuleApplicator.hpp>
#include <hyprland/src/plugins/HookSystem.hpp>
#include <hyprland/src/debug/HyprCtl.hpp>
#include <hyprland/src/xwayland/XWayland.hpp>
#include <drm_fourcc.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>
#include "globals.hpp"
#include "barDeco.hpp"
#include "KdeShadow.hpp"
#include "KdeShadowGeometry.hpp"
#include "KdeShadowPixels.hpp"
#include "kde-shadow-server.h"
using namespace Render::GL;

namespace {
constexpr const char *PASS="CBwmKdeShadowPass";
constexpr size_t MAX_BYTES=32*1024*1024;
struct Tile {
    int width=0,height=0;std::vector<uint8_t> pixels;SP<Render::ITexture> texture;
};
struct Image {
    std::array<std::shared_ptr<Tile>,8> tiles;BwmDeco::SExtents offset;
    std::shared_ptr<Tile> atlas;
    std::array<Vector2D,8> origins;
};
struct Record;
struct Node {
    WP<CWLSurfaceResource> surface;
    std::weak_ptr<Record> proposed,appliedRecord;
    std::shared_ptr<Image> image;
    std::optional<CBox> lastBox;
    CHyprSignalListener stateCommit,destroy;
};
struct Record {
    wl_resource *resource=nullptr;
    std::weak_ptr<Node> node;
    std::array<WP<IHLBuffer>,8> buffers,pending;
    uint8_t changed=0;
    BwmDeco::SExtents offset,nextOffset;
    bool offsetChanged=false;
    std::shared_ptr<Image> image;
};
struct Queued {
    WP<SSurfaceState> state;std::weak_ptr<Node> node;std::weak_ptr<Record> record;
};
class Server;
std::unique_ptr<Server> server;
CFunctionHook *commitHook=nullptr;
using Commit=void(*)(CWLSurfaceResource*,SSurfaceState&);

std::shared_ptr<Tile> copyTile(WP<IHLBuffer> buffer) {
    auto hold=buffer.lock();if(!hold)return {};
    auto *shm=dynamic_cast<CWLSHMBuffer*>(hold.get());
    if(!shm || !shm->m_pool)return {};
    const int width=hold->size.x,height=hold->size.y,stride=shm->m_stride;
    const uint32_t format=shm->shm().format; // m_fmt stores wl_shm enums (ARGB=0), not DRM fourcc.
    if(format!=DRM_FORMAT_ARGB8888 && format!=DRM_FORMAT_XRGB8888)return {};
    auto pixels=BwmKde::readTile(shm->m_pool->m_fd.get(),width,height,stride,shm->m_offset,shm->m_pool->m_size);
    if(!pixels)return {};
    auto tile=std::make_shared<Tile>();tile->width=width;tile->height=height;tile->pixels=std::move(*pixels);
    if(format==DRM_FORMAT_XRGB8888)for(size_t i=3;i<tile->pixels.size();i+=4)tile->pixels[i]=255;
    return tile;
}
void damage(const std::shared_ptr<Node> &node) {
    if(node->lastBox && g_pHyprRenderer)g_pHyprRenderer->damageBox(*node->lastBox);
}
bool packAtlas(Image &image) {
    // NinePatchOpenGL::create, KWin 6.7.5 scene/opengl/ninepatch.cpp.
    std::array<Vector2D,8> s;for(size_t i=0;i<8;++i)if(auto tile=image.tiles[i])s[i]={double(tile->width),double(tile->height)};
    const int left=std::max({s[7].x,s[6].x,s[5].x}),top=std::max({s[7].y,s[0].y,s[1].y});
    const int width=left+std::max(s[0].x,s[4].x)+std::max({s[1].x,s[2].x,s[3].x});
    const int height=top+std::max(s[6].y,s[2].y)+std::max({s[3].y,s[4].y,s[5].y});
    if(width<=0 || height<=0)return true;
    if(uint64_t(width)*height*4>MAX_BYTES)return false;
    image.origins=std::array<Vector2D,8>{Vector2D{double(left),0.0},Vector2D{width-s[1].x,0.0},Vector2D{width-s[2].x,double(top)},
        Vector2D{width-s[3].x,height-s[3].y},Vector2D{double(left),height-s[4].y},Vector2D{0.0,height-s[5].y},Vector2D{0.0,double(top)},Vector2D{0,0}};
    image.atlas=std::make_shared<Tile>();image.atlas->width=width;image.atlas->height=height;
    image.atlas->pixels.resize(size_t(width)*height*4);
    for(size_t i=0;i<8;++i)if(auto tile=image.tiles[i])for(int y=0;y<tile->height;++y)
        std::memcpy(image.atlas->pixels.data()+((size_t(image.origins[i].y)+y)*width+size_t(image.origins[i].x))*4,
            tile->pixels.data()+size_t(y)*tile->width*4,size_t(tile->width)*4);
    return true;
}
class Server {
public:
    wl_global *global=nullptr;
    std::set<wl_resource*> managers;
    std::map<wl_resource*,std::shared_ptr<Record>> records;
    std::map<CWLSurfaceResource*,std::shared_ptr<Node>> nodes;
    std::map<SSurfaceState*,Queued> queued;
    bool enabled=false;
    SP<SHyprCtlCommand> diagnostics;
    Server(){
        global=wl_global_create(g_pCompositor->m_wlDisplay,&org_kde_kwin_shadow_manager_interface,2,this,bind);
        if(!global)throw std::runtime_error("Cannot create native KDE shadow global");
        diagnostics=HyprlandAPI::registerHyprCtlCommand(PHANDLE,SHyprCtlCommand{.name="breezebars-shadows",.exact=true,.fn=[this](eHyprCtlOutputFormat,std::string){
            size_t applied=0,states=0;for(const auto &[surface,node]:nodes)if(node->image)++applied;
            for(const auto &[state,value]:queued)if(value.state)++states;
            std::string display;
            if(const char *value=std::getenv("DISPLAY");g_pXWayland && g_pXWayland->enabled() && value && std::regex_match(value,std::regex(":\\d+")))display=value;
            return std::format("{{\"version\":1,\"waylandProtocolVersion\":2,\"surfaces\":{},\"objects\":{},\"applied\":{},\"queued\":{},\"shm\":true,\"dmabuf\":false,\"x11Hints\":false,\"xwaylandDisplay\":\"{}\"}}",nodes.size(),records.size(),applied,states,display);
        }});
    }
    ~Server(){
        if(diagnostics)HyprlandAPI::unregisterHyprCtlCommand(PHANDLE,diagnostics);
        wl_global_destroy(global);
        while(!records.empty())wl_resource_destroy(records.begin()->first);
        while(!managers.empty())wl_resource_destroy(*managers.begin());
        queued.clear();nodes.clear();
    }
    static void destroy(wl_client*,wl_resource *r){wl_resource_destroy(r);}
    static void bind(wl_client *client,void *data,uint32_t version,uint32_t id){
        auto *self=static_cast<Server*>(data);auto *r=wl_resource_create(client,&org_kde_kwin_shadow_manager_interface,std::min(version,2u),id);
        if(!r){wl_client_post_no_memory(client);return;}
        static const struct org_kde_kwin_shadow_manager_interface impl{create,unset,destroy};
        self->managers.insert(r);wl_resource_set_implementation(r,&impl,self,[](wl_resource *r){static_cast<Server*>(wl_resource_get_user_data(r))->managers.erase(r);});
    }
    std::shared_ptr<Node> node(wl_resource *resource){
        auto surface=CWLSurfaceResource::fromResource(resource);if(!surface)return {};
        if(auto it=nodes.find(surface.get());it!=nodes.end())return it->second;
        auto n=std::make_shared<Node>();n->surface=surface;nodes[surface.get()]=n;
        n->stateCommit=surface->m_events.stateCommit.listen([this,weak=std::weak_ptr<Node>(n)](WP<SSurfaceState> state){
            // SurfaceStateQueue owns states with UniquePtr. Its weak reference
            // must be observed directly; lock() aborts for unique owners.
            auto n=weak.lock();auto s=state;if(!n || !s)return;
            std::erase_if(queued,[](const auto &entry){return !entry.second.state;});
            // KWin queues the shadow OBJECT, not a copy of its tile state. Its
            // separate shadow.commit can arrive while the surface waits on a
            // fence; read that object's committed tiles when the state latches.
            auto r=n->proposed.lock();queued[s.get()]={state,n,r};
        });
        n->destroy=surface->m_events.destroy.listen([this,key=surface.get()]{
            auto it=nodes.find(key);if(it!=nodes.end()){
                damage(it->second);
                std::erase_if(queued,[&](const auto &entry){return entry.second.node.lock()==it->second;});nodes.erase(it);
            }
        });
        return n;
    }
    static void create(wl_client *client,wl_resource *manager,uint32_t id,wl_resource *surface){
        auto *self=static_cast<Server*>(wl_resource_get_user_data(manager));auto n=self->node(surface);if(!n){wl_resource_post_error(manager,0,"Invalid surface");return;}
        auto *r=wl_resource_create(client,&org_kde_kwin_shadow_interface,wl_resource_get_version(manager),id);if(!r){wl_client_post_no_memory(client);return;}
        auto record=std::make_shared<Record>();record->resource=r;record->node=n;n->proposed=record;self->records[r]=record;
        static const struct org_kde_kwin_shadow_interface impl{
            commit,attach<6>,attach<7>,attach<0>,attach<1>,attach<2>,attach<3>,attach<4>,attach<5>,
            offset<0>,offset<1>,offset<2>,offset<3>,destroy};
        wl_resource_set_implementation(r,&impl,record.get(),[](wl_resource *resource){
            auto *record=static_cast<Record*>(wl_resource_get_user_data(resource));
            if(auto n=record->node.lock()){
                if(n->proposed.lock().get()==record)n->proposed.reset();
                if(n->appliedRecord.lock().get()==record){damage(n);n->image.reset();n->appliedRecord.reset();}
            }
            if(server)server->records.erase(resource);
        });
    }
    static void unset(wl_client*,wl_resource *manager,wl_resource *surface){
        auto *self=static_cast<Server*>(wl_resource_get_user_data(manager));if(auto n=self->node(surface))n->proposed.reset();
    }
    template<size_t N>static void attach(wl_client*,wl_resource *r,wl_resource *buffer){
        auto *record=static_cast<Record*>(wl_resource_get_user_data(r));auto b=CWLBufferResource::fromResource(buffer);
        record->pending[N]=b?b->m_buffer:WP<IHLBuffer>{};record->changed |= uint8_t(1u<<N);
    }
    template<size_t N>static void offset(wl_client*,wl_resource *r,wl_fixed_t value){
        auto *record=static_cast<Record*>(wl_resource_get_user_data(r));
        if(!record->offsetChanged)record->nextOffset=record->offset;
        double *fields[]={&record->nextOffset.left,&record->nextOffset.top,&record->nextOffset.right,&record->nextOffset.bottom};
        *fields[N]=std::clamp(wl_fixed_to_double(value),-4096.0,4096.0);record->offsetChanged=true;
    }
    static void commit(wl_client*,wl_resource *r){
        auto *record=static_cast<Record*>(wl_resource_get_user_data(r));
        auto image=std::make_shared<Image>();image->offset=record->offsetChanged?record->nextOffset:record->offset;
        size_t total=0;
        for(size_t i=0;i<8;++i){
            if(record->changed & (1u<<i))record->buffers[i]=record->pending[i];
            image->tiles[i]=record->image && !(record->changed & (1u<<i))?record->image->tiles[i]:copyTile(record->buffers[i]);
            if(image->tiles[i])total+=image->tiles[i]->pixels.size();
            if(total>MAX_BYTES){image.reset();break;}
        }
        if(image && !packAtlas(*image))image.reset();
        record->offset=image?image->offset:record->offset;record->image=image;record->changed=0;record->offsetChanged=false;
    }
    void apply(CWLSurfaceResource *surface,SSurfaceState &state){
        auto it=nodes.find(surface);if(it==nodes.end())return;
        auto n=it->second;std::shared_ptr<Record> record;std::shared_ptr<Image> image;
        auto q=queued.find(&state);
        if(q!=queued.end() && q->second.state){record=q->second.record.lock();image=record?record->image:nullptr;queued.erase(q);}
        else {record=n->proposed.lock();image=record?record->image:nullptr;}
        if(!record)image.reset();
        if(n->image!=image){damage(n);n->image=image;n->appliedRecord=record;}
    }
};
void commitSurface(CWLSurfaceResource *surface,SSurfaceState &state){
    // Match the compositor's actual latched state, not the arrival of a request:
    // dmabuf acquire fences / FIFO can delay commits. Null-buffer commits bypass its queue.
    if(server && !(!state.updated.all && surface->m_mapped && state.fifoScheduled))server->apply(surface,state);
    reinterpret_cast<Commit>(commitHook->m_original)(surface,state);
}
class ShadowPass final:public IPassElement {
public:
    ShadowPass(std::shared_ptr<Image> image,std::vector<BwmKde::Quad> quads,PHLMONITOR monitor,float alpha,CBox box)
        :image(std::move(image)),quads(std::move(quads)),monitor(monitor),alpha(alpha),box(box){}
    bool needsLiveBlur()override{return false;}bool needsPrecomputeBlur()override{return false;}
    const char *passName()override{return PASS;}ePassElementType type()override{return EK_CUSTOM;}
    std::optional<CBox> boundingBox()override{return box;}
    std::vector<UP<IPassElement>> draw()override{
        auto m=monitor.lock();if(!m)return {};
        auto tile=image->atlas;if(!tile)return {};
        if(!tile->texture)tile->texture=g_pHyprRenderer->createTexture(DRM_FORMAT_ARGB8888,tile->pixels.data(),tile->width*4,{double(tile->width),double(tile->height)});
        if(!tile->texture)return {};
        const auto &offset=image->offset;
        const double originX=std::round((box.x+offset.left)*m->m_scale)+std::round(-offset.left*m->m_scale);
        const double originY=std::round((box.y+offset.top)*m->m_scale)+std::round(-offset.top*m->m_scale);
        for(const auto &quad:quads){
            // KWin snaps item translation and LOCAL quad vertices separately.
            // Share the rounded endpoint at a fractional corner seam.
            const double x1=originX+std::round((quad.dst.x-box.x)*m->m_scale),y1=originY+std::round((quad.dst.y-box.y)*m->m_scale);
            const double x2=originX+std::round((quad.dst.x+quad.dst.w-box.x)*m->m_scale),y2=originY+std::round((quad.dst.y+quad.dst.h-box.y)*m->m_scale);
            CBox dst{x1,y1,x2-x1,y2-y1};if(dst.w<=0 || dst.h<=0)continue;
            const auto source=image->origins[quad.tile];
            CHyprOpenGLImpl::STextureRenderData data;data.a=alpha;data.allowCustomUV=true;
            data.primarySurfaceUVTopLeft={(source.x+quad.src.x)/tile->width,(source.y+quad.src.y)/tile->height};
            data.primarySurfaceUVBottomRight={(source.x+quad.src.x+quad.src.w)/tile->width,(source.y+quad.src.y+quad.src.h)/tile->height};
            g_pHyprOpenGL->renderTexture(tile->texture,dst,data);
        }return {};
    }
private:
    std::shared_ptr<Image> image;std::vector<BwmKde::Quad> quads;PHLMONITORREF monitor;float alpha;CBox box;
};
}
void initKdeShadows(){
    auto symbol=dlsym(RTLD_DEFAULT,"_ZN18CWLSurfaceResource11commitStateER13SSurfaceState");
    if(!symbol)throw std::runtime_error("breezebars: KDE shadows require the checked surface commit ABI");
    commitHook=HyprlandAPI::createFunctionHook(PHANDLE,symbol,reinterpret_cast<void*>(&commitSurface));
    if(!commitHook || !commitHook->hook())throw std::runtime_error("breezebars: cannot attach KDE shadow commit hook");
    try{server=std::make_unique<Server>();}catch(...){HyprlandAPI::removeFunctionHook(PHANDLE,commitHook);commitHook=nullptr;throw;}
}
void finishKdeShadows(){
    if(g_pHyprRenderer)g_pHyprRenderer->m_renderPass.removeAllOfType(PASS);
    // Destroy every resource while callbacks/code are still resident; no hot unload is supported.
    if(server){auto *p=server.get();while(!p->records.empty())wl_resource_destroy(p->records.begin()->first);server.reset();}
    if(commitHook)HyprlandAPI::removeFunctionHook(PHANDLE,commitHook);commitHook=nullptr;
}
void insertKdeShadows(){
    if(!server || !g_pGlobalState || !g_pHyprRenderer)return;
    const bool enabled=g_pGlobalState->config.enabled->value();
    if(server->enabled!=enabled){for(const auto &[surface,node]:server->nodes){damage(node);node->lastBox.reset();}server->enabled=enabled;}
    if(!enabled)return;
    auto &elements=g_pHyprRenderer->m_renderPass.m_passElements;
    std::vector<std::pair<size_t,UP<IPassElement>>> inserts;
    for(size_t i=0;i<elements.size();++i){
        const auto &element=elements[i].element;
        if(!element || element->type()!=EK_SURFACE || std::string_view(element->passName())!="CSurfacePassElement")continue;
        auto *surface=static_cast<CSurfacePassElement*>(element.get());const auto &d=surface->m_data;
        if(!d.surface || !d.pMonitor)continue;
        auto it=server->nodes.find(d.surface.get());if(it==server->nodes.end() || !it->second->image)continue;
        if(d.pWindow && !d.popup){
            if(d.pWindow->m_ruleApplicator->noShadow().valueOrDefault() || Fullscreen::controller()->isFullscreen(d.pWindow))continue;
            bool decorated=false;for(const auto &bar:g_pGlobalState->bars)if(bar && bar->getOwner()==d.pWindow && bar->remoteActive()){decorated=true;break;}
            if(decorated)continue; // KWin prioritizes KDecoration over the client's protocol shadow.
        }
        auto node=it->second;auto image=node->image;auto monitor=d.pMonitor.lock();if(!monitor)continue;
        // SurfacePassElement boxes, like pass bounding boxes, are monitor-local
        // logical coordinates. Apply the output scale exactly once, in draw().
        const auto tex=surface->getTexBox();
        const BwmDeco::SRectD frame{tex.x,tex.y,tex.w,tex.h};
        std::array<BwmKde::Size,8> sizes;for(size_t n=0;n<8;++n)if(auto tile=image->tiles[n])sizes[n]={double(tile->width),double(tile->height)};
        auto quads=BwmKde::tileQuads(frame,image->offset,sizes);if(quads.empty())continue;
        const auto &p=image->offset;CBox box{frame.x-p.left,frame.y-p.top,frame.w+p.left+p.right,frame.h+p.top+p.bottom};
        const auto global=CBox{box}.translate(monitor->m_position);
        if(!node->lastBox || *node->lastBox!=global){damage(node);node->lastBox=global;damage(node);}
        auto view=Desktop::View::CWLSurface::fromResource(d.surface);
        // KWin's alpha-modifier belongs to SurfaceItemWayland, not its sibling
        // ShadowItem. Compositor window/fade opacity still affects the shadow.
        const float opacity=d.alpha*d.fadeAlpha*(view ? view->m_overallOpacity : 1.F);
        inserts.emplace_back(i,makeUnique<ShadowPass>(image,std::move(quads),monitor,opacity,box));
    }
    for(auto it=inserts.rbegin();it!=inserts.rend();++it)elements.insert(elements.begin()+it->first,Render::CRenderPass::SPassElementData{.element=std::move(it->second)});
}
