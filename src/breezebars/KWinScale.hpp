// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

// R7: normal-window scale effect. Preserve native Hyprland timelines and implement
// KWin's interrupted-opening close policy before the snapshot is taken.
void initKWinScale();
void finishKWinScale();
