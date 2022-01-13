#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
base_dir=${script_dir}/..

if [ ! -z "${VIRTUAL_ENV}" ] ; then
    echo -e "\nI am already in a Python virtual environment. Deactivating."
    deactivate
fi

echo -e "\nCreating and activating Python virtual environment"
python3 -m venv ./.venv --copies

# TODO: Figure out what's actually needed here
pip install  \
    sphinx \
    sphinx-rtd-theme \
    myst-parser \
    renku-sphinx-theme \
    sphinx-rtd-theme \
    sphinx-markdown-builder \
    sphinxcontrib-email

pip install grpcio==1.43.0 grpcio-tools==1.43.0 googleapis-common-protos==1.54.0


cd ${base_dir}/docs

make clean && make html


