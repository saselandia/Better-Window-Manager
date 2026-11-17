// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <cstdint>
#include <string>
#include <string_view>
namespace BwmPlasma {
// Runtime copy of the existing shared preference; never reads/writes a file.
class CountMirror {
public:
    bool accept(std::string_view command);
    bool known()const{return m_value>0;}
    int value()const{return m_value;}
    uint64_t revision()const{return m_revision;}
    std::string receipt(bool accepted)const;
private:
    int m_value=0;
    uint64_t m_revision=0;
};
}
