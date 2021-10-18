#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
base_dir=${script_dir}/..
bfproto_file="${base_dir}/proto/bfruntime.proto"

bfproto_file=$(realpath ${bfproto_file})
bfproto_dir=$(dirname ${bfproto_file})

if [ ! -z "${VIRTUAL_ENV}" ] ; then
    echo -e "\nI am already in a Python virtual environment. Deactivating."
    deactivate
fi

echo -e "\nCreating Python virtual environment and installing packages"
python3 -m venv ./.venv --copies

. .venv/bin/activate

pip install -e ${base_dir}

site_packages=$(python -m site | grep .venv | sed -E -e "s/^\s*'//g" -e "s/',$//g")


python -m grpc_tools.protoc \
    --proto_path=${bfproto_dir} \
    --proto_path=${site_packages} \
    --python_out=${site_packages} \
    --grpc_python_out=${site_packages} \
        ${bfproto_file}