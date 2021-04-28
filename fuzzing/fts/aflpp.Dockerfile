FROM seed-selection/fts/base

# Get and build AFL++
ENV AFL_CC=clang-8
ENV AFL_CXX=clang++-8

RUN git clone --no-checkout https://github.com/aflplusplus/aflplusplus &&   \
    git -C aflplusplus checkout 5ee63a6e6267e448342ccb28cc8d3c0d34ffc1cd
ADD aflpp_driver_GNUmakefile /aflplusplus/examples/aflpp_driver/GNUmakefile
RUN cd aflplusplus &&                       \
    export LLVM_CONFIG="llvm-config-8" &&   \
    make -j &&                              \
    make -j -C llvm_mode
RUN cd aflplusplus &&                       \
    export LLVM_CONFIG="llvm-config-8" &&   \
    export CFLAGS="-m32" &&                 \
    make -j -C examples/aflpp_driver libAFLDriver.a

# Build AFL++ FTS
ENV AFL_SRC="/aflplusplus"
ENV FUZZING_ENGINE="aflpp"
RUN mkdir /build-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh freetype2-2017
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-freetype2-2017/lib        \
    /build-aflpp/RUNDIR-aflpp-freetype2-2017/freetype2-2017-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh guetzli-2017-3-30
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-guetzli-2017-3-30/lib     \
    /build-aflpp/RUNDIR-aflpp-guetzli-2017-3-30/guetzli-2017-3-30-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh json-2017-02-12
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-json-2017-02-12/lib       \
    /build-aflpp/RUNDIR-aflpp-json-2017-02-12/json-2017-02-12-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh libarchive-2017-01-04
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-libarchive-2017-01-04/lib \
    /build-aflpp/RUNDIR-aflpp-libarchive-2017-01-04/libarchive-2017-01-04-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh libjpeg-turbo-07-2017
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-libjpeg-turbo-07-2017/lib \
    /build-aflpp/RUNDIR-aflpp-libjpeg-turbo-07-2017/libjpeg-turbo-07-2017-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh libpng-1.2.56
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-libpng-1.2.56/lib         \
    /build-aflpp/RUNDIR-aflpp-libpng-1.2.56/libpng-1.2.56-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh libxml2-v2.9.2
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-libxml2-v2.9.2/lib        \
    /build-aflpp/RUNDIR-aflpp-libxml2-v2.9.2/libxml2-v2.9.2-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh pcre2-10.00
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-pcre2-10.00/lib           \
    /build-aflpp/RUNDIR-aflpp-pcre2-10.00/pcre2-10.00-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh re2-2014-12-09
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-re2-2014-12-09/lib        \
    /build-aflpp/RUNDIR-aflpp-re2-2014-12-09/re2-2014-12-09-aflpp

RUN cd /build-aflpp && /fuzzer-test-suite/build.sh vorbis-2017-12-11
RUN get_libs.py -o /build-aflpp/RUNDIR-aflpp-vorbis-2017-12-11/lib     \
    /build-aflpp/RUNDIR-aflpp-vorbis-2017-12-11/vorbis-2017-12-11-aflpp

# Build AFL++ FTS in CmpLog mode
ENV FUZZING_ENGINE="aflpp_cmplog"
RUN mkdir /build-cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh freetype2-2017
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-freetype2-2017/lib        \
    /build-cmplog/RUNDIR-aflpp_cmplog-freetype2-2017/freetype2-2017-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh guetzli-2017-3-30
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-guetzli-2017-3-30/lib     \
    /build-cmplog/RUNDIR-aflpp_cmplog-guetzli-2017-3-30/guetzli-2017-3-30-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh json-2017-02-12
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-json-2017-02-12/lib       \
    /build-cmplog/RUNDIR-aflpp_cmplog-json-2017-02-12/json-2017-02-12-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh libarchive-2017-01-04
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-libarchive-2017-01-04/lib \
    /build-cmplog/RUNDIR-aflpp_cmplog-libarchive-2017-01-04/libarchive-2017-01-04-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh libjpeg-turbo-07-2017
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-libjpeg-turbo-07-2017/lib \
    /build-cmplog/RUNDIR-aflpp_cmplog-libjpeg-turbo-07-2017/libjpeg-turbo-07-2017-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh libpng-1.2.56
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-libpng-1.2.56/lib         \
    /build-cmplog/RUNDIR-aflpp_cmplog-libpng-1.2.56/libpng-1.2.56-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh libxml2-v2.9.2
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-libxml2-v2.9.2/lib        \
    /build-cmplog/RUNDIR-aflpp_cmplog-libxml2-v2.9.2/libxml2-v2.9.2-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh pcre2-10.00
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-pcre2-10.00/lib           \
    /build-cmplog/RUNDIR-aflpp_cmplog-pcre2-10.00/pcre2-10.00-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh re2-2014-12-09
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-re2-2014-12-09/lib        \
    /build-cmplog/RUNDIR-aflpp_cmplog-re2-2014-12-09/re2-2014-12-09-aflpp_cmplog

RUN cd /build-cmplog && /fuzzer-test-suite/build.sh vorbis-2017-12-11
RUN get_libs.py -o /build-cmplog/RUNDIR-aflpp_cmplog-vorbis-2017-12-11/lib     \
    /build-cmplog/RUNDIR-aflpp_cmplog-vorbis-2017-12-11/vorbis-2017-12-11-aflpp_cmplog

# The `build` directory can be extracted to the host machine
RUN echo "\033[0;33m * Extract the '/build-aflpp', '/build-cmplog', and '/aflplusplus' directories\033[0m"
