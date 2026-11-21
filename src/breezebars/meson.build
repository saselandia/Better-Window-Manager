project('hyprbars', 'cpp', 'c',
  version: '0.1',
  default_options: ['buildtype=release'],
)

cpp_compiler = meson.get_compiler('cpp')
if cpp_compiler.has_argument('-std=c++23')
  add_global_arguments('-std=c++23', language: 'cpp')
elif cpp_compiler.has_argument('-std=c++2b')
  add_global_arguments('-std=c++2b', language: 'cpp')
else
  error('Could not configure current C++ compiler (' + cpp_compiler.get_id() + ' ' + cpp_compiler.version() + ') with required C++ standard (C++23)')
endif

add_project_arguments(
  [
    '-Wno-narrowing',
    '-fno-gnu-unique',
  ],
  language: 'cpp')

globber = run_command('find', '.', '-name', '*.cpp', check: true)
src = globber.stdout().strip().split('\n')

hyprland = dependency('hyprland')
scanner = find_program('wayland-scanner')
shadow_header = custom_target('kde-shadow-server', input: 'protocols/shadow.xml', output: 'kde-shadow-server.h', command: [scanner, 'server-header', '@INPUT@', '@OUTPUT@'])
shadow_code = custom_target('kde-shadow-code', input: 'protocols/shadow.xml', output: 'kde-shadow-protocol.c', command: [scanner, 'private-code', '@INPUT@', '@OUTPUT@'])

shared_module(meson.project_name(), src, shadow_header, shadow_code,
  include_directories: include_directories('.'),
  dependencies: [
    dependency('hyprland'),
    dependency('pixman-1'),
    dependency('libdrm'),
    dependency('libinput'),
    dependency('libudev'),
    dependency('wayland-server'),
    dependency('xkbcommon'),
    dependency('xcb'),
    cpp_compiler.find_library('dl'),
  ],
  install: true,
)
