/**
 * Perform an optimal (if possible) fuzzing corpus minimization based on
 * afl-showmap's edge coverage.
 *
 * Author: Adrian Herrera
 */

#include <chrono>
#include <cstdint>
#include <dirent.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <numeric>
#include <unistd.h>
#include <vector>

#include "Common.h"
#include "ProgressBar.h"
#include "Z3Common.h"

#include <z3++.h>

// This is based on the human class count in `count_class_human[256]` in
// `afl-showmap.c`
static constexpr uint32_t MAX_EDGE_FREQ = 8;

static void Usage(const char *Argv0) {
  std::cerr << '\n' << Argv0 << " [ options ] -- /path/to/corpus_dir\n\n";
  std::cerr << "Optional parameters:\n\n";
  std::cerr << "  -p         - Show progress bar\n";
  std::cerr << "  -e         - Use edge coverage only, ignore hit counts\n";
  std::cerr << "  -h         - Print this message\n";
  std::cerr << "  -s smt2    - Save SMT2\n";
  std::cerr << "  -w weights - CSV containing seed weights (see README)\n\n";
  std::cerr << std::endl;

  std::exit(1);
}

int main(int Argc, char *Argv[]) {
  bool ShowProg = false;
  bool EdgesOnly = false;
  std::string SMTOutFile = "";
  std::string WeightsFile;
  WeightsMap Weights;
  int Opt;
  ProgressBar Prog;

  std::chrono::time_point<std::chrono::steady_clock> StartTime, EndTime;
  std::chrono::seconds Duration;

  std::cout << "afl-showmap corpus minimization\n\n";

  // Parse command-line options
  while ((Opt = getopt(Argc, Argv, "+pehs:w:")) > 0) {
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
    case 's':
      // SMT2 file
      SMTOutFile = optarg;
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
    GetZ3Weights(IFS, Weights);
    IFS.close();
    EndTime = std::chrono::steady_clock::now();
    Duration =
        std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);

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

  Z3ExprSet SeedExprs;
  Z3CoverageMap SeedCoverage;

  z3::context Ctx;
  z3::optimize Optimizer(Ctx);

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

    // Create a variable (a boolean) to represent the seed
    z3::expr SeedExpr = Ctx.bool_const(MakeZ3ExprName(DP->d_name).c_str());
    SeedExprs.insert(SeedExpr);

    // Record the set of seeds that cover a particular edge
    for (const auto &[Edge, Freq] : Cov) {
      if (EdgesOnly) {
        // Ignore edge frequency
        SeedCoverage[Edge].insert(SeedExpr);
      } else {
        // Executing edge `E` `N` times means that it was executed `N - 1` times
        for (unsigned I = 0; I < Freq; ++I)
          SeedCoverage[MAX_EDGE_FREQ * Edge + I].insert(SeedExpr);
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
  if (!ShowProg) {
    std::cout << "[*] Generating constraints for " << SeedCoverage.size()
              << " seeds... " << std::flush;
  }
  StartTime = std::chrono::steady_clock::now();

  SeedCount = 0;

  for (const auto &[_, Seeds] : SeedCoverage) {
    if (Seeds.empty()) {
      continue;
    }

    z3::expr EdgeDisjunc = std::accumulate(
        Seeds.begin(), Seeds.end(), Ctx.bool_val(false),
        [](const z3::expr &E1, const z3::expr &E2) { return E1 || E2; });
    Optimizer.add(EdgeDisjunc);

    if ((++SeedCount % 10 == 0) && ShowProg) {
      Prog.Update(SeedCount * 100 / SeedCoverage.size(),
                  "Generating seed constraints");
    }
  }

  // Select the minimum number of seeds that cover a particular set of edges
  for (const auto &E : SeedExprs) {
    Optimizer.add(!E, Weights[E.to_string()]);
  }

  EndTime = std::chrono::steady_clock::now();
  Duration =
      std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
  if (ShowProg) {
    std::cout << std::endl;
  } else {
    std::cout << Duration.count() << 's' << std::endl;
  }

  // Dump constraints to SMT2
  if (!SMTOutFile.empty()) {
    std::cout << "[*] Writing SMT2 to `" << SMTOutFile << "`... " << std::flush;
    StartTime = std::chrono::steady_clock::now();

    std::ofstream OFS(SMTOutFile);
    OFS << Optimizer;
    OFS.close();

    EndTime = std::chrono::steady_clock::now();
    Duration =
        std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
    std::cout << Duration.count() << 's' << std::endl;
  }

  // Check if an optimal solution exists
  std::cout << "[*] Solving constraints... " << std::flush;
  StartTime = std::chrono::steady_clock::now();

  z3::check_result Result = Optimizer.check();

  EndTime = std::chrono::steady_clock::now();
  Duration =
      std::chrono::duration_cast<std::chrono::seconds>(EndTime - StartTime);
  std::cout << Duration.count() << 's' << std::endl;

  // Get the resulting coverset
  if (Result == z3::sat) {
    std::cout << "[+] Optimal corpus found\n";

    z3::model Model = Optimizer.get_model();
    std::vector<std::string> SelectedSeeds;
    for (const auto &SeedExpr : SeedExprs) {
      if (Model.eval(SeedExpr).is_true()) {
        SelectedSeeds.push_back(GetSeed(SeedExpr));
      }
    }

    // Compute some interesting statistics
    size_t NumSelectedSeeds = SelectedSeeds.size();
    float PercentSelected = (float)NumSelectedSeeds / SeedExprs.size() * 100.0;

    std::cout << "\nNum. seeds: " << NumSelectedSeeds << " (" << PercentSelected
              << "%)\n\n";
    std::copy(SelectedSeeds.begin(), SelectedSeeds.end(),
              std::ostream_iterator<std::string>(std::cout, "\n"));
    std::cout << std::endl;
  } else {
    std::cerr << "[- ]Unable to find optimal minimized corpus" << std::endl;
    return 1;
  }

  return 0;
}
