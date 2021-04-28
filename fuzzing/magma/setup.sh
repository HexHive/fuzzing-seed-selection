#!/bin/bash -e

if [ "$#" -ne 1 ]; then
    echo "usage: $0 /dest/path"
    exit 1
fi

THIS_DIR=$(dirname $(realpath -s $0))
DEST_DIR=$1

rm -rf ${DEST_DIR}
git clone --branch v1.1 --depth 1 https://github.com/HexHive/magma ${DEST_DIR}
git -C ${DEST_DIR} apply "${THIS_DIR}/v1.1.patch"
cp "${THIS_DIR}/log-execs.patch" ${DEST_DIR}/fuzzers/afl/src/
cp "${THIS_DIR}/../../scripts/bin/timestamp_afl.py" ${DEST_DIR}/fuzzers/afl/src/timestamp_findings.py

# Create php corpus directories
mkdir -p ${DEST_DIR}/targets/php/corpus/{exif,json,parser}
