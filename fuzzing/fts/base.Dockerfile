FROM ubuntu:18.04

# Install dependencies
RUN dpkg --add-architecture i386
RUN export DEBIAN_FRONTEND=noninteractive &&                                \
    apt-get update &&                                                       \
    apt-get -y install git subversion build-essential autoconf libtool      \
        cmake gcc-multilib g++-multilib pkg-config libarchive-dev:i386      \
        zlib1g-dev:i386 libbz2-dev:i386 libxml2-dev:i386 libssl-dev:i386    \
        liblzma-dev:i386 libexpat-dev:i386 nasm python3-pip wget

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get helper scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts

# Get LLVM compiler-rt
RUN wget -O - http://releases.llvm.org/8.0.0/compiler-rt-8.0.0.src.tar.xz | tar xJ

# Get Google FTS
RUN git clone https://github.com/google/fuzzer-test-suite
ADD build.sh /fuzzer-test-suite
ADD common.sh /fuzzer-test-suite
ADD libarchive-2017-01-04-build.sh /fuzzer-test-suite/libarchive-2017-01-04/build.sh
ADD libjpeg-turbo-07-2017-build.sh /fuzzer-test-suite/libjpeg-turbo-07-2017/build.sh
ADD libxml2-v2.9.2-build.sh /fuzzer-test-suite/libxml2-v2.9.2/build.sh

ENV LIBFUZZER_SRC="/compiler-rt-8.0.0.src/lib/fuzzer"
