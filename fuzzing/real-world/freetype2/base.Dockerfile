FROM ubuntu:18.04

# Install dependencies
RUN dpkg --add-architecture i386
RUN export DEBIAN_FRONTEND=noninteractive &&                                \
    apt-get update &&                                                       \
    apt-get -y install git build-essential gcc-multilib g++-multilib wget   \
        python3-pip

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get helper scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts

# Get the freetype source
RUN wget -O - https://download.savannah.gnu.org/releases/freetype/freetype-2.5.3.tar.gz | tar xz

# Create custom driver for freetype, taken from
# https://www.freetype.org/freetype2/docs/tutorial/example5.cpp
RUN mkdir ttf_bin
ADD https://www.freetype.org/freetype2/docs/tutorial/example5.cpp /ttf_bin/char2svg.cpp
