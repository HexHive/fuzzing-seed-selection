FROM seed-selection/real-world/sox/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Get and build AFL
ENV AFL_CC=clang-8
ENV AFL_CXX=clang++-8

RUN git clone --no-checkout https://github.com/google/afl &&    \
    git -C afl checkout v256b
RUN cd afl &&                           \
    export LLVM_CONFIG=llvm-config-8 && \
    export CC=$AFL_CC &&                \
    export CXX=$AFL_CXX &&              \
    make -j &&                          \
    make -j -C llvm_mode

# Build AFL SoX
RUN mkdir /build
RUN cd sox-14.4.2 &&                                                        \
    CC=/afl/afl-clang-fast CXX=/afl/afl-clang-fast++ LD=ldd                 \
    CFLAGS="-m32 -fsanitize=address" CXXFLAGS="-m32 -fsanitize=address"     \
    LDFLAGS="-m32 -fsanitize=address"                                       \
    ./configure --prefix=/build --host=i386-linux
RUN cd sox-14.4.2 &&    \
    make clean &&       \
    make -s &&          \
    make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py -o /build/lib           \
    /build/bin/sox

# The `build` directory can be extracted to the host machine
