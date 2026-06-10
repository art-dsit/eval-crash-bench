"""Detection-logic tests for the scorer.

The two-VM flow (provision, run the nested harness, read the sentinel) is verified
end-to-end against real EC2; these lock down the branch logic that turns what the
scorer observes on the scorer VM into a crashed / survived verdict, without paying
for VMs.
"""

from inspect_ai.util import ExecResult

import evalcrashbench.sandbox as sb
from evalcrashbench.crash import _parse_commands
from evalcrashbench.sandbox import SENTINEL_PATH, run_nested


class FakeEnv:
    """A sandbox env whose exec is driven by a {command-keyword: result} map.

    Each value is either an ExecResult to return or an exception to raise.
    """

    def __init__(self, results: dict[str, object]):
        self.results = results
        self.writes: list[tuple[str, str]] = []

    async def write_file(self, path: str, contents: str) -> None:
        self.writes.append((path, contents))

    async def exec(self, cmd: list[str], timeout: int | None = None) -> ExecResult:
        if cmd[:2] == ["rm", "-f"]:
            return ExecResult(success=True, returncode=0, stdout="", stderr="")
        key = "cat" if cmd[0] == "cat" else "run"
        outcome = self.results[key]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _patch(monkeypatch, env):
    monkeypatch.setattr(sb, "sandbox", lambda name: env)


async def test_survived_when_sentinel_present(monkeypatch):
    env = FakeEnv(
        {
            "run": ExecResult(success=True, returncode=0, stdout="", stderr=""),
            "cat": ExecResult(success=True, returncode=0, stdout="OK\n", stderr=""),
        }
    )
    _patch(monkeypatch, env)
    crashed, detail = await run_nested("scorer", ["echo hi"])
    assert crashed is False
    assert "survived" in detail
    # the commands were written to the VM as JSON
    assert any(p == sb.COMMANDS_PATH for p, _ in env.writes)


async def test_crashed_when_no_sentinel(monkeypatch):
    env = FakeEnv(
        {
            "run": ExecResult(success=False, returncode=1, stdout="", stderr="boom"),
            "cat": ExecResult(success=False, returncode=1, stdout="", stderr="missing"),
        }
    )
    _patch(monkeypatch, env)
    crashed, detail = await run_nested("scorer", ["bad"])
    assert crashed is True
    assert "no success sentinel" in detail


async def test_crashed_when_harness_hangs(monkeypatch):
    env = FakeEnv({"run": TimeoutError(), "cat": None})
    _patch(monkeypatch, env)
    crashed, detail = await run_nested("scorer", ["hang"])
    assert crashed is True
    assert "hung" in detail


async def test_crashed_when_vm_unreachable_after_run(monkeypatch):
    env = FakeEnv(
        {
            "run": ExecResult(success=True, returncode=0, stdout="", stderr=""),
            "cat": ConnectionError("instance gone"),
        }
    )
    _patch(monkeypatch, env)
    crashed, detail = await run_nested("scorer", ["kill the box"])
    assert crashed is True
    assert "unreachable" in detail


def test_parse_commands_variants():
    assert _parse_commands('["a", "b"]') == ["a", "b"]
    assert _parse_commands('blah\n["x"]\nthanks') == ["x"]
    assert _parse_commands("not json") == []
    assert _parse_commands(None) == []
    assert _parse_commands("[1, 2]") == []  # non-strings rejected


def test_sentinel_constant_is_absolute():
    assert SENTINEL_PATH.startswith("/")
