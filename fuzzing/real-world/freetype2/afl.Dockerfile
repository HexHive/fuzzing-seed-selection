FROM seed-selection/real-world/freetype2/base

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

# Build instrumented freetype for AFL
RUN mkdir /build
RUN cd freetype-2.5.3 &&                                                    \
    CC=/afl/afl-clang-fast CXX=/afl/afl-clang-fast++                        \
    CFLAGS="-m32 -fsanitize=address"                                        \
    CXXFLAGS="-m32 -fsanitize=address"                                      \
    LDFLAGS="-m32 -fsanitize=address"                                       \
    ./configure --prefix=/build --host=i386-linux --without-png
RUN cd freetype-2.5.3 &&    \
    make clean &&           \
    make -j &&              \
    make install 
RUN cd ttf_bin && rm -f char2svg &&                                         \
    /afl/afl-clang-fast++ -m32 -fsanitize=address                           \
    -I/build/include/freetype2 -o char2svg char2svg.cpp                 \
    -L/build/lib/ -lfreetype

RUN cp /ttf_bin/char2svg /build/bin/
RUN LD_LIBRARY_PATH=/build/lib get_libs.py -o /build/lib   \
    /build/bin/char2svg

# The `build` directory can be extracted to the host machine
