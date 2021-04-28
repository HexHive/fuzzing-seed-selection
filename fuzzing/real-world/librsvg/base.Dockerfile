FROM ubuntu:18.04

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Install dependencies
RUN dpkg --add-architecture i386
RUN export DEBIAN_FRONTEND=noninteractive &&                                \
    apt-get update &&                                                       \
    apt-get -y install git build-essential gcc-multilib g++-multilib        \
    libc6-dev:i386 autoconf pkg-config libtool libgirepository1.0-dev       \
    gtk-doc-tools libgdk-pixbuf2.0-dev:i386 libglib2.0-dev:i386             \
    libgio2.0-cil-dev libxml2-dev:i386 libpango1.0-dev:i386                 \
    libpangocairo-1.0.0:i386 libpangoft2-1.0.0:i386 libcairo2-dev:i386      \
    libcroco3-dev:i386 wget python3-pip

# Install LLVM 8
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN apt-get install -y llvm-8 clang-8

# Get helper scripts
RUN git clone https://github.com/HexHive/fuzzing-seed-selection &&  \
    pip3 install fuzzing-seed-selection/scripts

# Get the librsvg source
RUN wget -O - https://gitlab.gnome.org/GNOME/librsvg/-/archive/2.40.20/librsvg-2.40.20.tar.gz | tar xz

# we have to use 'autoreconf -i' or 'autogen.sh' because we don't have
# the configure script.

# for whatever reason, the autoreconf (autogen) couldn't find gtk-doc.make
RUN ln -s /usr/share/gtk-doc/data/gtk-doc.make librsvg-2.40.20

# gobject-introspection ultimately has to be disabled because we can't install 
# the 32bit version of it without breaking dependencies. There is also a weird
# case where it is trying to link against 64bit version of libfreetype.so.
# Hence, the extra -L flag in the LDFLAGS
