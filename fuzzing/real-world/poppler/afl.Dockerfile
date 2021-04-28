FROM seed-selection/real-world/poppler/base

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

# Configure AFL poppler
RUN mkdir /build
RUN mkdir poppler-0.64.0-afl/build &&                                       \
    cd poppler-0.64.0-afl/build &&                                          \
    cmake ..                                                                \
        -DCMAKE_TOOLCHAIN_FILE=/afl-toolchain-llvm.cmake                    \
        -DCMAKE_INSTALL_PREFIX=/build                                       \
        -DCMAKE_C_FLAGS="-m32 -fsanitize=address"                           \
        -DCMAKE_CXX_FLAGS="-m32 -fsanitize=address"                         \
        -DCMAKE_SYSTEM_PROCESSOR="i386"

# It is necessary for the 32-bit to reinstall the libopenjp2 as the 32-bit and
# 64-bit versions are mutually exclusive
RUN apt-get -y install libopenjp2-7-dev:i386

# Actually make the AFL poppler
RUN cd poppler-0.64.0-afl/build &&                                          \
    make clean && make -j && make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py -o /build/lib           \
    /build/bin/pdftotext

# The `build` directory can be extracted to the host machine
