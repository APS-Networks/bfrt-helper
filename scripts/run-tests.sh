#! /usr/bin/env bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"


. ${script_dir}/env.sh

pip install pytest pytest-cov

python -m pytest --capture=tee-sys -v --cov=bfrt_helper --cov-report html ${PYDIR}