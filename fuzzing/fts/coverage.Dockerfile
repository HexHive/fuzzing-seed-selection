FROM seed-selection/fts/base

# Build coverage FTS
ENV FUZZING_ENGINE="coverage"
RUN mkdir /build-cov

RUN cd /build-cov && /fuzzer-test-suite/build.sh freetype2-2017
RUN get_libs.py -o /build-cov/RUNDIR-coverage-freetype2-2017/lib           \
    /build-cov/RUNDIR-coverage-freetype2-2017/freetype2-2017-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh guetzli-2017-3-30
RUN get_libs.py -o /build-cov/RUNDIR-coverage-guetzli-2017-3-30/lib        \
    /build-cov/RUNDIR-coverage-guetzli-2017-3-30/guetzli-2017-3-30-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh json-2017-02-12
RUN get_libs.py -o /build-cov/RUNDIR-coverage-json-2017-02-12/lib          \
    /build-cov/RUNDIR-coverage-json-2017-02-12/json-2017-02-12-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh libarchive-2017-01-04
RUN get_libs.py -o /build-cov/RUNDIR-coverage-libarchive-2017-01-04/lib    \
    /build-cov/RUNDIR-coverage-libarchive-2017-01-04/libarchive-2017-01-04-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh libjpeg-turbo-07-2017
RUN get_libs.py -o /build-cov/RUNDIR-coverage-libjpeg-turbo-07-2017/lib    \
    /build-cov/RUNDIR-coverage-libjpeg-turbo-07-2017/libjpeg-turbo-07-2017-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh libpng-1.2.56
RUN get_libs.py -o /build-cov/RUNDIR-coverage-libpng-1.2.56/lib            \
    /build-cov/RUNDIR-coverage-libpng-1.2.56/libpng-1.2.56-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh libxml2-v2.9.2
RUN get_libs.py -o /build-cov/RUNDIR-coverage-libxml2-v2.9.2/lib           \
    /build-cov/RUNDIR-coverage-libxml2-v2.9.2/libxml2-v2.9.2-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh pcre2-10.00
RUN get_libs.py -o /build-cov/RUNDIR-coverage-pcre2-10.00/lib              \
    /build-cov/RUNDIR-coverage-pcre2-10.00/pcre2-10.00-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh re2-2014-12-09
RUN get_libs.py -o /build-cov/RUNDIR-coverage-re2-2014-12-09/lib           \
    /build-cov/RUNDIR-coverage-re2-2014-12-09/re2-2014-12-09-coverage

RUN cd /build-cov && /fuzzer-test-suite/build.sh vorbis-2017-12-11
RUN get_libs.py -o /build-cov/RUNDIR-coverage-vorbis-2017-12-11/lib        \
    /build-cov/RUNDIR-coverage-vorbis-2017-12-11/vorbis-2017-12-11-coverage

RUN echo "\033[0;33m * Extract the 'build-cov' directory\033[0m"
