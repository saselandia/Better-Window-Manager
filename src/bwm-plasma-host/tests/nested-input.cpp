// SPDX-License-Identifier: GPL-2.0-or-later
#include "nested-input.h"
#include "test-virtual-keyboard-client.h"
#include "test-virtual-pointer-client.h"
#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <wayland-client.h>
#include <sys/socket.h>
#include <sys/mman.h>
#include <unistd.h>
#include <cstring>
#include <xkbcommon/xkbcommon.h>

NestedInput::~NestedInput() {
    if(keymap)xkb_keymap_unref(keymap);
    if(!display)return;
    if(keyboard)zwp_virtual_keyboard_v1_destroy(keyboard);
    if(pointer)zwlr_virtual_pointer_v1_destroy(pointer);
    wl_display_flush(display);wl_display_disconnect(display);
}
bool NestedInput::open(const QString &layout) {
    const QString config=qEnvironmentVariable("BWM_FOCUS_CONFIG");
    bool pidOk=false;const int expected=qEnvironmentVariableIntValue("BWM_FOCUS_COMPOSITOR_PID",&pidOk);
    if(qEnvironmentVariable("BWM_FOCUS_NESTED")!="1" || !pidOk || expected<=0 ||
       !QFileInfo(config).canonicalFilePath().startsWith(QDir::tempPath()+"/bwm-focus-safety-")) {
        error="Missing private nested-compositor identity";return false;
    }
    display=wl_display_connect(nullptr);
    if(!display){error="Cannot connect to private Wayland display";return false;}
    ucred peer{};socklen_t size=sizeof(peer);
    if(getsockopt(wl_display_get_fd(display),SOL_SOCKET,SO_PEERCRED,&peer,&size)!=0 || peer.uid!=getuid() || peer.pid!=expected) {
        error="Wayland peer does not match the disposable compositor";return false;
    }
    QFile args(QString("/proc/%1/cmdline").arg(peer.pid));
    if(!args.open(QIODevice::ReadOnly)){error="Cannot verify compositor command";return false;}
    const auto command=args.readAll().split('\0');const int option=command.indexOf("--config");
    if(option<0 || command.value(option+1)!=config.toUtf8()) {
        error="Peer is not using the private test configuration";return false;
    }
    auto *registry=wl_display_get_registry(display);
    static const wl_registry_listener listener={
        [](void *data,wl_registry *r,uint32_t id,const char *name,uint32_t){
            auto *self=static_cast<NestedInput*>(data);
            if(std::strcmp(name,"wl_seat")==0) {
                self->seat=static_cast<wl_seat*>(wl_registry_bind(r,id,&wl_seat_interface,1));
                static const wl_seat_listener ignore={[](void*,wl_seat*,uint32_t){},[](void*,wl_seat*,const char*){}};
                wl_seat_add_listener(self->seat,&ignore,nullptr);
            } else if(std::strcmp(name,"zwp_virtual_keyboard_manager_v1")==0)
                self->keyboards=static_cast<zwp_virtual_keyboard_manager_v1*>(wl_registry_bind(r,id,&zwp_virtual_keyboard_manager_v1_interface,1));
            else if(std::strcmp(name,"zwlr_virtual_pointer_manager_v1")==0)
                self->pointers=static_cast<zwlr_virtual_pointer_manager_v1*>(wl_registry_bind(r,id,&zwlr_virtual_pointer_manager_v1_interface,1));
        },[](void*,wl_registry*,uint32_t){}
    };
    wl_registry_add_listener(registry,&listener,this);
    if(wl_display_roundtrip(display)<0 || !seat || !keyboards || !pointers) {
        error="Private compositor lacks input protocols";return false;
    }
    // A deliberately tiny keymap: only 'a' and Escape. Parsed by the compositor;
    // no client-side key delivery or QTest::keyClick bypasses the Wayland seat.
    const char keymap[]=R"(xkb_keymap {
        xkb_keycodes "fixture" { minimum=8; maximum=255; <AC01>=38; <ESC>=9; };
        xkb_types "fixture" { type "ONE_LEVEL" { modifiers=None; level_name[Level1]="Any"; }; };
        xkb_compatibility "fixture" {};
        xkb_symbols "fixture" { key <AC01> { [ a ] }; key <ESC> { [ Escape ] }; };
    };)";
    QByteArray map(keymap,sizeof(keymap));
    if(!layout.isEmpty()) {
        if(layout!="us" && layout!="es"){error="Unsupported fixture layout";return false;}
        auto *context=xkb_context_new(XKB_CONTEXT_NO_FLAGS);
        const auto name=layout.toUtf8();xkb_rule_names names{};names.layout=name.constData();
        this->keymap=xkb_keymap_new_from_names(context,&names,XKB_KEYMAP_COMPILE_NO_FLAGS);
        xkb_context_unref(context);
        if(!this->keymap){error="Cannot compile fixture layout";return false;}
        char *text=xkb_keymap_get_as_string(this->keymap,XKB_KEYMAP_FORMAT_TEXT_V1);
        map=QByteArray(text,int(std::strlen(text)+1));free(text);
    }
    const int fd=memfd_create("bwm-test-keymap",MFD_CLOEXEC);
    if(fd<0){error="Cannot allocate fixture keymap";return false;}
    const bool written=write(fd,map.constData(),map.size())==map.size();
    if(!written){close(fd);error="Cannot write fixture keymap";return false;}
    keyboard=zwp_virtual_keyboard_manager_v1_create_virtual_keyboard(keyboards,seat);
    zwp_virtual_keyboard_v1_keymap(keyboard,WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1,fd,map.size());
    close(fd);
    pointer=zwlr_virtual_pointer_manager_v1_create_virtual_pointer(pointers,seat);
    if(wl_display_roundtrip(display)<0){error="Input fixture setup failed";return false;}
    return true;
}
bool NestedInput::shortcut(const QString &symbol,bool shift) {
    if(!keymap)return false;
    const auto wanted=xkb_keysym_from_name(symbol.toUtf8().constData(),XKB_KEYSYM_NO_FLAGS);
    xkb_keycode_t found=0;
    for(auto code=xkb_keymap_min_keycode(keymap);code<=xkb_keymap_max_keycode(keymap);++code) {
        const xkb_keysym_t *syms=nullptr;
        const int count=xkb_keymap_key_get_syms_by_level(keymap,code,0,shift?1:0,&syms);
        if(count==1 && syms[0]==wanted){found=code;break;}
    }
    if(found<8)return false;
    const auto logo=xkb_keymap_mod_get_index(keymap,XKB_MOD_NAME_LOGO);
    const auto shifted=xkb_keymap_mod_get_index(keymap,XKB_MOD_NAME_SHIFT);
    zwp_virtual_keyboard_v1_key(keyboard,++timestamp,125,WL_KEYBOARD_KEY_STATE_PRESSED);
    if(shift)zwp_virtual_keyboard_v1_key(keyboard,++timestamp,42,WL_KEYBOARD_KEY_STATE_PRESSED);
    zwp_virtual_keyboard_v1_modifiers(keyboard,(1u<<logo)|(shift?(1u<<shifted):0),0,0,0);
    key(found-8);
    if(shift)zwp_virtual_keyboard_v1_key(keyboard,++timestamp,42,WL_KEYBOARD_KEY_STATE_RELEASED);
    zwp_virtual_keyboard_v1_key(keyboard,++timestamp,125,WL_KEYBOARD_KEY_STATE_RELEASED);
    zwp_virtual_keyboard_v1_modifiers(keyboard,0,0,0,0);wl_display_roundtrip(display);
    return true;
}
void NestedInput::key(uint32_t code) {
    zwp_virtual_keyboard_v1_key(keyboard,++timestamp,code,WL_KEYBOARD_KEY_STATE_PRESSED);
    zwp_virtual_keyboard_v1_key(keyboard,++timestamp,code,WL_KEYBOARD_KEY_STATE_RELEASED);
    wl_display_roundtrip(display);
}
void NestedInput::move(uint32_t x,uint32_t y,uint32_t width,uint32_t height) {
    zwlr_virtual_pointer_v1_motion_absolute(pointer,++timestamp,x,y,width,height);
    zwlr_virtual_pointer_v1_frame(pointer);wl_display_roundtrip(display);
}
