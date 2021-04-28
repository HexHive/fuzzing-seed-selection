#!/bin/bash -e

NUM_TRIALS=5
TRIAL_LEN=$((10*60*60))
NUM_CORES=$(grep -c ^processor /proc/cpuinfo)
SEM_ID="readelf-fuzz"

export AFL_NO_UI=1

# AFLFast
mkdir /readelf-aflfast
for TRIAL in $(seq 1 ${NUM_TRIALS}); do
    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /aflfast/afl-fuzz -p fast -i /uninformed-seed                       \
        -o /readelf-aflfast/uninformed-trial-${TRIAL} --                \
        /binutils-aflfast/bin/readelf -a @@ > /dev/null
    sleep 2s

    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /aflfast/afl-fuzz -p fast -i /aflfast/testcases/others/elf          \
        -o /readelf-aflfast/singleton-trial-${TRIAL} --                 \
        /binutils-aflfast/bin/readelf -a @@ > /dev/null
    sleep 2s

    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /aflfast/afl-fuzz -p fast -i /cmin-seeds                            \
        -o /readelf-aflfast/cmin-trial-${TRIAL} --                      \
        /binutils-aflfast/bin/readelf -a @@ > /dev/null
    sleep 2s
done

# AFL++
mkdir /readelf-aflplusplus
for TRIAL in $(seq 1 ${NUM_TRIALS}); do
    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /aflplusplus/afl-fuzz -i /uninformed-seed                           \
        -o /readelf-aflplusplus/uninformed-trial-${TRIAL}               \
        -m none -c /binutils-aflplusplus/cmplog/bin/readelf --          \
        /binutils-aflplusplus/afl/bin/readelf -a @@ > /dev/null
    sleep 2s

    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /aflplusplus/afl-fuzz -i /aflfast/testcases/others/elf              \
        -o /readelf-aflplusplus/singleton-trial-${TRIAL}                \
        -m none -c /binutils-aflplusplus/cmplog/bin/readelf --          \
        /binutils-aflplusplus/afl/bin/readelf -a @@ > /dev/null
    sleep 2s

    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /aflplusplus/afl-fuzz -i /cmin-seeds                                \
        -o /readelf-aflplusplus/cmin-trial-${TRIAL}                     \
        -m none -c /binutils-aflplusplus/cmplog/bin/readelf --          \
        /binutils-aflplusplus/afl/bin/readelf -a @@ > /dev/null
    sleep 2s
done

# honggfuzz
mkdir readelf-honggfuzz
for TRIAL in $(seq 1 ${NUM_TRIALS}); do
    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u            \
        --halt now,fail=1                                                       \
    /honggfuzz/honggfuzz --threads 1 --quiet -z -q -v                           \
        -i /uninformed-seed -o /readelf-honggfuzz/uninformed-trial-${TRIAL}     \
        -- /binutils-honggfuzz/bin/readelf -a ___FILE___ > /dev/null
    sleep 2s

    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /honggfuzz/honggfuzz --threads 1 --quiet -z -q -v                   \
        -i /aflfast/testcases/others/elf                                \
        -o /readelf-honggfuzz/singleton-trial-${TRIAL}                  \
        -- /binutils-honggfuzz/bin/readelf -a ___FILE___ > /dev/null
    sleep 2s

    sem --timeout ${TRIAL_LEN} --jobs ${NUM_CORES} --id ${SEM_ID} -u    \
        --halt now,fail=1                                               \
    /honggfuzz/honggfuzz --threads 1 --quiet -z -q -v                   \
        -i /cmin-seeds                                                  \
        -o /readelf-honggfuzz/cmin-trial-${TRIAL}                       \
        -- /binutils-honggfuzz/bin/readelf -a ___FILE___ > /dev/null
    sleep 2s
done

# Wait for fuzzers to finish
sem --wait --id ${SEM_ID}
