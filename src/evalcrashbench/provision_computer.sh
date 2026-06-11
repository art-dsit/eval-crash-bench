#!/bin/bash
# Provision EC2 VMs for the computer-tool crash eval.
# Pins inspect_ai to a version with the comma key bug.

set -euxo pipefail

python3 -m venv /venv
source /venv/bin/activate

# Pin to inspect_ai==0.3.204 or earlier (before comma key fix in 0.3.205).
# The comma key bug: inspect #3632
# https://github.com/UKGovernmentBEIS/inspect_ai/pull/3632
pip install 'inspect_ai==0.3.204' docker

echo "Provisioned with inspect_ai==0.3.204 (computer tool comma key bug present)"
