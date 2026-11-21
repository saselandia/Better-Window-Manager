cmake_minimum_required(VERSION 3.27)

project(hyprbars
    DESCRIPTION "hyprbars plugin for Hyprland"
    VERSION 0.1
    LANGUAGES C CXX
)

set(CMAKE_CXX_STANDARD 23)

file(GLOB_RECURSE SRC "*.cpp")

add_library(hyprbars SHARED ${SRC})
find_program(WAYLAND_SCANNER wayland-scanner REQUIRED)
add_custom_command(OUTPUT kde-shadow-server.h kde-shadow-protocol.c
    COMMAND ${WAYLAND_SCANNER} server-header ${CMAKE_CURRENT_SOURCE_DIR}/protocols/shadow.xml kde-shadow-server.h
    COMMAND ${WAYLAND_SCANNER} private-code ${CMAKE_CURRENT_SOURCE_DIR}/protocols/shadow.xml kde-shadow-protocol.c
    DEPENDS protocols/shadow.xml VERBATIM)
target_sources(hyprbars PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/kde-shadow-protocol.c ${CMAKE_CURRENT_BINARY_DIR}/kde-shadow-server.h)
target_include_directories(hyprbars PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
target_compile_options(hyprbars PRIVATE $<$<COMPILE_LANGUAGE:CXX>:-fno-gnu-unique>)

find_package(PkgConfig REQUIRED)
pkg_check_modules(deps REQUIRED IMPORTED_TARGET
    hyprland
    libdrm
    libinput
    libudev
    pixman-1
    wayland-server
    xkbcommon
)
target_link_libraries(hyprbars PRIVATE rt xcb dl PkgConfig::deps)

install(TARGETS hyprbars)
