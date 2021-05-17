# Seed Selection Tools

A collection of scripts to help with analyzing fuzzing seed selection practices.

## afl_cmin.py

A wrapper around [`afl-cmin`](https://github.com/google/AFL/blob/master/afl-cmin)
that prints the seeds selected (but does not copy them).

## afl_coverage_merge.py

Merge the [final coverage bitmaps](https://github.com/google/AFL/blob/master/afl-fuzz.c#L863)
from multiple AFL parallel nodes.

## afl_coverage_pca.py

Generate a [PCA](https://en.wikipedia.org/wiki/Principal_component_analysis)
plot for a given seed set (stored in an HDF5 file, such as those stored on
[OSF](https://osf.io/hz8em)).

## coverage_auc.py

Compute the area under curve (AUC) of AFL coverage data (stored in `plot_data`
files).

## eval_maxsat.py

Run [EvalMaxSAT](https://github.com/FlorentAvellaneda/EvalMaxSAT) over a WCNF
produced by `afl-showmap-maxsat` to compute an optimum corpus.

## expand_hdf5_coverage.py

Extract [`afl-showmap`](https://github.com/google/AFL/blob/master/afl-showmap.c)
style bitmaps from an HDF5 file containing AFL coverage (as stored on
[OSF](https://osf.io/hz8em/)).

## fuzz.py

Run multiple AFL campaigns in parallel. Ensures that CPU-usage is properly
managed and optionally provides a watchdog that timestamps artifacts created by
AFL (e.g., crashes, queue entries).

## get_corpus.py

Download a corpus of seeds from [cloudstor](https://cloudstor.aarnet.edu.au/)
based on a given minimization technique (e.g., optimal, afl-cmin).

## get_libs.py

Extract all shared libraries that a given program depends on and copy these
libraries to a particular directory.

## llvm_cov_merge.py

Merge LLVM [SanitizerCoverage](https://clang.llvm.org/docs/SanitizerCoverage.html).

## qminset.py

Wraps the MinSet tool as proposed in the [Optimizing Seed Selection for
Fuzzing](https://www.usenix.org/conference/usenixsecurity14/technical-sessions/presentation/rebert)
paper. Prints the selected seeds.

## replay_seeds.py

Replay a directory of inputs seeds and generate coverage information. This
coverage information is stored in an HDF5 (as stored on
[OSF](https://osf.io/hz8em)).

## triage_crashes.py

Replay AFL's `crashes` directory and match crash outputs to a regex (e.g., such
as those provided [here](../fuzzing/config/fts-bug-regexs.toml).

## visualize_corpora.py

Plot a "Venn diagram" (it's not really a Venn diagram) of different minimized
corpora.
