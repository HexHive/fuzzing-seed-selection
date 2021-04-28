/**
 * Perform an optimal (if possible) fuzzing corpus minimization based on
 * llvm-cov's JSON coverage report.
 *
 * Author: Adrian Herrera
 */

#include <chrono>
#include <dirent.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <numeric>
#include <unistd.h>
#include <unordered_map>
#include <vector>

#include "Common.h"
#include "ProgressBar.h"
#include "Z3Common.h"
#include "json/json.h"

#include <z3++.h>

namespace {

/// Based on LLVM's CoverageMapping (see
/// llvm/include/llvm/ProfileData/Coverage/CoverageMapping.h).
struct CountedRegion {
  enum RegionKind { CodeRegion, ExpansionRegion, SkippedRegion, GapRegion };

  const uint64_t Count;
  const unsigned FileID, ExpandedFileID;
  const unsigned LineStart, ColumnStart, LineEnd, ColumnEnd;
  const RegionKind Kind;

  CountedRegion(uint64_t Count, unsigned FileID, unsigned ExpandedFileID,
                unsigned LineStart, unsigned ColumnStart, unsigned LineEnd,
                unsigned ColumnEnd, RegionKind Kind)
      : Count(Count), FileID(FileID), ExpandedFileID(ExpandedFileID),
        LineStart(LineStart), ColumnStart(ColumnStart), LineEnd(LineEnd),
        ColumnEnd(ColumnEnd), Kind(Kind) {}

  // See renderRegion in llvm/tools/llvm-cov/CoverageExporterJson.cpp
  CountedRegion(const Json::Value &V)
      : Count(V[4].asUInt()), FileID(V[5].asUInt()),
        ExpandedFileID(V[6].asUInt()), LineStart(V[0].asUInt()),
        ColumnStart(V[1].asUInt()), LineEnd(V[2].asUInt()),
        ColumnEnd(V[3].asUInt()), Kind(RegionKind(V[7].asUInt())) {}

  bool operator==(const CountedRegion &O) const {
    return Count == O.Count && FileID == O.FileID &&
           ExpandedFileID == O.ExpandedFileID && LineStart == O.LineStart &&
           ColumnStart == O.ColumnStart && LineEnd == O.LineEnd &&
           ColumnEnd == O.ColumnEnd && Kind == O.Kind;
  }

  // Ignore execution counts
  static CountedRegion MakeUncounted(const CountedRegion &R) {
    return CountedRegion(R.Count > 0 ? 1 : 0, R.FileID, R.ExpandedFileID,
                         R.LineStart, R.ColumnStart, R.LineEnd, R.ColumnEnd,
                         R.Kind);
  }
};

struct CountedRegionHash {
  std::size_t operator()(const CountedRegion &R) const noexcept {
    std::size_t res = 17;
    res = res * 31 + std::hash<uint64_t>()(R.Count);
    res = res * 31 + std::hash<unsigned>()(R.FileID);
    res = res * 31 + std::hash<unsigned>()(R.ExpandedFileID);
    res = res * 31 + std::hash<unsigned>()(R.LineStart);
    res = res * 31 + std::hash<unsigned>()(R.ColumnStart);
    res = res * 31 + std::hash<unsigned>()(R.LineEnd);
    res = res * 31 + std::hash<unsigned>()(R.ColumnEnd);
    res = res * 31 + std::hash<unsigned>()(R.Kind);
    return res;
  }
};
} // anonymous namespace

using CountedRegionVector = std::vector<CountedRegion>;
using Z3RegionMap =
    std::unordered_map<CountedRegion, Z3ExprSet, CountedRegionHash>;

static void ParseJSON(std::istream &IS, CountedRegionVector &Regions) {
  Json::Value Root;
  IS >> Root;
  assert(Root["data"].size() == 1);
  Json::Value Functions = Root["data"][0]["functions"];

  for (const auto &Func : Functions)
    for (const auto &V : Func["regions"]) {
      CountedRegion Region(V);
      if (Region.Count > 0 &&
          Region.Kind == CountedRegion::RegionKind::CodeRegion) {
        Regions.push_back(Region);
      }
    }
}

static void Usage(const char *Argv0) {
  std::cerr << '\n' << Argv0 << " [ options ] -- /path/to/corpus_dir\n\n";
  std::cerr << "Optional parameters:\n\n";
  std::cerr << "  -p         - Show progress bar\n";
  std::cerr << "  -r         - Use region coverage only, ignore counts\n";
  std::cerr << "  -h         - Print this message\n";
  std::cerr << "  -s smt2    - Save SMT2\n";
  std::cerr << "  -w weights - CSV containing seed weights (see README)\n\n";
  std::cerr << std::endl;

  std::exit(1);
}

int main(int Argc, char *Argv[]) {
  bool ShowProg = false;
  bool RegionsOnly = false;
  std::string SMTOutFile = "";
  std::string WeightsFile;
  WeightsMap Weights;
  int Opt;
  ProgressBar Prog;

  std::chrono::time_point<std::chrono::steady_clock> StartTime, EndTime;
  std::chrono::seconds Duration;

  std::cout << "llvm-cov corpus minimization\n\n";

  // Parse command-line options
  while ((Opt = getopt(Argc, Argv, "+prhs:w:")) > 0) {
    switch (Opt) {
    case 'p':
      // Show progress bar
      ShowProg = true;
      break;
    case 'r':
      // Solve for region coverage only (not region counts)
      RegionsOnly = true;
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

  const char *CorpusDir = Argv[optind];
  DIR *DirFD;
  struct dirent *DP;
  CountedRegionVector Cov;

  Z3ExprSet SeedExprs;
  Z3RegionMap SeedCoverage;

  z3::context Ctx;
  z3::optimize Optimizer(Ctx);

  // Get seed coverage
  //
  // Iterate over the corpus directory, which should contain llvm-cov-style
  // JSON files. Read each of these files and store them in the appropriate
  // data structures.
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
  size_t NumSeeds = GetNumSeeds(DirFD);

  while ((DP = readdir(DirFD)) != nullptr) {
    if (DP->d_type == DT_DIR) {
      continue;
    }

    // Get seed coverage
    std::ifstream IFS(std::string(CorpusDir) + '/' + DP->d_name);
    Cov.clear();
    ParseJSON(IFS, Cov);
    IFS.close();

    // Create a variable (a boolean) to represent the seed
    const auto SeedExpr = Ctx.bool_const(MakeZ3ExprName(DP->d_name).c_str());
    SeedExprs.insert(SeedExpr);

    // Record the set of seeds that cover a particular region
    for (const auto &Reg : Cov) {
      if (RegionsOnly) {
        // Ignore counts
        SeedCoverage[CountedRegion::MakeUncounted(Reg)].insert(SeedExpr);
      } else {
        SeedCoverage[Reg].insert(SeedExpr);
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
    std::cout << "[*] Generating constraints for " << NumSeeds << " seeds... "
              << std::flush;
  }
  StartTime = std::chrono::steady_clock::now();

  SeedCount = 0;
  NumSeeds = SeedCoverage.size();

  for (const auto &[_, Seeds] : SeedCoverage) {
    if (Seeds.empty()) {
      continue;
    }

    z3::expr EdgeDisjunc = std::accumulate(
        Seeds.begin(), Seeds.end(), Ctx.bool_val(false),
        [](const z3::expr &E1, const z3::expr &E2) { return E1 || E2; });
    Optimizer.add(EdgeDisjunc);

    if ((++SeedCount % 10 == 0) && ShowProg) {
      Prog.Update(SeedCount * 100 / NumSeeds, "Generating seed constraints");
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

  const auto Result = Optimizer.check();

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
