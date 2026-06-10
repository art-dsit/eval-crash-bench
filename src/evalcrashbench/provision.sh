#!/bin/bash
# Provision an EC2 VM to host the nested target harness (run_nested.py): a working
# docker daemon, the inspect default sandbox image pre-pulled, and inspect_ai on
# the system python. Run identically on both the `generate` and `scorer` VMs so
# the agent iterates against the same harness that scores it. Idempotent.
set -e

# Docker is preinstalled on the AISI sandbox AMI; fall back to apt only if not.
# The DPkg::Lock timeout waits out the unattended-upgrades job that holds the
# dpkg lock on fresh Ubuntu VMs.
if ! command -v docker >/dev/null; then
    sudo apt-get -o DPkg::Lock::Timeout=600 update
    sudo apt-get -o DPkg::Lock::Timeout=600 install -y docker.io
fi
sudo systemctl start docker
# So the (non-root) command user's docker calls work without sudo.
sudo chmod 666 /var/run/docker.sock

# Pre-pull the image inspect's default `sandbox="docker"` uses, so the nested
# eval doesn't pay (or fail) a pull mid-run.
docker pull aisiuk/inspect-tool-support

# inspect_ai for the nested eval, on the system python that run_nested.py runs as.
# Try uv (on the AMI) first, then pip variants for whatever base image we got.
if command -v uv >/dev/null; then
    sudo uv pip install --system inspect_ai
elif command -v pip3 >/dev/null; then
    sudo pip3 install --break-system-packages inspect_ai || sudo pip3 install inspect_ai
else
    sudo python3 -m pip install --break-system-packages inspect_ai
fi
