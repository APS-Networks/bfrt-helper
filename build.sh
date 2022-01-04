#! /usr/bin/env bash

# BfRt Helper Build Script
# A script is required to simplify the process of building because of the
# version of gRPC used in the SDE. This may to be temprary script until the
# build requirements and protobuf compilation are rolled into setuptools, but
# this does currently work.

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

cd ${script_dir}
${script_dir}/build-proto.sh

