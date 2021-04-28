# Fuzzing Targets

This directory contains build scripts for building the targets fuzzed in the
paper. Like in the paper, we group the targets into three benchmarks: Magma,
the Google Fuzzer Test Suite (FTS), and a set of real-world programs.

Note: AFL typically requires that coredumps be disabled:

```bash
sudo bash -c 'echo core >/proc/sys/kernel/core_pattern'
sudo systemctl disable apport.service
```

## Magma

[Magma](https://hexhive.epfl.ch/magma) is a ground-truth fuzzing benchmark. To
build:

1. Install dependencies, as described [here](https://hexhive.epfl.ch/magma/docs/getting-started.html)
1. Run `./magma/setup.sh /magma/benchmark/dir`
1. Clean out the default corpora `./magma/clean_corpora.sh /magma/benchmark/dir`
1. Copy the relevant `TARGET` corpus into
   `/magma/benchmark/dir/targets/TARGET/corpus/PROGRAM`. You can either distill
   your own corpus or use one that we have already prepared. For the former,
   see the [Run OptiMin](../README.md#run-optimin) instructions. For the latter,
   use the [`get_corpus.py`](../scripts/bin/get_corpus.py) script. E.g., to
   download the `afl-cmin`-minimized libpng corpus (this can take up to 15-20
   mins):

   ```bash
   get_corpus.py --benchmark magma --corpus cmin --log info --target libpng \
     /magma/benchmark/dir/targets/libpng/corpus/libpng_read_fuzzer
   ```
1. Set `WORKDIR` in `/magma/benchmark/dir/tools/captain/captainrc` to something
   appropriate. If you only want to fuzz a single target (e.g., libpng), edit
   the `afl_TARGETS`/`aflplusplus_TARGETS` entry in `captainrc`
1. Start fuzzing!

   ```bash
   cd /magma/benchmark/dir/tools/captain
   ./run.sh
   ```
1. [This](https://github.com/HexHive/magma/blob/dev/tools/benchd/survival_analysis.py)
   Magma script can be used to perform the survival analysis on the results

## FTS

The [Google Fuzzer Test Suite](https://github.com/google/fuzzer-test-suite) is
a widely-used fuzzing benchmark.

1. Build the base image

   ```bash
   docker build -t seed-selection/fts/base -f fts/base.Dockerfile fts
   ```
1. Build the FTS targets with the required `$INSTRUMENTATION` (one of `afl`,
   `aflpp`, or `coverage`)

   ```bash
   docker build -t seed-selection/fts/$INSTRUMENTATION  \
     -f fts/$INSTRUMENTATION.Dockerfile fts
   ```
1. Extract the relevant files for fuzzing, as instructed at the end of the
   previous step. E.g., for AFL++

   ```bash
   ./extract-from-container.sh seed-selection/fts/$INSTRUMENTATION /aflplusplus .
   ./extract-from-container.sh seed-selection/fts/$INSTRUMENTATION /build-aflpp .
   ./extract-from-container.sh seed-selection/fts/$INSTRUMENTATION /build-cmplog .
   ```
1. Create a fuzzing corpus using the
   [`get_corpus.py`](../scripts/bin/get_corpus.py) script
1. Start fuzzing. The runtime fuzzer configurations (e.g., timeouts and memory
   limits) that we used are stored [here](config/targets.toml). The `fuzz.py`
   script (in `scripts/bin`) can be used to launch multiple campaigns in
   parallel. For example, to fuzz FreeType2 with AFL++ and the provided seeds:

   ```bash
   LD_LIBRARY_PATH=$(pwd)/build-aflpp/RUNDIR-aflpp-freetype2-2017/lib   \
     fuzz.py -i $(pwd)/build-aflpp/RUNDIR-aflpp-freetype2-2017/seeds    \
     -o fuzz-out -n2 --num-trials 30 --trial-len $((18*60*60))          \
     --cmp-log $(pwd)/build-aflpp_cmplog/RUNDIR-aflpp_cmplog-freetype2-2017/freetype2-2017-aflpp_cmplog \
     $(pwd)/build-aflpp/RUNDIR-aflpp-freetype2-2017/freetype2-2017-aflpp
   ```
1. We use the regexs [here](config/fts-bug-regexs.toml) to determine each
   crash's root cause.

## Real-world Targets

A set of real-world programs.

1. Build the base image for a given `$TARGET` (e.g., sox, freetype)

   ```bash
   docker build -t seed-selection/real-world/$TARGET/base       \
     -f real-world/$TARGET/base.Dockerfile real-world/$TARGET
   ```
1. Build the target with the required `$INSTRUMENTATION`

   ```bash
   docker build -t seed-selection/real-world/$TARGET/$INSTRUMENTATION   \
     -f real-world/$TARGET/$INSTRUMENTATION.Dockerfile                  \
     real-world/$TARGET
   ```
1. Extract the relevant files for fuzzing, using the `extract-from-container.sh`
   script
1. Create a fuzzing corpus using the
   [`get_corpus.py`](../scripts/bin/get_corpus.py) script
1. Start fuzzing. Again, the `fuzz.py` script can be used.

## `readelf`

To reproduce the `readelf` experiment (Section 3.1 of the paper):

1. Build the Docker image

   ```bash
   docker build -t seed-selection/readelf readelf
   ```
1. Start the container, run the fuzzers, and process the results

   ```bash
   docker run -ti --rm seed-selection/readelf
   
   # Execute the following commands inside the Docker container
   
   ./fuzz.sh
   
   ./get_afl_cov.sh
   ./get_hfuzz_cov.sh
   
   ./merge_cov.py 
   ./plot_cov.py
   ```

## Generating LLVM Code Coverage

We use LLVM's [source-code-level
coverage](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html) in our
evaluation. To generate LLVM coverage after a fuzzing campaign:

1. Build the target with LLVM's coverage instrumentation. For Magma, this
   requires building with the `llvm_cov` fuzzer. For the FTS and real-world
   targets, build with the `coverage` Dockerfile.
1. Replay the final fuzzing queue (in AFL, this is the `queue` output directory)
   using the [`llvm_cov_merge`](../scripts/bin/llvm_cov_merge.py) script
1. Summarize the results using
   [`llvm_cov_stats`](../scripts/bin/llvm_cov_stats.py)
