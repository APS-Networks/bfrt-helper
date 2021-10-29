#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
base_dir=$(realpath ${script_dir}/..)

cd ${base_dir}
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
pip install -r requirements.txt

python -m pytest --capture=tee-sys -v --cov=bfrt_helper --cov-report html ${PYDIR}