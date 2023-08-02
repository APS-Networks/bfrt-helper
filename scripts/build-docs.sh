#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
base_dir=${script_dir}/..

if [ ! -z "${VIRTUAL_ENV}" ] ; then
    echo -e "\nI am already in a Python virtual environment. Deactivating."
    deactivate
fi

echo -e "\nCreating and activating Python virtual environment"
python3 -m venv ./.docsvenv
. .docsvenv/bin/activate

pip install ${base_dir}
# TODO: Figure out what's actually needed here
pip install  \
    sphinx \
    myst-parser \
    renku-sphinx-theme \
    sphinxcontrib-email \
    sphinx-rtd-theme \
    sphinx-documatt-theme \
    sphinx-material


cd ${base_dir}/docs

make clean && make html



