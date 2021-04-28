FROM ubuntu:latest

# Install prerequesites
RUN export DEBIAN_FRONTEND=noninteractive &&    \
    apt update &&                               \
    apt install -y git build-essential cmake    \
        libboost-container-dev libz-dev python3

# Add OptiMin source
ADD CMakeLists.txt /optimin/
ADD src /optimin/src

# Build OptiMin
RUN mkdir -p /optimin/build
RUN cd /optimin/build &&        \
    cmake .. &&                 \
    make -j &&                  \
    make install

# Build EvalMaxSAT
RUN git clone https://github.com/FlorentAvellaneda/EvalMaxSAT
RUN mkdir -p EvalMaxSAT/build
RUN cd EvalMaxSAT/build &&      \
    cmake .. &&                 \
    make -j &&                  \
    make install

# Add OptiMin wrapper
ADD optimin.py /optimin/
ENTRYPOINT ["/optimin/optimin.py"]
