#!/bin/bash

set -e

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <DOCKER_IMAGE> <CONTAINER_PATH> <HOST_DIR>"
    echo ""
    echo "DOCKER_IMAGE: Name of the Docker image to extract a directory from"
    echo "CONTAINER_PATH: The directory in the Docker container to extract"
    echo "HOST_DIR: The location of the host directory to extract to"
    exit 1
fi

DOCKER_IMAGE=$1
CONTAINER_PATH=$2
HOST_DIR=$(mkdir -p $3 && cd $3 && pwd)

docker_container=$(docker run -d ${DOCKER_IMAGE} sleep 1000)
docker cp ${docker_container}:${CONTAINER_PATH} ${HOST_DIR}
docker kill ${docker_container} > /dev/null
docker rm ${docker_container} > /dev/null
