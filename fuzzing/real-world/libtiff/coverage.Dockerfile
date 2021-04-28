FROM seed-selection/real-world/libtiff/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Build coverage libtiff
RUN mkdir /build
RUN cd tiff-4.0.9 &&                                                        \
    CC=clang-8 CXX=clang++-8                                                \
    CFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"               \
    CXXFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"             \
    LDFLAGS="-m32 -fno-stack-protector"                                     \
    ./configure --prefix=/build --host=i386-linux
RUN cd tiff-4.0.9 &&                                                        \
    make clean &&                                                           \
    make -j &&                                                              \
    make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py                         \
    -o /build/lib /build/bin/tiff2pdf

# The `build` directory can be extracted to the host machine
