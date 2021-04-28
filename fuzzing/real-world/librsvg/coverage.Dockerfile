FROM seed-selection/real-world/librsvg/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Build coverage librsvg
RUN mkdir /build
RUN cd librsvg-2.40.20 &&                                                   \
    PKG_CONFIG_PATH=/usr/lib/i386-linux-gnu/pkgconfig                       \
    CC=clang-8 CXX=clang++-8                                                \
    CFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"               \
    CXXFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"             \
    LDFLAGS="-L/usr/lib/i386-linux-gnu -m32"                                \
    ./autogen.sh --prefix=/build --enable-introspection=no                  \
    --host=i386-linux
RUN cd librsvg-2.40.20 &&                                                   \
    make clean &&                                                           \
    make -j &&                                                              \
    make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py                         \
    -o /build/lib /build/bin/rsvg-convert

# The `build` and directory can be extracted to the host machine
