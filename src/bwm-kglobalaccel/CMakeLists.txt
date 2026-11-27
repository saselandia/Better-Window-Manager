cmake_minimum_required(VERSION 3.25)
project(bwm-kglobalaccel VERSION 0.1 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_AUTOMOC ON)
find_package(Qt6 REQUIRED COMPONENTS Gui DBus Network GuiPrivate)
find_package(KF6GlobalAccel REQUIRED)
find_package(KGlobalAccelD 6.7.5 EXACT REQUIRED) # Same library KWin embeds on Wayland.
find_package(PkgConfig REQUIRED)
pkg_check_modules(XKB REQUIRED IMPORTED_TARGET xkbcommon)

add_library(bwmkeymap STATIC keymap.cpp)
target_link_libraries(bwmkeymap PUBLIC Qt6::Gui Qt6::GuiPrivate PkgConfig::XKB)

add_executable(bwm-kglobalaccel main.cpp platform.cpp controller.cpp)
# Static platform plugin compiled into the daemon (QPluginLoader::staticPlugins()).
target_compile_definitions(bwm-kglobalaccel PRIVATE QT_STATICPLUGIN)
target_link_libraries(bwm-kglobalaccel PRIVATE bwmkeymap K::KGlobalAccelD KF6::GlobalAccel Qt6::DBus Qt6::Network)

option(BUILD_TESTING "Build tests" ON)
if(BUILD_TESTING)
    enable_testing()
    find_package(Qt6 REQUIRED COMPONENTS Test)
    find_package(Qt6 REQUIRED COMPONENTS Gui)
    add_executable(test-client test-client.cpp)
    target_link_libraries(test-client PRIVATE KF6::GlobalAccel Qt6::Gui Qt6::DBus)
    add_executable(test-keymap test-keymap.cpp)
    target_link_libraries(test-keymap PRIVATE bwmkeymap Qt6::Test)
    add_test(NAME keymap COMMAND test-keymap)
    add_test(NAME daemon COMMAND dbus-run-session -- python3 ${CMAKE_CURRENT_SOURCE_DIR}/check-daemon.py
             --binary $<TARGET_FILE:bwm-kglobalaccel> --client $<TARGET_FILE:test-client>)
    set_tests_properties(daemon PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen" TIMEOUT 60)
endif()
