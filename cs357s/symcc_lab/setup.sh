#!/bin/bash

set -eu

root="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
cd "$root"

rm -rf venv
python3 -m venv --without-pip venv
curl https://bootstrap.pypa.io/get-pip.py | venv/bin/python
venv/bin/pip install pysmt cvc5
wget -O cvc5.zip https://github.com/cvc5/cvc5/releases/download/cvc5-1.3.2/cvc5-Linux-x86_64-libcxx-static.zip
unzip -j cvc5.zip cvc5-Linux-x86_64-libcxx-static/bin/cvc5 -d venv/bin
rm -f cvc5.zip
