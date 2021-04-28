add_executable(afl-showmap-maxsat AFLShowmapMaxSat.cpp Common.cpp)

install(TARGETS afl-showmap-maxsat RUNTIME DESTINATION bin)

if(USE_Z3)
  add_executable(afl-showmap-z3 AFLShowmapZ3.cpp
                                Common.cpp
                                Z3Common.cpp)
  add_executable(llvm-cov-z3 LLVMCovZ3.cpp
                             Common.cpp
                             Z3Common.cpp
                             jsoncpp/jsoncpp.cpp)
  target_include_directories(llvm-cov-z3 PRIVATE jsoncpp)

  install(TARGETS afl-showmap-z3 RUNTIME DESTINATION bin)
  install(TARGETS llvm-cov-z3 RUNTIME DESTINATION bin)
endif(USE_Z3)
