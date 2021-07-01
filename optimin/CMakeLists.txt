cmake_minimum_required(VERSION 3.7)

project(optimin
  LANGUAGES CXX
  DESCRIPTION "SAT-based fuzzing corpus minimizer"
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(USE_Z3)
  find_package(Z3 REQUIRED config)
  message(STATUS "Found Z3 ${Z3_VERSION_STRING}")
  include_directories(${Z3_CXX_INCLUDE_DIRS})
  link_libraries(${Z3_LIBRARIES})
endif(USE_Z3)

find_package(Boost COMPONENTS container REQUIRED)
message(STATUS "Found Boost ${Boost_VERSION_STRING}")

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3")

include_directories(${Boost_INCLUDE_DIR})

add_subdirectory(src)
