FROM ubuntu:18.04

# Install depndencies
RUN export DEBIAN_FRONTEND=noninteractiv &&                                 \
    apt-get update &&                                                       \
    apt-get -y install git build-essential wget binutils-dev libunwind-dev  \
        parallel python3 python3-pip

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get AFLFast
RUN git clone --no-checkout https://github.com/mboehme/aflfast &&           \
    git -C aflfast checkout 11ec1828448d27bdcc54fdeb91bf3215d4d8c583
ADD afl_llvm_mode.Makefile /aflfast/llvm_mode/Makefile
RUN make -C aflfast -j &&                                                   \
    CC=clang-8 CXX=clang++-8 LLVM_CONFIG=llvm-config-8 make -C aflfast/llvm_mode

# Get AFL++
RUN git clone --no-checkout https://github.com/AFLplusplus/AFLplusplus aflplusplus &&   \
    git -C aflplusplus checkout fa933036a7bdbf9a59a9b1b7669d6ec7db64a202 && \
    CC=clang-8 CXX=clang++-8 LLVM_CONFIG=llvm-config-8 make -C aflplusplus

# Get honggfuzz
RUN git clone --no-checkout https://github.com/google/honggfuzz &&          \
    git -C honggfuzz checkout 5810856f5381f93c461e3a7ba6452945c0725574 &&   \
    make -C honggfuzz

# Get binutils
RUN wget ftp://sourceware.org/pub/binutils/snapshots/binutils-2.30.0.tar.xz

# AFLFast build
RUN rm -rf binutils-2.30.0
RUN tar xJf /binutils-2.30.0.tar.xz
RUN mkdir -p /binutils-afl
RUN cd binutils-2.30.0 &&                                                   \
    export AFL_CC=clang-8 &&                                                \
    export AFL_CXX=clang++-8 &&                                             \
    export CC=/aflfast/afl-clang-fast &&                                    \
    export CXX=/aflfast/afl-clang-fast++ &&                                 \
    ./configure --prefix=/binutils-aflfast --disable-shared --disable-werror\
    --disable-ld --disable-gdb &&                                           \
    make -j && make install

# AFL++ build
RUN rm -rf binutils-2.30.0
RUN tar xJf /binutils-2.30.0.tar.xz
RUN mkdir -p /binutils-aflplusplus/afl
RUN cd binutils-2.30.0 &&                                                   \
    export AFL_CC=clang-8 &&                                                \
    export AFL_CXX=clang++-8 &&                                             \
    export CC=/aflplusplus/afl-clang-fast &&                                \
    export CXX=/aflplusplus/afl-clang-fast++ &&                             \
    ./configure --prefix=/binutils-aflplusplus/afl --disable-shared         \
    --disable-werror --disable-ld --disable-gdb &&                          \
    make -j && make install

RUN rm -rf binutils-2.30.0
RUN tar xJf /binutils-2.30.0.tar.xz
RUN mkdir -p /binutils-aflplusplus/cmplog
RUN cd binutils-2.30.0 &&                                                   \
    export AFL_CC=clang-8 &&                                                \
    export AFL_CXX=clang++-8 &&                                             \
    export CC=/aflplusplus/afl-clang-fast &&                                \
    export CXX=/aflplusplus/afl-clang-fast++ &&                             \
    export AFL_LLVM_CMPLOG=1 &&                                             \
    ./configure --prefix=/binutils-aflplusplus/cmplog --disable-shared      \
    --disable-werror --disable-ld --disable-gdb &&                          \
    make -j && make install

# honggfuzz build
RUN rm -rf binutils-2.30.0
RUN tar xJf /binutils-2.30.0.tar.xz
RUN mkdir -p /binutils-honggfuzz
RUN cd binutils-2.30.0 &&                                                   \
    export CC=/honggfuzz/hfuzz_cc/hfuzz-clang &&                            \
    export CXX=/honggfuzz/hfuzz_cc/hfuzz-clang++ &&                         \
    ./configure --prefix=/binutils-honggfuzz --disable-shared               \
    --disable-werror --disable-ld --disable-gdb &&                          \
    make -j && make install

# Coverage build
RUN rm -rf binutils-2.30.0
RUN tar xJf /binutils-2.30.0.tar.xz
RUN mkdir -p /binutils-coverage
RUN cd binutils-2.30.0 &&                                                   \
    export CC=clang-8 &&                                                    \
    export CXX=clang++-8 &&                                                 \
    export CFLAGS="-fprofile-instr-generate -fcoverage-mapping" &&          \
    export CXXFLAGS="-fprofile-instr-generate -fcoverage-mapping" &&        \
    ./configure --prefix=/binutils-coverage --disable-shared                \
    --disable-werror --disable-ld --disable-gdb &&                          \
    make -j && make install

# Add fuzzer files
RUN mkdir /uninformed-seed
ADD seeds/uninformed-seed /uninformed-seed/seed
ADD seeds/cmin-seeds.tar.xz /

# Add scripts
ADD scripts /scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts
RUN pip3 install -r /scripts/requirements.txt
