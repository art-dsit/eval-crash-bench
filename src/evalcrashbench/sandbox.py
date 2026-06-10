"""Inner-container exec helper for the EC2-hosted Docker sandbox.

The Inspect sandbox is an EC2 VM; ``setup.sh`` runs a memory-limited Docker
container ("eval-container") inside it. Commands run in that container via
``docker exec``.
"""

from pathlib import Path

from inspect_ai.util import ExecResult, sandbox

PACKAGE_DIR = Path(__file__).parent
SETUP_SCRIPT = (PACKAGE_DIR / "setup.sh").as_posix()

CONTAINER_NAME = "eval-container"


async def exec_in_container(
    cmd: list[str], timeout: int | None = None
) -> ExecResult[str]:
    """Run ``cmd`` inside the memory-limited container via ``docker exec``."""
    return await sandbox().exec(
        cmd=["docker", "exec", CONTAINER_NAME, *cmd], timeout=timeout
    )
