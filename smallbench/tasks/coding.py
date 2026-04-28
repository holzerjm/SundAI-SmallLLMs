"""Implement-this-function tasks. Grader executes the response and runs test cases."""
import re


def extract_code(text: str) -> str:
    """Pull the first ```python or ``` block out of a model response."""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else text


def make_grader(fn_name: str, cases: list[tuple[tuple, object]]):
    def grader(resp) -> tuple[bool, str]:
        code = extract_code(resp.content or "")
        ns: dict = {}
        try:
            exec(code, ns)
        except Exception as e:
            return False, f"exec failed: {type(e).__name__}: {e}"
        fn = ns.get(fn_name)
        if not callable(fn):
            return False, f"{fn_name} not defined"
        for inp, expected in cases:
            try:
                actual = fn(*inp)
            except Exception as e:
                return False, f"{fn_name}{inp} raised {type(e).__name__}: {e}"
            if actual != expected:
                return False, f"{fn_name}{inp} = {actual!r}, expected {expected!r}"
        return True, "all cases pass"

    return grader


TASKS = [
    {
        "id": "fizzbuzz",
        "prompt": (
            "Write a Python function `fizzbuzz(n: int) -> list[str]` that returns the "
            "FizzBuzz sequence from 1 to n inclusive: 'Fizz' for multiples of 3, "
            "'Buzz' for multiples of 5, 'FizzBuzz' for multiples of 15, otherwise the "
            "number as a string. Output only the function in a python code block."
        ),
        "grader": make_grader("fizzbuzz", [
            ((5,), ["1", "2", "Fizz", "4", "Buzz"]),
            ((15,), ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz",
                     "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]),
        ]),
    },
    {
        "id": "palindrome",
        "prompt": (
            "Write `is_palindrome(s: str) -> bool` that returns True if s reads the "
            "same forwards and backwards, ignoring case and non-alphanumeric chars. "
            "Output only the function in a python code block."
        ),
        "grader": make_grader("is_palindrome", [
            (("racecar",), True),
            (("A man, a plan, a canal: Panama",), True),
            (("hello",), False),
            (("",), True),
        ]),
    },
    {
        "id": "merge_intervals",
        "prompt": (
            "Write `merge(intervals: list[list[int]]) -> list[list[int]]` that merges "
            "overlapping intervals. Example: [[1,3],[2,6],[8,10]] -> [[1,6],[8,10]]. "
            "Output only the function in a python code block."
        ),
        "grader": make_grader("merge", [
            (([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]),
            (([[1, 4], [4, 5]],), [[1, 5]]),
            (([],), []),
        ]),
    },
]
