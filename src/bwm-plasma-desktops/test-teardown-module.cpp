// SPDX-License-Identifier: GPL-2.0-or-later
// TEST ONLY. A dlopen/dlclose fixture, not a Hyprland plugin or installed server.
#include "provider.h"
extern "C" __attribute__((visibility("default"))) void *bwm_test_provider_create(wl_display *display){
    auto *provider=new BwmPlasma::DesktopProvider(display,{});
    if(!provider->publish({{{"1","One",{"output-A"}},{"2","Two",{"output-B"}}},"1",1})){
        delete provider;return nullptr;
    }
    provider->setAvailable(true);return provider;
}
extern "C" __attribute__((visibility("default"))) void bwm_test_provider_retire(void *provider){
    static_cast<BwmPlasma::DesktopProvider*>(provider)->setAvailable(false);
}
extern "C" __attribute__((visibility("default"))) void bwm_test_provider_destroy(void *provider){
    delete static_cast<BwmPlasma::DesktopProvider*>(provider);
}
