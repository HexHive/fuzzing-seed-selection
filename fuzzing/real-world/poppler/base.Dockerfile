FROM ubuntu:18.04

# Install dependencies
RUN dpkg --add-architecture i386
RUN export DEBIAN_FRONTEND=noninteractive &&                                \
    apt-get update &&                                                       \
    apt-get -y install git build-essential wget gcc-multilib g++-multilib   \
    libc6-dev:i386 xz-utils pkg-config libfreetype6-dev libfontconfig-dev   \
    libjpeg-dev libopenjp2-7-dev cmake libfreetype6-dev:i386                \
    libfontconfig-dev:i386 libjpeg-dev:i386 python3-pip

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get helper scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts

# Get the poppler source
RUN wget -O - https://poppler.freedesktop.org/poppler-0.64.0.tar.xz | tar xJ

# Make a copy for the source so that we don't have to reinstall libopenjp2-7
# again
RUN cp -r poppler-0.64.0 poppler-0.64.0-afl

# Add the poppler build toolchain files
ADD toolchain.cmake /
ADD afl-toolchain-llvm.cmake /

# It seems that the compiler flags passed in toolchain.cmake is not used by cmake
