"""Agent tools for the crash eval."""

from inspect_ai.tool import Tool, tool
from inspect_ai.tool._tools._execute import code_viewer

from .sandbox import exec_in_container


@tool(viewer=code_viewer("bash", "cmd"))
def container_bash(timeout: int = 180) -> Tool:
    """Run bash commands inside the memory-limited container.

    Args:
        timeout: Command timeout in seconds.
    """

    async def execute(cmd: str) -> str:
        """Run a bash command inside the sandbox container.

        Args:
            cmd: Bash command to execute.

        Returns:
            Command output (stderr then stdout).
        """
        result = await exec_in_container(["bash", "-c", cmd], timeout=timeout)
        output = f"{result.stderr}\n" if result.stderr else ""
        return f"{output}{result.stdout}"

    return execute
