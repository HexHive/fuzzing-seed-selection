#!/bin/bash -u

export THIS_DIR=$(dirname $(readlink -f $0))
export TARGET="/binutils-coverage/bin/readelf"
export TIMEOUT="1m"

function get_cov() {
    local QUEUE=$(realpath $1)
    local OUT_DIR=${QUEUE}
    local LLVM_COV_DIR=$(realpath "${QUEUE}/llvm_cov")
    local SEEDS_LIST="${LLVM_COV_DIR}/seeds.txt"

    timestamps_honggfuzz.py -o ${OUT_DIR}/timestamps.csv ${OUT_DIR}

    rm -f ${SEEDS_LIST}
    for SEED in $(ls -rt ${QUEUE}); do
        if [[ ${SEED} != *.honggfuzz.cov ]]; then
            continue
        fi

        echo "[*] processing ${SEED}"

        local SEED_PATH="${QUEUE}/${SEED}"
        export LLVM_PROFILE_FILE="${LLVM_COV_DIR}/${SEED}.profraw"

        timeout --preserve-status ${TIMEOUT} ${TARGET} -a ${SEED_PATH} > /dev/null 2>&1

        echo "1,${LLVM_PROFILE_FILE}" >> ${SEEDS_LIST}
        llvm-profdata-8 merge --sparse                              \
            --input-files "${LLVM_COV_DIR}/seeds.txt"               \
            --output "${LLVM_PROFILE_FILE%.profraw}.profdata"       \
            --num-threads=5

        llvm-cov-8 export --summary-only ${TARGET}                  \
            --instr-profile "${LLVM_PROFILE_FILE%.profraw}.profdata"\
            --format text --num-threads=5 > "${LLVM_PROFILE_FILE%.profraw}.json"
    done
}

export -f get_cov

find . -maxdepth 2 -path '*-honggfuzz/*-trial-*' -type d -print0 | parallel -0 -u get_cov {}
