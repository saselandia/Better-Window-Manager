// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <string>
struct wl_display;
void createThumbnailTestGlobals(wl_display *display);
bool thumbnailTestCommand(const std::string &command);
