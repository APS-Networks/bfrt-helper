#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# base_dir=${script_dir}/..
bfproto_file="${base_dir}/proto/bfruntime.proto"

bfproto_file=$(realpath ${bfproto_file})
bfproto_dir=$(dirname ${bfproto_file})

echo "script_dir:    ${script_dir}"
echo "base_dir:      ${base_dir}"
echo "bfproto_file:  ${bfproto_file}"
echo "bfproto_dir:   ${bfproto_dir}"

if [ ! -z "${VIRTUAL_ENV}" ] ; then
    echo -e "\nI am already in a Python virtual environment. Deactivating."
    deactivate
fi

echo -e "\nCreating Python virtual environment and installing packages"
python3 -m venv ./.venv --copies

. .venv/bin/activate

pip install -e ${script_dir}
pip install -r requirements.txt

site_packages=$(python -m site | grep .venv | sed -E -e "s/^\s*'//g" -e "s/',$//g")

git clone https://github.com/googleapis/api-common-protos

mkdir -p ./bfrt_helper/pb2
python -m grpc_tools.protoc \
    --proto_path=${bfproto_dir} \
    --proto_path=./api-common-protos \
    --python_out=./bfrt_helper/pb2 \
    --grpc_python_out=./bfrt_helper/pb2 \
        ${bfproto_file}