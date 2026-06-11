#!/bin/bash
# Provision an EC2 VM to host the nested computer-tool harness
# (run_nested_computer.py): a working docker daemon, the inspect computer-tool
# desktop image, and inspect_ai on the system python. Run identically on both the
# `generate` and `scorer` VMs so the agent iterates against the same harness that
# scores it. Idempotent.
set -e

# Docker is preinstalled on the AISI sandbox AMI; fall back to apt only if not.
if ! command -v docker >/dev/null; then
    sudo apt-get -o DPkg::Lock::Timeout=600 update
    sudo apt-get -o DPkg::Lock::Timeout=600 install -y docker.io
fi
sudo systemctl start docker
# So the (non-root) command user's docker calls work without sudo.
sudo chmod 666 /var/run/docker.sock

# The desktop sandbox the nested `computer` tool drives. The published image's
# system python is missing typing_extensions (which /opt/inspect/tool's
# computer_tool.py imports), so as shipped *every* computer action errors at
# import time. We add it in a thin derived image so benign actions succeed and
# only the agent's action can crash the harness. compose_computer.yaml references
# this local tag with `x-local: true`.
docker pull aisiuk/inspect-computer-tool
docker build -t inspect-computer-tool-crashbench - <<'EOF'
FROM aisiuk/inspect-computer-tool
RUN pip install --break-system-packages typing_extensions || pip install typing_extensions
EOF

# inspect_ai for the nested eval, on the system python that run_nested_computer.py
# runs as. Unlike the text_editor #1739 eval, the crash here does NOT depend on the
# framework version: an out-of-bounds computer coordinate makes computer_tool.py
# exit non-zero, and inspect's _send_cmd re-raises that as a bare RuntimeError that
# terminates the eval (present in current inspect too). So this pin is only for
# reproducibility - float it if you need to.
INSPECT_VERSION="inspect_ai==0.3.234"
if command -v uv >/dev/null; then
    sudo uv pip install --system "$INSPECT_VERSION"
elif command -v pip3 >/dev/null; then
    sudo pip3 install --break-system-packages "$INSPECT_VERSION" || sudo pip3 install "$INSPECT_VERSION"
else
    sudo python3 -m pip install --break-system-packages "$INSPECT_VERSION"
fi
