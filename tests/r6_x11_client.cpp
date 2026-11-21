// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: BSD-3-Clause
// Synthetic X11 hints, not a claim that real GTK CSD pixels were tested.
#include <xcb/xcb.h>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unistd.h>
int main(int argc,char **argv) {
    const char *display=getenv("DISPLAY"),*expected=getenv("BWM_R6_X11_DISPLAY");
    const char *root=getenv("XDG_CONFIG_HOME");
    if(!display || !expected || strcmp(display,expected) || !root || std::string(root).find("/tmp/bwm-r6-nested-")!=0 || argc!=2)return 2;
    auto *c=xcb_connect(display,nullptr);if(xcb_connection_has_error(c))return 3;
    auto *s=xcb_setup_roots_iterator(xcb_get_setup(c)).data;auto w=xcb_generate_id(c);
    const uint32_t values[]={0x707070,XCB_EVENT_MASK_EXPOSURE};
    xcb_create_window(c,XCB_COPY_FROM_PARENT,w,s->root,220,180,500,300,0,XCB_WINDOW_CLASS_INPUT_OUTPUT,s->root_visual,XCB_CW_BACK_PIXEL|XCB_CW_EVENT_MASK,values);
    auto atom=[&](const char *name){auto *r=xcb_intern_atom_reply(c,xcb_intern_atom(c,0,strlen(name),name),nullptr);auto a=r?r->atom:0;free(r);return a;};
    const char cls[]="bwm-r6-window\0bwm-r6-window\0";
    xcb_change_property(c,XCB_PROP_MODE_REPLACE,w,XCB_ATOM_WM_CLASS,XCB_ATOM_STRING,8,sizeof(cls)-1,cls);
    const char title[]="BWM R6 X11 fixture";
    xcb_change_property(c,XCB_PROP_MODE_REPLACE,w,XCB_ATOM_WM_NAME,XCB_ATOM_STRING,8,sizeof(title)-1,title);
    const uint32_t pid=getpid();xcb_change_property(c,XCB_PROP_MODE_REPLACE,w,atom("_NET_WM_PID"),XCB_ATOM_CARDINAL,32,1,&pid);
    if(std::string(argv[1])=="gtk") {const uint32_t extents[]={8,8,28,8};xcb_change_property(c,XCB_PROP_MODE_REPLACE,w,atom("_GTK_FRAME_EXTENTS"),XCB_ATOM_CARDINAL,32,4,extents);}
    else if(std::string(argv[1])=="motif") {const uint32_t hints[]={2,0,0,0,0};const auto a=atom("_MOTIF_WM_HINTS");xcb_change_property(c,XCB_PROP_MODE_REPLACE,w,a,a,32,5,hints);}
    else if(std::string(argv[1])!="ssd")return 4;
    xcb_map_window(c,w);xcb_flush(c);
    while(auto *event=xcb_wait_for_event(c))free(event);
    xcb_disconnect(c);return 0;
}
