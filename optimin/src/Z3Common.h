#ifndef Z3_COMMON_H
#define Z3_COMMON_H

#include <map>
#include <string>
#include <unordered_set>

#include <boost/container/flat_map.hpp>
#include <z3++.h>

#include "Common.h"

/// Hash structure so a `z3::expr` can be stored in an `std::unordered_set`
struct Z3ExprHash {
  size_t operator()(const z3::expr &E) const noexcept {
    return std::hash<unsigned>()(E.hash());
  }
};

/// Set of Z3 expressions
using Z3ExprSet = std::unordered_set<z3::expr, Z3ExprHash>;

/// Maps tuple IDs to Z3 expressions that "cover" that tuple
using Z3CoverageMap =
    boost::container::flat_map<AFLTuple::first_type, Z3ExprSet>;

/// Get the seed name from a Z3 expression
std::string GetSeed(const z3::expr &);

/// Read a CSV file containing seed weights
void GetZ3Weights(std::istream &, WeightsMap &);

/// Create a name for a Z3 expression
std::string MakeZ3ExprName(const std::string &);

#endif // Z3_COMMON_H
