cmake_minimum_required(VERSION 3.25)
project(bwm-plasma-host VERSION 0.1 LANGUAGES C CXX) # C: generated Wayland protocol code
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_AUTOMOC ON)
find_package(Qt6 REQUIRED COMPONENTS Widgets Quick DBus)
find_package(Plasma 6.7.5 EXACT REQUIRED)
find_package(PlasmaQuick REQUIRED)
find_package(KF6Package REQUIRED)
find_package(KF6CoreAddons REQUIRED)
find_package(KF6Config REQUIRED)
find_package(KF6NewStuff REQUIRED)
find_package(KF6Svg REQUIRED)
find_package(KF6Service REQUIRED)
find_package(KF6KIO REQUIRED)
find_package(KF6I18n REQUIRED) # CurrentContainmentActionsModel (plasma-workspace 6.7.5).
find_package(KF6WindowSystem 6.29.0 EXACT REQUIRED) # Process-local private V5 adapter ABI.
find_package(LibTaskManager 6.7.5 EXACT REQUIRED)
find_package(LayerShellQt 6.7.5 REQUIRED)
# hyprland_focus_grab_v1: closes Dialogs on outside clicks under Hyprland (focusgrab.cpp).
find_package(Qt6 REQUIRED COMPONENTS WaylandClient WaylandClientPrivate GuiPrivate)
find_package(PkgConfig REQUIRED)
pkg_check_modules(WAYLAND_CLIENT REQUIRED IMPORTED_TARGET wayland-client)
pkg_get_variable(HYPRLAND_PROTOCOLS_DIR hyprland-protocols pkgdatadir)
pkg_get_variable(WAYLAND_PROTOCOLS_DIR wayland-protocols pkgdatadir)
find_program(WAYLAND_SCANNER wayland-scanner REQUIRED)
if(NOT EXISTS "${WAYLAND_PROTOCOLS_DIR}/staging/ext-image-copy-capture/ext-image-copy-capture-v1.xml")
    message(FATAL_ERROR "wayland-protocols with ext-image-copy-capture-v1.xml is required")
endif()
if(NOT HYPRLAND_PROTOCOLS_DIR)
    message(FATAL_ERROR "hyprland-protocols (pkg-config) is required for hyprland-focus-grab-v1.xml")
endif()
add_library(bwm-plasma-configuration STATIC configurationsession.cpp catalog.cpp surfaces.cpp migration.cpp panelprobe.cpp panelsession.cpp themeinventory.cpp packagewindows.cpp viewcorona.cpp focusgrab.cpp panelviewhost.cpp panelconfigview.cpp widgetexplorerview.cpp panelviewsettings.cpp outputidentity.cpp panelruntime.cpp runtimecontrol.cpp profilestore.cpp kns.cpp)
target_sources(bwm-plasma-configuration PRIVATE tasksource.cpp taskbridge.cpp taskpreview.cpp previewappearance.cpp nativedesktopcontrol.cpp desktopregistry.cpp taskmenupolicy.cpp)
target_sources(bwm-plasma-configuration PRIVATE taskthumbnail.cpp tasklauncher.cpp launchrouter.cpp desktopsessioncheck.cpp)
target_sources(bwm-plasma-configuration PRIVATE panelclone.cpp alternativeshelper.cpp desktopviewhost.cpp containmentconfigview.cpp currentcontainmentactionsmodel.cpp layouttemplate.cpp)
target_sources(bwm-plasma-configuration PRIVATE containmentmanagement.cpp)
target_sources(bwm-plasma-configuration PRIVATE panelshadows.cpp)
target_compile_definitions(bwm-plasma-configuration PRIVATE BWM_TASK_THUMBNAIL_QML="${CMAKE_CURRENT_SOURCE_DIR}/qml/TaskThumbnail.qml"
    BWM_WIDGET_EXPLORER_HOST_QML="${CMAKE_CURRENT_SOURCE_DIR}/qml/WidgetExplorerHost.qml")
target_include_directories(bwm-plasma-configuration PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
add_library(bwm-thumbnail-protocols STATIC)
target_link_libraries(bwm-plasma-configuration PUBLIC bwm-thumbnail-protocols)
target_link_libraries(bwm-plasma-configuration PRIVATE Qt6::WaylandClientPrivate)
foreach(PROTOCOL foreign mapping source copy wlr)
    if(PROTOCOL STREQUAL "foreign")
        set(XML "${WAYLAND_PROTOCOLS_DIR}/staging/ext-foreign-toplevel-list/ext-foreign-toplevel-list-v1.xml")
    elseif(PROTOCOL STREQUAL "mapping")
        set(XML "${HYPRLAND_PROTOCOLS_DIR}/protocols/hyprland-toplevel-mapping-v1.xml")
    elseif(PROTOCOL STREQUAL "source")
        set(XML "${WAYLAND_PROTOCOLS_DIR}/staging/ext-image-capture-source/ext-image-capture-source-v1.xml")
    elseif(PROTOCOL STREQUAL "copy")
        set(XML "${WAYLAND_PROTOCOLS_DIR}/staging/ext-image-copy-capture/ext-image-copy-capture-v1.xml")
    else()
        set(XML "${CMAKE_CURRENT_SOURCE_DIR}/protocols/wlr-foreign-toplevel-management-unstable-v1.xml")
    endif()
    add_custom_command(OUTPUT thumbnail-${PROTOCOL}-client.h thumbnail-${PROTOCOL}-protocol.c
        COMMAND ${WAYLAND_SCANNER} client-header ${XML} thumbnail-${PROTOCOL}-client.h
        COMMAND ${WAYLAND_SCANNER} private-code ${XML} thumbnail-${PROTOCOL}-protocol.c
        DEPENDS ${XML} VERBATIM)
    target_sources(bwm-thumbnail-protocols PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/thumbnail-${PROTOCOL}-protocol.c
        ${CMAKE_CURRENT_BINARY_DIR}/thumbnail-${PROTOCOL}-client.h)
    add_custom_command(OUTPUT thumbnail-${PROTOCOL}-server.h
        COMMAND ${WAYLAND_SCANNER} server-header ${XML} thumbnail-${PROTOCOL}-server.h DEPENDS ${XML} VERBATIM)
    target_sources(bwm-plasma-configuration PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/thumbnail-${PROTOCOL}-client.h)
endforeach()
target_link_libraries(bwm-plasma-configuration PUBLIC PkgConfig::WAYLAND_CLIENT)
target_compile_definitions(bwm-plasma-configuration PRIVATE BWM_TASK_CONTEXT_SHA256="ceefbecbc0daf6d4e9968a075b3e8c55a59815b79c89f7add6d7b88dc4cc4f81")
target_link_libraries(bwm-plasma-configuration PUBLIC PW::LibTaskManager KF6::Service KF6::KIOGui KF6::KIOFileWidgets)
target_compile_definitions(bwm-plasma-configuration PRIVATE BWM_TASK_HELPER_SOURCE="${CMAKE_CURRENT_SOURCE_DIR}/../../config/hypr/skins/plasma/scripts/native-tasks.py")
add_library(bwm-window-system STATIC desktopbridge.cpp windowsystemplugin.cpp)
target_link_libraries(bwm-window-system PUBLIC KF6::WindowSystem Qt6::Widgets)
target_compile_definitions(bwm-window-system PRIVATE QT_STATICPLUGIN BWM_WINDOW_MANAGER_SOURCE="${CMAKE_CURRENT_SOURCE_DIR}/../../config/hypr/skins/plasma/scripts/kwin-window.py")
target_link_libraries(bwm-plasma-configuration PUBLIC bwm-window-system)
qt6_generate_wayland_protocol_client_sources(bwm-plasma-configuration FILES ${HYPRLAND_PROTOCOLS_DIR}/protocols/hyprland-focus-grab-v1.xml)
qt6_generate_wayland_protocol_client_sources(bwm-plasma-configuration FILES ${CMAKE_CURRENT_SOURCE_DIR}/../bwm-plasma-desktops/bwm-plasma-desktop-control-v1.xml)
target_link_libraries(bwm-plasma-configuration PUBLIC Qt6::Widgets Qt6::Quick Plasma::Plasma Plasma::PlasmaQuick KF6::ConfigCore KF6::ConfigQml KF6::Package KF6::CoreAddons KF6::NewStuffWidgets KF6::NewStuffCore KF6::Svg KF6::I18n LayerShellQt::Interface Qt6::WaylandClient Qt6::GuiPrivate)
add_executable(bwm-plasma-host main.cpp trayprobe.cpp)
target_link_libraries(bwm-plasma-host PRIVATE bwm-plasma-configuration Qt6::DBus)
target_compile_definitions(bwm-plasma-host PRIVATE BWM_SHELL_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shell")
target_link_libraries(bwm-plasma-host PRIVATE Qt6::Widgets Qt6::Quick Plasma::Plasma Plasma::PlasmaQuick KF6::Package KF6::ConfigCore KF6::ConfigQml)
include(CTest)
if(BUILD_TESTING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    find_package(Qt6 REQUIRED COMPONENTS Test)
    find_package(KF6StatusNotifierItem REQUIRED)
    find_program(BWM_TEST_LUA NAMES lua5.4 lua REQUIRED)
    find_program(BWM_TEST_SYCOCA NAMES kbuildsycoca6 REQUIRED)
    add_test(NAME isolated-task-application-launch COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-task-launch.py
        --binary $<TARGET_FILE:bwm-plasma-host> --sycoca ${BWM_TEST_SYCOCA}
        --report ${CMAKE_CURRENT_BINARY_DIR}/task-launch-results.json)
    set_tests_properties(isolated-task-application-launch PROPERTIES TIMEOUT 45)
    set(BWM_GUARD_TEST_ASAN)
    if(CMAKE_CXX_FLAGS MATCHES "fsanitize=address")
        set(BWM_GUARD_TEST_ASAN --asan)
    endif()
    add_test(NAME isolated-workspace-activation-routing COMMAND ${Python3_EXECUTABLE}
        ${CMAKE_CURRENT_SOURCE_DIR}/../bwm-plasma-desktops/check-activation-routing.py
        --compiler ${CMAKE_CXX_COMPILER} ${BWM_GUARD_TEST_ASAN}
        --report ${CMAKE_CURRENT_BINARY_DIR}/activation-routing-results.json)
    set_tests_properties(isolated-workspace-activation-routing PROPERTIES TIMEOUT 45)
    add_test(NAME isolated-screenshare-monitor-guard COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-screenshare-guard.py
        --compiler ${CMAKE_CXX_COMPILER} ${BWM_GUARD_TEST_ASAN} --report ${CMAKE_CURRENT_BINARY_DIR}/screenshare-guard-results.json)
    add_executable(test-taskthumbnail test-taskthumbnail.cpp)
    target_link_libraries(test-taskthumbnail PRIVATE bwm-plasma-configuration Qt6::Test)
    add_test(NAME isolated-task-thumbnail COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-thumbnail-local.py
        --binary $<TARGET_FILE:test-taskthumbnail> --host $<TARGET_FILE:bwm-plasma-host> --report ${CMAKE_CURRENT_BINARY_DIR}/thumbnail-local-results.json)
    add_executable(test-previewappearance test-previewappearance.cpp)
    target_link_libraries(test-previewappearance PRIVATE Qt6::Widgets Plasma::Plasma)
    add_test(NAME isolated-preview-appearance COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-preview-appearance.py
        --binary $<TARGET_FILE:bwm-plasma-host> --probe $<TARGET_FILE:test-previewappearance>
        --report ${CMAKE_CURRENT_BINARY_DIR}/appearance-results.json)
    set_tests_properties(isolated-preview-appearance PROPERTIES TIMEOUT 45)
    add_executable(test-taskmetadata test-taskmetadata.cpp)
    target_link_libraries(test-taskmetadata PRIVATE bwm-plasma-configuration Qt6::Test)
    target_compile_definitions(test-taskmetadata PRIVATE BWM_TEST_SYCOCA_PROGRAM="${BWM_TEST_SYCOCA}")
    add_executable(test-paneltasks test-paneltasks.cpp)
    target_link_libraries(test-paneltasks PRIVATE bwm-plasma-configuration Qt6::Test)
    target_compile_definitions(test-paneltasks PRIVATE BWM_SHELL_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shell" BWM_TEST_SYCOCA_PROGRAM="${BWM_TEST_SYCOCA}")
    add_executable(test-taskmenu test-taskmenu.cpp)
    target_link_libraries(test-taskmenu PRIVATE bwm-plasma-configuration Qt6::Test)
    target_compile_definitions(test-taskmenu PRIVATE BWM_SHELL_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shell")
    add_subdirectory(../bwm-plasma-desktops desktop-protocol)
    add_executable(thumbnail-test-display ../bwm-plasma-desktops/test-display.cpp tests/thumbnail-server.cpp
        ${CMAKE_CURRENT_BINARY_DIR}/desktop-protocol/test-xdg-shell.c
        ${CMAKE_CURRENT_BINARY_DIR}/desktop-protocol/test-xdg-shell-server.h)
    target_compile_definitions(thumbnail-test-display PRIVATE BWM_THUMBNAIL_FIXTURE=1)
    target_include_directories(thumbnail-test-display PRIVATE ${CMAKE_CURRENT_BINARY_DIR} ${CMAKE_CURRENT_BINARY_DIR}/desktop-protocol ${CMAKE_CURRENT_SOURCE_DIR}/tests)
    target_link_libraries(thumbnail-test-display PRIVATE bwm-desktop-protocol bwm-thumbnail-protocols)
    foreach(PROTOCOL foreign mapping source copy)
        target_sources(thumbnail-test-display PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/thumbnail-${PROTOCOL}-server.h)
    endforeach()
    add_executable(test-taskthumbnail-native test-taskthumbnail-native.cpp)
    target_link_libraries(test-taskthumbnail-native PRIVATE bwm-plasma-configuration Qt6::Test)
    add_test(NAME native-task-thumbnail COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-desktops.py
        --fixture $<TARGET_FILE:thumbnail-test-display> --client $<TARGET_FILE:test-taskthumbnail-native>
        --thumbnails --report ${CMAKE_CURRENT_BINARY_DIR}/thumbnail-native-results.json)
    set_tests_properties(native-task-thumbnail PROPERTIES TIMEOUT 55)
    add_test(NAME desktop-workspace-projection COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/../bwm-plasma-desktops/check-count-mirror.py
        --binary $<TARGET_FILE:test-workspace-projection> --report ${CMAKE_CURRENT_BINARY_DIR}/count-mirror-results.json)
    add_test(NAME native-desktop-provider-arbitration COMMAND $<TARGET_FILE:test-desktop-provider>)
    set_tests_properties(native-desktop-provider-arbitration PROPERTIES TIMEOUT 20)
    add_executable(test-desktops test-desktops.cpp)
    target_link_libraries(test-desktops PRIVATE bwm-plasma-configuration Qt6::Test)
    add_executable(test-taskdelegate test-taskdelegate.cpp)
    target_link_libraries(test-taskdelegate PRIVATE bwm-plasma-configuration Qt6::Test)
    target_compile_definitions(test-taskdelegate PRIVATE BWM_SHELL_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shell" BWM_TEST_SYCOCA_PROGRAM="${BWM_TEST_SYCOCA}")
    add_test(NAME native-task-delegate-render COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-desktops.py
        --fixture $<TARGET_FILE:desktop-test-display> --client $<TARGET_FILE:test-taskdelegate>
        --memory-render --report ${CMAKE_CURRENT_BINARY_DIR}/task-delegate-results.json)
    set_tests_properties(native-task-delegate-render PROPERTIES TIMEOUT 55)
    add_test(NAME native-desktop-protocol COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-desktops.py
        --fixture $<TARGET_FILE:desktop-test-display> --client $<TARGET_FILE:test-desktops>
        --report ${CMAKE_CURRENT_BINARY_DIR}/desktop-protocol-results.json)
    set_tests_properties(native-desktop-protocol PROPERTIES TIMEOUT 55)
    add_test(NAME native-desktop-arbitrated-kde-consumer COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-desktops.py
        --fixture $<TARGET_FILE:desktop-provider-test-display> --client $<TARGET_FILE:test-desktops> --arbitrated
        --report ${CMAKE_CURRENT_BINARY_DIR}/desktop-arbitrated-kde-results.json)
    set_tests_properties(native-desktop-arbitrated-kde-consumer PROPERTIES TIMEOUT 55)
    add_test(NAME native-desktop-control-wire COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-desktops.py
        --fixture $<TARGET_FILE:desktop-test-display> --client $<TARGET_FILE:test-desktop-control-wire>
        --report ${CMAKE_CURRENT_BINARY_DIR}/desktop-control-wire-results.json)
    set_tests_properties(native-desktop-control-wire PROPERTIES TIMEOUT 55)
    # Real-Hyprland acceptance: built only, run by check-desktops-hyprland.py
    # against a disposable nested Hyprland (never registered with CTest).
    add_executable(test-desktops-hyprland test-desktops-hyprland.cpp)
    target_link_libraries(test-desktops-hyprland PRIVATE bwm-plasma-configuration Qt6::Test)
    target_compile_definitions(test-desktops-hyprland PRIVATE BWM_TASK_HELPER_SOURCE="${CMAKE_CURRENT_SOURCE_DIR}/../../config/hypr/skins/plasma/scripts/native-tasks.py")
    add_executable(test-tasks test-tasks.cpp)
    target_link_libraries(test-tasks PRIVATE bwm-plasma-configuration Qt6::Test)
    target_compile_definitions(test-tasks PRIVATE BWM_TASK_HELPER_SOURCE="${CMAKE_CURRENT_SOURCE_DIR}/../../config/hypr/skins/plasma/scripts/native-tasks.py")
    add_executable(test-desktop test-desktop.cpp)
    target_link_libraries(test-desktop PRIVATE bwm-window-system Qt6::Test Qt6::Quick Plasma::Plasma)
    add_executable(test-surfaces test-surfaces.cpp)
    target_link_libraries(test-surfaces PRIVATE bwm-plasma-configuration Qt6::Test)
    add_test(NAME surface-geometry COMMAND test-surfaces)
    set_tests_properties(surface-geometry PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
    add_executable(test-plasma-ui test-ui.cpp trayprobe.cpp)
    add_executable(test-r6-native test-r6-native.cpp)
    set(R6_ALPHA_XML "${WAYLAND_PROTOCOLS_DIR}/staging/alpha-modifier/alpha-modifier-v1.xml")
    add_custom_command(OUTPUT r6-alpha-client.h r6-alpha-protocol.c
        COMMAND ${WAYLAND_SCANNER} client-header ${R6_ALPHA_XML} r6-alpha-client.h
        COMMAND ${WAYLAND_SCANNER} private-code ${R6_ALPHA_XML} r6-alpha-protocol.c
        DEPENDS ${R6_ALPHA_XML} VERBATIM)
    target_sources(test-r6-native PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/r6-alpha-client.h ${CMAKE_CURRENT_BINARY_DIR}/r6-alpha-protocol.c)
    target_include_directories(test-r6-native PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
    target_link_libraries(test-r6-native PRIVATE Qt6::GuiPrivate)
    target_link_libraries(test-r6-native PRIVATE bwm-plasma-configuration PkgConfig::WAYLAND_CLIENT)
    target_link_libraries(test-plasma-ui PRIVATE bwm-plasma-configuration Qt6::DBus Qt6::Test KF6::Package)
    target_compile_definitions(test-plasma-ui PRIVATE BWM_SHELL_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shell")
    # Session-only (not in CTest): run through check-edit-mode-session.py.
    add_executable(test-editmode-session test-editmode-session.cpp)
    target_link_libraries(test-editmode-session PRIVATE bwm-plasma-configuration Qt6::Test KF6::Package)
    target_compile_definitions(test-editmode-session PRIVATE BWM_SHELL_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shell")
    add_executable(test-plasma-tray-events test-tray-events.cpp)
    target_link_libraries(test-plasma-tray-events PRIVATE bwm-plasma-configuration Qt6::WaylandClientPrivate
        Qt6::DBus Qt6::Test KF6::StatusNotifierItem)
    add_test(NAME isolated-local-configuration COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-local.py
        --binary $<TARGET_FILE:bwm-plasma-host> --ui-test $<TARGET_FILE:test-plasma-ui>
        --desktop-test $<TARGET_FILE:test-desktop>
        --tasks-test $<TARGET_FILE:test-tasks>
        --menu-test $<TARGET_FILE:test-taskmenu>
        --metadata-test $<TARGET_FILE:test-taskmetadata>
        --panel-tasks-test $<TARGET_FILE:test-paneltasks>
        --lua ${BWM_TEST_LUA}
        --report ${CMAKE_CURRENT_BINARY_DIR}/local-results.json)
    set_tests_properties(isolated-local-configuration PROPERTIES TIMEOUT 120)
    set(BWM_TEST_UPSTREAM "" CACHE PATH "Selected extracted libplasma 6.7.5 sources")
    set(BWM_TEST_EXTERNAL "" CACHE PATH "Selected third-party plasmoid sources")
    if(BWM_TEST_UPSTREAM AND BWM_TEST_EXTERNAL)
        find_package(Python3 REQUIRED COMPONENTS Interpreter)
        add_test(NAME isolated-plasmoids COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check-isolated.py
            --binary $<TARGET_FILE:bwm-plasma-host> --upstream ${BWM_TEST_UPSTREAM}
            --external ${BWM_TEST_EXTERNAL} --ui-test $<TARGET_FILE:test-plasma-ui>
            --report ${CMAKE_CURRENT_BINARY_DIR}/isolated-results.json)
        set_tests_properties(isolated-plasmoids PROPERTIES TIMEOUT 120)
    endif()
endif()
