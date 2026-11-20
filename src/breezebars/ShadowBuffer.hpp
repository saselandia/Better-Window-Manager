// SPDX-FileCopyrightText: 2026 BWM
// SPDX-License-Identifier: BSD-3-Clause
#pragma once

#include "DecoWire.hpp"
#include <cerrno>
#include <sys/stat.h>
#include <unistd.h>

namespace BwmDeco {
    // A short/truncated memfd must never cause SIGBUS in the compositor. Copy with
    // pread (not mmap), checking the bounded wire layout before allocating/reading.
    inline std::optional<std::vector<uint8_t>> readShadowPixels(const SShadow& s, int fd) {
        struct stat st {};
        if (fd < 0 || fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_size < 0 ||
            !shadowIsSane(s, static_cast<size_t>(st.st_size)))
            return std::nullopt;
        std::vector<uint8_t> pixels(static_cast<size_t>(s.stride) * s.height);
        size_t offset = 0;
        while (offset < pixels.size()) {
            const auto n = pread(fd, pixels.data() + offset, pixels.size() - offset, static_cast<off_t>(offset));
            if (n < 0 && errno == EINTR)
                continue;
            if (n <= 0)
                return std::nullopt;
            offset += static_cast<size_t>(n);
        }
        return pixels;
    }
}
