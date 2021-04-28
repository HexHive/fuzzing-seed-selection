#ifndef COMMON_H
#define COMMON_H

#include <cstdint>
#include <dirent.h>
#include <istream>
#include <map>
#include <string>
#include <vector>

/// Seed weights default to 1
class WeightT {
public:
  WeightT() : WeightT(1){};
  WeightT(uint32_t V) : Value(V){};

  operator unsigned() const { return Value; }

private:
  const unsigned Value;
};

/// Pair of tuple (edge) ID and hit count
using AFLTuple =
    std::pair</* Tuple ID */ uint32_t, /* Execution count */ unsigned>;

/// Coverage for a given seed file
using AFLCoverageVector = std::vector<AFLTuple>;

/// Maps seed file paths to a weight
using WeightsMap =
    std::map</* Seed file */ std::string, /* Seed weight */ WeightT>;

/// Read AFL coverage as produced by `afl-showmap`
void GetAFLCoverage(std::istream &, AFLCoverageVector &);

/// Read a CSV file containing seed weights
void GetWeights(std::istream &, WeightsMap &);

/// Get the number of seeds in a directory
size_t GetNumSeeds(DIR *);

#endif // COMMON_H
