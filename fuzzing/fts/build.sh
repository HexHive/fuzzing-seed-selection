#!/bin/bash -x
# Copyright 2016 Google Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
. $(dirname $(realpath -s $0))/common.sh

if [ $# -ne 1 ]; then
    echo "usage: $0 TARGET"
    exit 1
fi

BUILD=$SCRIPT_DIR/$1/build.sh

[ ! -e $BUILD ] && echo "NO SUCH FILE: $BUILD" && exit 1

RUNDIR="RUNDIR-${FUZZING_ENGINE}-$1"
mkdir -p $RUNDIR
cd $RUNDIR
$BUILD

