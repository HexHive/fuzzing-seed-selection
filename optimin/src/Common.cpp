#include "Common.h"

void GetAFLCoverage(std::istream &IS, AFLCoverageVector &Cov) {
  std::string Line;

  while (std::getline(IS, Line, '\n')) {
    const size_t DelimPos = Line.find(':');
    const uint32_t E = std::stoul(Line.substr(0, DelimPos));
    const unsigned Freq = std::stoul(Line.substr(DelimPos + 1));

    Cov.push_back({E, Freq});
  }
}

void GetWeights(std::istream &IS, WeightsMap &Weights) {
  std::string Line;

  while (std::getline(IS, Line, '\n')) {
    const size_t DelimPos = Line.find(',');
    const std::string Seed = Line.substr(0, DelimPos).c_str();
    const unsigned Weight = std::stoul(Line.substr(DelimPos + 1));

    Weights.emplace(Seed, Weight);
  }
}

size_t GetNumSeeds(DIR *FD) {
  struct dirent *DP;
  size_t SeedCount = 0;

  while ((DP = readdir(FD)) != nullptr) {
    if (DP->d_type == DT_REG) {
      ++SeedCount;
    }
  }

  rewinddir(FD);

  return SeedCount;
}
