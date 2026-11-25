// SPDX-License-Identifier: GPL-2.0-or-later
// TEST ONLY: input on the runner's private nested compositor, never the daily one.
#pragma once
#include <QString>
#include <cstdint>
struct wl_display;
struct wl_seat;
struct zwp_virtual_keyboard_manager_v1;
struct zwp_virtual_keyboard_v1;
struct zwlr_virtual_pointer_manager_v1;
struct zwlr_virtual_pointer_v1;
class NestedInput {
public:
    ~NestedInput();
    bool open();
    void key(uint32_t code);
    void move(uint32_t x,uint32_t y,uint32_t width,uint32_t height);
    QString error;
private:
    wl_display *display=nullptr;
    wl_seat *seat=nullptr;
    zwp_virtual_keyboard_manager_v1 *keyboards=nullptr;
    zwp_virtual_keyboard_v1 *keyboard=nullptr;
    zwlr_virtual_pointer_manager_v1 *pointers=nullptr;
    zwlr_virtual_pointer_v1 *pointer=nullptr;
    uint32_t timestamp=0;
};
