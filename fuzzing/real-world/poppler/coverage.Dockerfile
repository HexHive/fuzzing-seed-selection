FROM seed-selection/real-world/poppler/base

MAINTAINER Adrian Herrera <adrian.herrera@anu.edu.au>

# Configure coverage poppler
RUN mkdir /build
RUN mkdir poppler-0.64.0/build &&                                           \
    cd poppler-0.64.0/build &&                                              \
    cmake .. -DCMAKE_TOOLCHAIN_FILE=/toolchain.cmake                        \
        -DCMAKE_INSTALL_PREFIX=/build                                       \
        -DCMAKE_C_FLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"  \
        -DCMAKE_CXX_FLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"\
        -DCMAKE_SYSTEM_PROCESSOR="i386"

# It is necessary for the 32-bit to reinstall the libopenjp2 as the 32-bit and
# 64-bit versions are mutually exclusive
RUN apt-get -y install libopenjp2-7-dev:i386

# Actually make the coverage poppler
RUN cd poppler-0.64.0/build &&                                              \
    make clean && make -j && make install
RUN LD_LIBRARY_PATH=/build/lib get_libs.py -o /build/lib           \
    /build/bin/pdftotext

# The `build` directory can be extracted to the host machine
