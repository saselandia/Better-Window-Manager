// SPDX-FileCopyrightText: 2026 BWM contributors
// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstdint>
#include <vector>
#include <optional>
#include <cerrno>
#include <sys/stat.h>
#include <unistd.h>
namespace BwmKde {
// Never dereference a client's SHM mapping: an unsealed pool can shrink between
// validation and reading. All arithmetic and allocations are bounded before pread.
inline std::optional<std::vector<uint8_t>> readTile(int fd,int32_t width,int32_t height,int32_t stride,int32_t offset,uint64_t poolSize) {
    if(fd<0 || width<=0 || height<=0 || width>2048 || height>2048 || stride<width*4 || stride>65536 || offset<0)return {};
    const uint64_t end=uint64_t(offset)+uint64_t(height-1)*stride+uint64_t(width)*4;
    struct stat st{};if(fstat(fd,&st)!=0 || !S_ISREG(st.st_mode) || st.st_size<0 || end>uint64_t(st.st_size) || end>poolSize)return {};
    std::vector<uint8_t> result(size_t(width)*height*4);
    for(int y=0;y<height;++y){
        const size_t row=size_t(width)*4;size_t done=0;
        while(done<row){
            const auto n=pread(fd,result.data()+size_t(y)*row+done,row-done,off_t(offset)+off_t(y)*stride+done);
            if(n<0 && errno==EINTR)continue;
            if(n<=0)return {};done+=size_t(n);
        }
    }
    return result;
}
}
