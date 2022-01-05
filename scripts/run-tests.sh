#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
base_dir=$(realpath ${script_dir}/..)

cd ${base_dir}

./scripts/build-proto.sh
python3 -m venv .venv
. .venv/bin/activate

pip install build pytest pytest-cov
pip install grpcio==1.43.0 grpcio-tools==1.43.0 googleapis-common-protos==1.54.0



python -m build install
# pip install -e .
# pip install -r requirements.txt

python -m pytest --capture=tee-sys -v --cov=bfrt_helper --cov-report html ${PYDIR}