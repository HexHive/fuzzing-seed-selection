#include "Z3Common.h"

std::string GetSeed(const z3::expr &E) {
  std::string Name = E.to_string();
  Name.pop_back();

  return Name.erase(0, 1);
}

std::string MakeZ3ExprName(const std::string &S) {
  // Z3 "quotes" strings with a pipe if it begins with a numeric value. So we
  // just quote everything
  std::string Name("|");
  Name.append(S);
  Name.append("|");

  return Name;
}

void GetZ3Weights(std::istream &IS, WeightsMap &Weights) {
  std::string Line;

  while (std::getline(IS, Line, '\n')) {
    const size_t DelimPos = Line.find(',');
    const std::string Seed = Line.substr(0, DelimPos).c_str();
    const unsigned Weight = std::stoul(Line.substr(DelimPos + 1));

    Weights.emplace(MakeZ3ExprName(Seed), Weight);
  }
}
