// SPDX-License-Identifier: GPL-2.0-or-later
// TEST ONLY: synthetic pixels, stable foreign handles, never a session service.
#include "thumbnail-server.h"
#include "thumbnail-foreign-server.h"
#include "thumbnail-mapping-server.h"
#include "thumbnail-source-server.h"
#include "thumbnail-copy-server.h"
#include <wayland-server.h>
#include <vector>
#include <algorithm>
#include <cstdint>
namespace {
void destroy(wl_client *,wl_resource *r){wl_resource_destroy(r);}
struct Foreign {wl_resource *resource;bool closed=false;};
struct Frame {wl_resource *buffer=nullptr;};
std::vector<wl_resource*> lists,sessions;
std::vector<Foreign*> handles;
wl_global *captureGlobal=nullptr;
bool staticPixels=false;
int pixelWidth=64,pixelHeight=48;
std::vector<wl_resource*> waiting;
void foreign(wl_resource *list){
    auto *resource=wl_resource_create(wl_resource_get_client(list),&ext_foreign_toplevel_handle_v1_interface,1,0);
    auto *data=new Foreign{resource};handles.push_back(data);
    static const struct ext_foreign_toplevel_handle_v1_interface implementation={destroy};
    wl_resource_set_implementation(resource,&implementation,data,[](wl_resource *r){auto *f=static_cast<Foreign*>(wl_resource_get_user_data(r));std::erase(handles,f);delete f;});
    ext_foreign_toplevel_list_v1_send_toplevel(list,resource);
    ext_foreign_toplevel_handle_v1_send_identifier(resource,"own-fixture-window");
    ext_foreign_toplevel_handle_v1_send_title(resource,"Own synthetic frame");
    ext_foreign_toplevel_handle_v1_send_app_id(resource,"org.bwm.thumbnail.fixture");
    ext_foreign_toplevel_handle_v1_send_done(resource);
}
void bindList(wl_client *client,void *,uint32_t,uint32_t id){
    auto *resource=wl_resource_create(client,&ext_foreign_toplevel_list_v1_interface,1,id);lists.push_back(resource);
    static const struct ext_foreign_toplevel_list_v1_interface implementation={[](wl_client *,wl_resource *r){ext_foreign_toplevel_list_v1_send_finished(r);},destroy};
    wl_resource_set_implementation(resource,&implementation,nullptr,[](wl_resource *r){std::erase(lists,r);});foreign(resource);
}
void map(wl_client *client,wl_resource *,uint32_t id,wl_resource *handle){
    auto *resource=wl_resource_create(client,&hyprland_toplevel_window_mapping_handle_v1_interface,1,id);
    static const struct hyprland_toplevel_window_mapping_handle_v1_interface implementation={destroy};
    wl_resource_set_implementation(resource,&implementation,nullptr,nullptr);
    auto *data=static_cast<Foreign*>(wl_resource_get_user_data(handle));
    if(data && !data->closed)hyprland_toplevel_window_mapping_handle_v1_send_window_address(resource,0,0xabc);
    else hyprland_toplevel_window_mapping_handle_v1_send_failed(resource);
}
void bindMapping(wl_client *client,void *,uint32_t,uint32_t id){
    auto *resource=wl_resource_create(client,&hyprland_toplevel_mapping_manager_v1_interface,1,id);
    static const struct hyprland_toplevel_mapping_manager_v1_interface implementation={map,[](wl_client *,wl_resource *r,uint32_t,wl_resource *){wl_resource_post_error(r,0,"WLR mapping not used by this fixture");},destroy};
    wl_resource_set_implementation(resource,&implementation,nullptr,nullptr);
}
void source(wl_client *client,wl_resource *,uint32_t id,wl_resource *handle){
    auto *resource=wl_resource_create(client,&ext_image_capture_source_v1_interface,1,id);
    static const struct ext_image_capture_source_v1_interface implementation={destroy};
    wl_resource_set_implementation(resource,&implementation,wl_resource_get_user_data(handle),nullptr);
}
void bindSource(wl_client *client,void *,uint32_t,uint32_t id){
    auto *resource=wl_resource_create(client,&ext_foreign_toplevel_image_capture_source_manager_v1_interface,1,id);
    static const struct ext_foreign_toplevel_image_capture_source_manager_v1_interface implementation={source,destroy};
    wl_resource_set_implementation(resource,&implementation,nullptr,nullptr);
}
void capture(wl_client *,wl_resource *resource){
    if(staticPixels){waiting.push_back(resource);return;}
    auto *frame=static_cast<Frame*>(wl_resource_get_user_data(resource));
    auto *buffer=frame?wl_shm_buffer_get(frame->buffer):nullptr;
    if(!buffer || wl_shm_buffer_get_width(buffer)!=pixelWidth || wl_shm_buffer_get_height(buffer)!=pixelHeight){ext_image_copy_capture_frame_v1_send_failed(resource,EXT_IMAGE_COPY_CAPTURE_FRAME_V1_FAILURE_REASON_BUFFER_CONSTRAINTS);return;}
    wl_shm_buffer_begin_access(buffer);auto *pixels=static_cast<uint8_t*>(wl_shm_buffer_get_data(buffer));
    const auto stride=wl_shm_buffer_get_stride(buffer);
    for(int y=0;y<pixelHeight;++y){auto *row=reinterpret_cast<uint32_t*>(pixels+y*stride);for(int x=0;x<pixelWidth;++x)row[x]=0xff3684c9;}
    wl_shm_buffer_end_access(buffer);
    ext_image_copy_capture_frame_v1_send_transform(resource,WL_OUTPUT_TRANSFORM_NORMAL);
    ext_image_copy_capture_frame_v1_send_damage(resource,0,0,pixelWidth,pixelHeight);
    ext_image_copy_capture_frame_v1_send_presentation_time(resource,0,1,0);
    ext_image_copy_capture_frame_v1_send_ready(resource);wl_buffer_send_release(frame->buffer);
}
void frame(wl_client *client,wl_resource *,uint32_t id){
    auto *resource=wl_resource_create(client,&ext_image_copy_capture_frame_v1_interface,1,id);
    auto *data=new Frame;
    static const struct ext_image_copy_capture_frame_v1_interface implementation={destroy,
        [](wl_client *,wl_resource *r,wl_resource *buffer){static_cast<Frame*>(wl_resource_get_user_data(r))->buffer=buffer;},
        [](wl_client *,wl_resource *,int32_t,int32_t,int32_t,int32_t){},capture};
    wl_resource_set_implementation(resource,&implementation,data,[](wl_resource *r){std::erase(waiting,r);delete static_cast<Frame*>(wl_resource_get_user_data(r));});
}
void session(wl_client *client,wl_resource *,uint32_t id,wl_resource *,uint32_t options){
    auto *resource=wl_resource_create(client,&ext_image_copy_capture_session_v1_interface,1,id);sessions.push_back(resource);
    static const struct ext_image_copy_capture_session_v1_interface implementation={frame,destroy};
    wl_resource_set_implementation(resource,&implementation,nullptr,[](wl_resource *r){std::erase(sessions,r);});
    if(options!=0){wl_resource_post_error(resource,0,"The fixture expects cursor-free window capture");return;}
    ext_image_copy_capture_session_v1_send_shm_format(resource,WL_SHM_FORMAT_ARGB8888);
    ext_image_copy_capture_session_v1_send_buffer_size(resource,pixelWidth,pixelHeight);
    ext_image_copy_capture_session_v1_send_done(resource);
}
void bindCopy(wl_client *client,void *,uint32_t,uint32_t id){
    auto *resource=wl_resource_create(client,&ext_image_copy_capture_manager_v1_interface,1,id);
    static const struct ext_image_copy_capture_manager_v1_interface implementation={session,
        [](wl_client *,wl_resource *r,uint32_t,wl_resource *,wl_resource *){wl_resource_post_error(r,0,"No cursor sessions in this fixture");},destroy};
    wl_resource_set_implementation(resource,&implementation,nullptr,nullptr);
}
}
void createThumbnailTestGlobals(wl_display *display){
    wl_global_create(display,&ext_foreign_toplevel_list_v1_interface,1,nullptr,bindList);
    wl_global_create(display,&hyprland_toplevel_mapping_manager_v1_interface,1,nullptr,bindMapping);
    wl_global_create(display,&ext_foreign_toplevel_image_capture_source_manager_v1_interface,1,nullptr,bindSource);
    captureGlobal=wl_global_create(display,&ext_image_copy_capture_manager_v1_interface,1,nullptr,bindCopy);
}
bool thumbnailTestCommand(const std::string &command){
    if(command=="thumbnail-static"){staticPixels=true;return true;}
    if(command=="thumbnail-live"){
        staticPixels=false;const auto pending=waiting;waiting.clear();for(auto *r:pending)capture(nullptr,r);return true;
    }
    if(command=="thumbnail-resize"){
        pixelWidth=96;pixelHeight=64;
        for(auto *r:sessions){
            ext_image_copy_capture_session_v1_send_shm_format(r,WL_SHM_FORMAT_ARGB8888);
            ext_image_copy_capture_session_v1_send_buffer_size(r,pixelWidth,pixelHeight);
            ext_image_copy_capture_session_v1_send_done(r);
        }
        return true;
    }
    if(command=="thumbnail-close"){
        for(auto *f:handles)if(!f->closed){f->closed=true;ext_foreign_toplevel_handle_v1_send_closed(f->resource);}
        return true;
    }
    if(command=="thumbnail-withdraw"){
        if(captureGlobal){wl_global_remove(captureGlobal);captureGlobal=nullptr;}
        return true;
    }
    return false;
}
