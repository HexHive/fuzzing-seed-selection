/**
 * Perform an optimal (if possible) fuzzing corpus minimization based on
 * afl-showmap's edge coverage.
 *
 * Author: Adrian Herrera
 */

#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <dirent.h>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <unistd.h>
#include <vector>

#include <boost/container/flat_map.hpp>
#include <boost/container/flat_set.hpp>

#include "Common.h"
#include "ProgressBar.h"

// This is based on the human class count in `count_class_human[256]` in
// `afl-showmap.c`
static constexpr uint32_t MAX_EDGE_FREQ = 8;

/// Maps WCNF literal identifiers (integers) to seed files
using MaxSatMap = boost::container::flat_map<unsigned, std::string>;

/// Set of WCNF literals
using MaxSatLiteralSet = boost::container::flat_set<unsigned>;

/// Maps tuple IDs to WCNF literals that "cover" that tuple
using MaxSatCoverageMap =
    boost::container::flat_map<AFLTuple::first_type, MaxSatLiteralSet>;

static void Usage(const char *Argv0) {
  std::cerr << '\n' << Argv0 << " [ options ] -- /path/to/corpus_dir\n\n";
  std::cerr << "Required parameters:\n\n";
  std::cerr << "  -o         - Output WCNF (DIMACS) file\n\n";
  std::cerr << "Optional parameters:\n\n";
  std::cerr << "  -p         - Show progress bar\n";
  std::cerr << "  -e         - Use edge coverage only, ignore hit counts\n";
  std::cerr << "  -h         - Print this message\n";
  std::cerr << "  -w weights - CSV containing seed weights (see README)\n\n";
  std::cerr << std::endl;

  std::exit(1);
}

int main(int Argc, char *Argv[]) {
  bool ShowProg = false;
  bool EdgesOnly = false;
  std::string WCNFOutFile;
  std::string WeightsFile;
  WeightsMap Weights;
  int Opt;
  ProgressBar Prog;

  std::chrono::time_point<std::chrono::steady_clock> StartTime, EndTime;
  std::chrono::seconds Duration;

  std::cout << "afl-showmap corpus minimization\n\n";

  // Parse command-line options
  while ((Opt = getopt(Argc, Argv, "+peho:w:")) > 0) {
    switch (Opt) {
    case 'p':
      // Show progres bar
      ShowProg = true;
      break;
    case 'e':
      // Solve for edge coverage only (not frequency of edge coverage)
      EdgesOnly = true;
      break;
    case 'h':
      // Help
      Usage(Argv[0]);
      break;
    case 'o':
      // WCNF file
      WCNFOutFile = optarg;
      break;
    case 'w':
      // Weights file
      WeightsFile = optarg;
      break;
    default:
      Usage(Argv[0]);
    }
  }

  if (optind >= Argc) {
    Usage(Argv[0]);
  }

  if (WCNFOutFile.empty()) {
    Usage(Argv[0]);
  }

  const char *CorpusDir = Argv[optind];

  // Parse weights
  //
  // Weights are stored in CSV file mapping a seed file name to an integer
  // greater than zero.
  if (!WeightsFile.empty()) {
    std::cout << "[*] Reading weights from `" << WeightsFile << "`... "
              << std::flush;
    StartTime = std::chrono::steady_clock::now();

    std::ifstream IFS(WeightsFile);
    GetWeights(IFS, Weights);
    IFS.close();

    EndTime = std::chrono::steady_clock::now();
    Duration =
        std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
    std::cout << Duration.count() << 's' << std::endl;
  }

  // Calculate the top value
  //
  // This top value is the weight assigned to "hard clauses", and is
  // typically calculated as the sum of all possible weights (per
  // https://maxsat-evaluations.github.io/2020/format.html). Soft clauses have
  // always be less than top.
  if (!ShowProg) {
    std::cout << "[*] Calculating top... " << std::flush;
  }
  StartTime = std::chrono::steady_clock::now();

  size_t WeightCount = 0;
  uint64_t Top = Weights.empty() ? 2 : 1;
  for (const auto &[_, W] : Weights) {
    Top += W;

    // Check for unsigned integer overflow
    if (Top < W) {
      std::cerr << "Top has overflowed. Aborting" << std::endl;
      std::abort();
    }

    if ((++WeightCount % 10 == 0) && ShowProg) {
      Prog.Update(WeightCount * 100 / Weights.size(), "Calculating top");
    }
  }

  EndTime = std::chrono::steady_clock::now();
  Duration =
      std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
  if (ShowProg) {
    std::cout << std::endl;
  } else {
    std::cout << Duration.count() << 's' << std::endl;
  }

  // Get seed coverage
  //
  // Iterate over the corpus directory, which should contain afl-showmap-style
  // output files. Read each of these files and store them in the appropriate
  // data structures.
  struct dirent *DP;
  DIR *DirFD;
  AFLCoverageVector Cov;

  MaxSatMap SeedLiterals;
  MaxSatCoverageMap SeedCoverage;

  if (!ShowProg) {
    std::cout << "[*] Reading coverage in `" << CorpusDir << "`... "
              << std::flush;
  }
  StartTime = std::chrono::steady_clock::now();

  if ((DirFD = opendir(CorpusDir)) == nullptr) {
    std::cerr << "[-] Unable to open corpus directory" << std::endl;
    return 1;
  }

  size_t SeedCount = 0;
  const size_t NumSeeds = GetNumSeeds(DirFD);

  while ((DP = readdir(DirFD)) != nullptr) {
    if (DP->d_type == DT_DIR) {
      continue;
    }

    // Get seed coverage
    std::ifstream IFS(std::string(CorpusDir) + '/' + DP->d_name);
    Cov.clear();
    GetAFLCoverage(IFS, Cov);
    IFS.close();

    // Create a literal (an integer) to represent the seed
    const unsigned SeedLit = SeedCount + 1;
    SeedLiterals.emplace(SeedLit, DP->d_name);

    // Record the set of seeds that cover a particular edge
    for (const auto &[Edge, Freq] : Cov) {
      if (EdgesOnly) {
        // Ignore edge frequency
        SeedCoverage[Edge].insert(SeedLit);
      } else {
        // Executing edge `E` `N` times means that it was executed `N - 1` times
        for (unsigned I = 0; I < Freq; ++I)
          SeedCoverage[MAX_EDGE_FREQ * Edge + I].insert(SeedLit);
      }
    }

    if ((++SeedCount % 10 == 0) && ShowProg) {
      Prog.Update(SeedCount * 100 / NumSeeds, "Reading seed coverage");
    }
  }

  closedir(DirFD);

  EndTime = std::chrono::steady_clock::now();
  Duration =
      std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
  if (ShowProg) {
    std::cout << std::endl;
  } else {
    std::cout << Duration.count() << 's' << std::endl;
  }

  // Ensure that at least one seed is selected that covers a particular edge
  // (hard constraint)
  if (!ShowProg) {
    std::cout << "[*] Generating clauses... " << std::flush;
  }
  StartTime = std::chrono::steady_clock::now();

  SeedCount = 0;
  boost::container::flat_set<MaxSatLiteralSet> Clauses;

  for (const auto &[_, Seeds] : SeedCoverage) {
    if (Seeds.empty()) {
      continue;
    }

    Clauses.insert(Seeds);

    if ((++SeedCount % 10 == 0) && ShowProg) {
      Prog.Update(SeedCount * 100 / SeedCoverage.size(), "Generating clauses");
    }
  }

  EndTime = std::chrono::steady_clock::now();
  Duration =
      std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
  if (ShowProg) {
    std::cout << std::endl;
  } else {
    std::cout << Duration.count() << 's' << std::endl;
  }

  // Now we actually generated the weighted conjunctive normal form (WCNF). This
  // format is similar to the DIMACS CNF format, and is described at
  // https://maxsat-evaluations.github.io/2020/rules.html#input

  // Write WCNF header
  std::ofstream OFS(WCNFOutFile);
  OFS << "c corpus dir: " << CorpusDir << "\nc" << std::endl;
  for (const auto &[Literal, Seed] : SeedLiterals) {
    OFS << "c " << Literal << " : " << Seed << std::endl;
  }
  OFS << "c" << std::endl;
  OFS << "p wcnf " << SeedLiterals.size() << ' '
      << Clauses.size() + SeedLiterals.size() << ' ' << Top << std::endl;

  // Write clauses
  for (const auto &Clause : Clauses) {
    OFS << Top << ' ';
    for (const auto &Seed : Clause) {
      OFS << Seed << ' ';
    }
    OFS << 0 << std::endl;
  }

  // Select the minimum number of seeds that cover a particular set of edges
  // (soft constraint)
  for (const auto &[Literal, Seed] : SeedLiterals) {
    OFS << Weights[Seed] << " -" << Literal << ' ' << 0 << std::endl;
  }
  OFS.close();

  return 0;
}
