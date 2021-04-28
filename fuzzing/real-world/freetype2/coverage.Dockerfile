FROM seed-selection/real-world/freetype2/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Build coverage freetype 
RUN mkdir /build
RUN cd freetype-2.5.3 &&                                                    \
    CC=clang-8 CXX=clang++-8                                                \
    CFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"               \
    CXXFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"             \
    LDFLAGS="-m32"                                                          \
    ./configure --prefix=/build --host=i386-linux --without-png
RUN cd freetype-2.5.3 &&    \
    make clean &&           \
    make -j &&              \
    make install 
RUN cd ttf_bin && rm -f char2svg &&                                \
    clang++-8 -m32 -fprofile-instr-generate -fcoverage-mapping     \
    -I/build/include/freetype2 -o char2svg                         \
    char2svg.cpp -L/build/lib/ -lfreetype

RUN cp /ttf_bin/char2svg /build/bin/
RUN LD_LIBRARY_PATH=/build/lib get_libs.py -o /build/lib  \
    /build/bin/char2svg

# The `build` directory can be extracted to the host machine
