// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
namespace Plasma {class Containment;}
// Configuration/ID remapping from ShellCorona::clonePanelTo (Plasma 6.7.5).
// The caller assigns edge/output and creates the new view only after copying.
bool copyPanelConfiguration(Plasma::Containment *source,Plasma::Containment *target);
