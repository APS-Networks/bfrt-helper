#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
base_dir=$(realpath ${script_dir}/..)
bfproto_file="${base_dir}/proto/bfrt_helper/pb2/bfruntime.proto"
bfproto_dir=$(realpath ./proto)

echo "script_dir:    ${script_dir}"
echo "base_dir:      ${base_dir}"
echo "bfproto_file:  ${bfproto_file}"
echo "bfproto_dir:   ${bfproto_dir}"

if [ ! -z "${VIRTUAL_ENV}" ] ; then
    echo -e "\nI am already in a Python virtual environment. Deactivating."
    deactivate
fi

echo -e "\nCreating and activating Python virtual environment"
python3 -m venv ./.venv --copies

. .venv/bin/activate

pip install grpcio==1.43.0 grpcio-tools==1.43.0


echo -e "\nCompiling BfRt protobuf"

if [ ! -d "python-api-common-protos" ] ; then
    git clone https://github.com/googleapis/python-api-common-protos
fi

mkdir -p ./bfrt_helper/pb2

python -m grpc_tools.protoc \
    --proto_path=./python-api-common-protos \
    --proto_path=${bfproto_dir} \
    --python_out=.\
    --grpc_python_out=. \
        ${bfproto_file}
