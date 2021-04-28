#!/bin/bash -e

if [ "$#" -ne 1 ]; then
    echo "usage: $0 /path/to/magma"
    exit 1
fi

MAGMA_DIR=$1

set -x
rm -rf ${MAGMA_DIR}/targets/libpng/corpus/libpng_read_fuzzer/*
rm -rf ${MAGMA_DIR}/targets/libtiff/corpus/tiff_read_rgba_fuzzer/*
rm -rf ${MAGMA_DIR}/targets/libxml2/corpus/libxml2_xml_reader_for_file_fuzzer/*
rm -rf ${MAGMA_DIR}/targets/php/corpus/{exif,json,parser}/*
rm -rf ${MAGMA_DIR}/targets/poppler/corpus/pdf_fuzzer/*
