FROM seed-selection/real-world/libxml2/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Build coverage libxml2
RUN mkdir /build
RUN cd libxml2-2.9.0 &&                                                     \
    CC=clang-8 CXX=clang++-8                                                \
    CFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"               \
    CXXFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"             \
    LDFLAGS="-m32"                                                          \
    ./configure --prefix=/build --host=i386-linux
RUN cd libxml2-2.9.0 &&                                                     \
    make clean &&                                                           \
    make -j &&                                                              \
    make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py                         \
    -o /build/lib /build/bin/xmllint

# The `build` directory can be extracted to the host machine
