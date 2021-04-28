FROM ubuntu:18.04

# Install dependencies
RUN dpkg --add-architecture i386
RUN export DEBIAN_FRONTEND=noninteractive &&                                \
    apt-get update &&                                                       \
    apt-get -y install git build-essential gcc-multilib g++-multilib        \
    libmad0-dev:i386 libc6-dev:i386 wget python3-pip

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get helper scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts

# Get the SoX source
RUN wget -O - https://sourceforge.net/projects/sox/files/sox/14.4.2/sox-14.4.2.tar.gz | tar xz
