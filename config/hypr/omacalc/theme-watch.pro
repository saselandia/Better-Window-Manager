QT += core gui testlib
CONFIG += testcase c++17
TEMPLATE = app
TARGET = theme-watch
isEmpty(OMACALC_SOURCE): error(Pass OMACALC_SOURCE pointing to the patched upstream source)
INCLUDEPATH += $$OMACALC_SOURCE/src
SOURCES += $$PWD/theme-watch.cpp $$OMACALC_SOURCE/src/backend.cpp
HEADERS += $$OMACALC_SOURCE/src/backend.h
