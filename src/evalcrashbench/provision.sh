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
# Pinned to the last release with the unfixed text_editor crash (inspect #1739:
# text_editor on a missing path raises an uncaught error and terminates the eval;
# fixed in 0.3.91). The whole point of the eval is that this version is buggy, so
# the pin is load-bearing - don't float it.
INSPECT_VERSION="inspect_ai==0.3.89"
# Try uv (on the AMI) first, then pip variants for whatever base image we got.
if command -v uv >/dev/null; then
    sudo uv pip install --system "$INSPECT_VERSION"
elif command -v pip3 >/dev/null; then
    sudo pip3 install --break-system-packages "$INSPECT_VERSION" || sudo pip3 install "$INSPECT_VERSION"
else
    sudo python3 -m pip install --break-system-packages "$INSPECT_VERSION"
fi
