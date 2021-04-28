FROM ubuntu:18.04

# Install dependencies
RUN dpkg --add-architecture i386
RUN export DEBIAN_FRONTEND=noninteractive &&                                \
    apt-get update &&                                                       \
    apt-get -y install git wget build-essential gcc-multilib g++-multilib   \
    libc6-dev:i386 python3-pip

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get helper scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts

# Get the libtiff source
RUN wget -O - http://download.osgeo.org/libtiff/tiff-4.0.9.tar.gz | tar xz
