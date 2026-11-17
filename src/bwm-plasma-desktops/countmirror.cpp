// SPDX-License-Identifier: GPL-2.0-or-later
#include "countmirror.h"
#include <charconv>
namespace BwmPlasma {
bool CountMirror::accept(std::string_view command){
    constexpr std::string_view prefix="bwm-plasma-desktops-count ";
    if(!command.starts_with(prefix))return false;
    const auto argument=command.substr(prefix.size());
    if(argument.empty() || argument.size()>3)return false;
    int value=0;const auto [end,error]=std::from_chars(argument.data(),argument.data()+argument.size(),value);
    if(error!=std::errc() || end!=argument.data()+argument.size() || value<1 || value>100 || std::to_string(value)!=argument)return false;
    if(value!=m_value){m_value=value;++m_revision;}
    return true;
}
std::string CountMirror::receipt(bool accepted)const{
    return "{\"version\":1,\"accepted\":"+std::string(accepted?"true":"false")+",\"configuredCount\":"+std::to_string(m_value)+
        ",\"revision\":"+std::to_string(m_revision)+(accepted?"}":",\"error\":\"invalid-count-command\"}");
}
}
