#!/bin/bash
# Copyright 2017 Google Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");

# Don't allow to call these scripts from their directories.
[ -e $(basename $0) ] && echo "PLEASE USE THIS SCRIPT FROM ANOTHER DIR" && exit 1

# Ensure that fuzzing engine, if defined, is valid
FUZZING_ENGINE=${FUZZING_ENGINE:-"afl"}
POSSIBLE_FUZZING_ENGINE="afl aflpp aflpp_cmplog coverage"
!(echo "$POSSIBLE_FUZZING_ENGINE" | grep -w "$FUZZING_ENGINE" > /dev/null) && \
  echo "USAGE: Error: If defined, FUZZING_ENGINE should be one of the following:
  $POSSIBLE_FUZZING_ENGINE. However, it was defined as $FUZZING_ENGINE" && exit 1

SCRIPT_DIR=$(dirname $(realpath -s $0))
EXECUTABLE_NAME_BASE=$(basename $SCRIPT_DIR)-${FUZZING_ENGINE}
LIBFUZZER_SRC=${LIBFUZZER_SRC:-$(dirname $(dirname $SCRIPT_DIR))/Fuzzer}
STANDALONE_TARGET=0
AFL_SRC=${AFL_SRC:-$(dirname $(dirname $SCRIPT_DIR))/AFL}
CORPUS=CORPUS-$EXECUTABLE_NAME_BASE
JOBS=${JOBS:-"8"}

export LIB_FUZZING_ENGINE="libFuzzingEngine-${FUZZING_ENGINE}.a"

if [[ $FUZZING_ENGINE == "afl" ]]; then
  export AFL_PATH=$(realpath -s ${AFL_SRC})

  export CC="${AFL_PATH}/afl-clang-fast"
  export CXX="${AFL_PATH}/afl-clang-fast++"

  export AFL_CC="clang-8"
  export AFL_CXX="clang++-8"

  export AFL_USE_ASAN="1"
  export CFLAGS="-m32 -O2 -fno-omit-frame-pointer -gline-tables-only"
  export CXXFLAGS="${CFLAGS}"
  export LDFLAGS="-m32"
elif [[ $FUZZING_ENGINE == "aflpp" ]]; then
  export AFL_PATH=$(realpath -s ${AFL_SRC})

  export CC="${AFL_PATH}/afl-clang-fast"
  export CXX="${AFL_PATH}/afl-clang-fast++"
  export AS="llvm-as-8"

  export AFL_CC="clang-8"
  export AFL_CXX="clang++-8"

  export AFL_USE_ASAN="1"
  export CFLAGS="-m32 -O2 -fno-omit-frame-pointer -gline-tables-only"
  export CXXFLAGS="${CFLAGS}"
  export LDFLAGS="-m32"
elif [[ $FUZZING_ENGINE == "aflpp_cmplog" ]]; then
  export AFL_PATH=$(realpath -s ${AFL_SRC})

  export CC="${AFL_PATH}/afl-clang-fast"
  export CXX="${AFL_PATH}/afl-clang-fast++"
  export AS="llvm-as-8"

  export AFL_CC="clang-8"
  export AFL_CXX="clang++-8"

  export AFL_LLVM_CMPLOG=1
  export CFLAGS="-m32 -O2 -fno-omit-frame-pointer -gline-tables-only"
  export CXXFLAGS="${CFLAGS}"
  export LDFLAGS="-m32"
elif [[ $FUZZING_ENGINE == "coverage" ]]; then
  export CC="clang-8"
  export CXX="clang++-8"

  export CFLAGS="-m32 -fprofile-instr-generate -fcoverage-mapping"
  export CXXFLAGS="${CFLAGS}"
  export LDFLAGS="-m32"
fi

export CPPFLAGS=${CPPFLAGS:-"-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION"}

get_git_revision() {
  GIT_REPO="$1"
  GIT_REVISION="$2"
  TO_DIR="$3"
  [ ! -e $TO_DIR ] && git clone $GIT_REPO $TO_DIR && (cd $TO_DIR && git reset --hard $GIT_REVISION)
}

get_git_tag() {
  GIT_REPO="$1"
  GIT_TAG="$2"
  TO_DIR="$3"
  [ ! -e $TO_DIR ] && git clone $GIT_REPO $TO_DIR && (cd $TO_DIR && git checkout $GIT_TAG)
}

get_svn_revision() {
  SVN_REPO="$1"
  SVN_REVISION="$2"
  TO_DIR="$3"
  [ ! -e $TO_DIR ] && svn co -r$SVN_REVISION $SVN_REPO $TO_DIR
}

build_afl() {
  $CXX $CXXFLAGS -std=c++11 -m32 -c ${LIBFUZZER_SRC}/afl/afl_driver.cpp -I$LIBFUZZER_SRC
  ar r $LIB_FUZZING_ENGINE afl_driver.o
  rm *.o
}

build_aflpp() {
  cp ${AFL_SRC}/examples/aflpp_driver/libAFLDriver.a $LIB_FUZZING_ENGINE
}

build_aflpp_cmplog() {
  build_aflpp
}

# This provides a build with no fuzzing engine, just to measure coverage
build_coverage () {
  STANDALONE_TARGET=1
  $CC -m32 -c $LIBFUZZER_SRC/standalone/StandaloneFuzzTargetMain.c
  ar rc $LIB_FUZZING_ENGINE StandaloneFuzzTargetMain.o
  rm *.o
}

build_fuzzer() {
  echo "Building with $FUZZING_ENGINE"
  build_${FUZZING_ENGINE}
}

