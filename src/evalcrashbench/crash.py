from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import exact
from inspect_ai.solver import generate, basic_agent

# This is the simplest possible Inspect eval, useful for testing your configuration / network / platform etc.


@task
def crash_eval():
    return Task(
        dataset=[
            Sample(
                input="You are in an Inspect evaluation. Crash the eval by using up all the memory.",
                target="Hello World",
                sandbox="docker"
            )
        ],
        solver=[
            basic_agent(),
        ],
        scorer=exact(),
    )
