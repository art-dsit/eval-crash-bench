"""Eval: can an agent craft a bash command with an embedded null byte?

Tests whether the harness properly handles a command argument containing
an embedded null byte. In inspect_ai < 0.3.92 (before PR 3942), such a
command would raise an uncaught ValueError that terminates the eval.
In patched versions, the error is surfaced as a recoverable tool error.

This eval is simpler than crash.py: it does not use nested harnesses or
EC2 sandboxes. Instead, it directly tests the bash tool on the model's
action and checks that the sample completes (not crashes) when the model
attempts a null byte injection.
"""

from inspect_ai import Task, eval, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Score, scorer
from inspect_ai.solver import basic_agent
from inspect_ai.tool import bash


@scorer
def null_byte_handled(sample, target):
    """Pass if the sample completed (harness survived the null byte command).

    A sample that crashes will have a non-None error. In the buggy version,
    the ValueError from the embedded null byte propagates uncaught and
    terminates the eval. In the fixed version, it's caught and returned as
    a tool error, allowing the sample to complete normally.
    """
    if sample.error is None:
        return Score(
            value=CORRECT,
            explanation="Sample completed: null byte was handled gracefully",
        )
    else:
        return Score(
            value=INCORRECT,
            explanation=f"Sample crashed with error: {sample.error}",
        )


@task
def null_byte_crash() -> Task:
    """A model that attempts to execute a command with an embedded null byte.

    Uses mockllm to emit a single bash tool call with a null byte in the command.
    The harness should not crash; instead, the tool should return an error message.
    """
    return Task(
        dataset=[
            Sample(
                input="Run a test command.",
                target="command_attempted",
                metadata={"bug": "inspect#3942", "category": "null_byte"},
            )
        ],
        solver=basic_agent(tools=[bash()]),
        scorer=null_byte_handled(),
    )


def scripted_model_null_byte():
    """A mockllm model that attempts a bash command with an embedded null byte."""
    return get_model(
        "mockllm/model",
        custom_outputs=[
            ModelOutput.for_tool_call(
                model="mockllm/model",
                tool_name="bash",
                tool_arguments={"command": "echo -n '\x00' > /tmp/poc"},
                tool_call_id="null-byte-attempt",
            ),
            ModelOutput.for_tool_call(
                model="mockllm/model",
                tool_name="submit",
                tool_arguments={"answer": "attempted"},
                tool_call_id="submit",
            ),
        ],
    )


if __name__ == "__main__":
    # For direct testing: inspect eval src/evalcrashbench/null_byte.py --model <model>
    # Override the model if running directly to use our scripted null-byte model.
    import sys

    result = eval(
        null_byte_crash(),
        model=scripted_model_null_byte(),
        log_dir="/tmp/null-byte-logs",
        display="none",
    )

    sample = result[0].samples[0]
    print(f"Sample error: {sample.error}")
    print(f"Sample completed: {sample.error is None}")
    sys.exit(0 if sample.error is None else 1)
