FROM seed-selection/fts/base

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

# Build AFL FTS
ENV AFL_SRC="/afl"
ENV FUZZING_ENGINE="afl"
RUN mkdir /build-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh freetype2-2017
RUN get_libs.py -o /build-afl/RUNDIR-afl-freetype2-2017/lib        \
    /build-afl/RUNDIR-afl-freetype2-2017/freetype2-2017-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh guetzli-2017-3-30
RUN get_libs.py -o /build-afl/RUNDIR-afl-guetzli-2017-3-30/lib     \
    /build-afl/RUNDIR-afl-guetzli-2017-3-30/guetzli-2017-3-30-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh json-2017-02-12
RUN get_libs.py -o /build-afl/RUNDIR-afl-json-2017-02-12/lib       \
    /build-afl/RUNDIR-afl-json-2017-02-12/json-2017-02-12-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh libarchive-2017-01-04
RUN get_libs.py -o /build-afl/RUNDIR-afl-libarchive-2017-01-04/lib \
    /build-afl/RUNDIR-afl-libarchive-2017-01-04/libarchive-2017-01-04-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh libjpeg-turbo-07-2017
RUN get_libs.py -o /build-afl/RUNDIR-afl-libjpeg-turbo-07-2017/lib \
    /build-afl/RUNDIR-afl-libjpeg-turbo-07-2017/libjpeg-turbo-07-2017-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh libpng-1.2.56
RUN get_libs.py -o /build-afl/RUNDIR-afl-libpng-1.2.56/lib         \
    /build-afl/RUNDIR-afl-libpng-1.2.56/libpng-1.2.56-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh libxml2-v2.9.2
RUN get_libs.py -o /build-afl/RUNDIR-afl-libxml2-v2.9.2/lib        \
    /build-afl/RUNDIR-afl-libxml2-v2.9.2/libxml2-v2.9.2-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh pcre2-10.00
RUN get_libs.py -o /build-afl/RUNDIR-afl-pcre2-10.00/lib           \
    /build-afl/RUNDIR-afl-pcre2-10.00/pcre2-10.00-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh re2-2014-12-09
RUN get_libs.py -o /build-afl/RUNDIR-afl-re2-2014-12-09/lib        \
    /build-afl/RUNDIR-afl-re2-2014-12-09/re2-2014-12-09-afl

RUN cd /build-afl && /fuzzer-test-suite/build.sh vorbis-2017-12-11
RUN get_libs.py -o /build-afl/RUNDIR-afl-vorbis-2017-12-11/lib     \
    /build-afl/RUNDIR-afl-vorbis-2017-12-11/vorbis-2017-12-11-afl

RUN echo "\033[0;33m * Extract the '/build-afl' and '/afl' directories\033[0m"
