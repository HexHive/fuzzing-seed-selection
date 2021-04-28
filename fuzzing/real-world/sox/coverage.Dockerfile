FROM seed-selection/real-world/sox/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Build coverage SoX
RUN mkdir /build
RUN cd sox-14.4.2 &&                                                        \
    CC=clang-8 CXX=clang++-8                                                \
    CFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"               \
    CXXFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"             \
    LDFLAGS="-m32"                                                          \
    ./configure --prefix=/build --host=i386-linux
RUN cd sox-14.4.2 &&    \
    make clean &&       \
    make -s &&          \
    make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py                         \
    -o /build/lib /build/bin/sox

# The `build` directory can be extracted to the host machine
