---
name: python
description: >
  Python dev rules. Bazel builds, typing, CLI scripts, pytest, heavy-dep lazy import. 
  Use when writing or reviewing Python in this repo.
---

# Python Dev Skill

## Type Annotations

Python 3.11+ target. Every module gets this at top:

```python
from __future__ import annotations  # first line after docstring/shebang
```

Always annotate params and returns. Use `Path` not `str` for file paths. Generic collections only.

Use `X | None`, never `Optional[X]`.

## Project Layout

Source under `src/<pkg>/`. Tests mirror layout under `tests/`. CLI scripts at example root.

```
<any_example_or_module>/
|-- src/<package_name>/
|   |-- __init__.py
|   `-- <modules>.py
`-- tests/<package_name>/
    |-- __init__.py
    |-- test_*.py
    `-- conftest.py              # fixtures. shared setup.
|-- BUILD.bazel                  # if bazel-builtin
`-- README.md
```

New project? Drop `SKILLS.md` only if it diverges from workspace rules. Not for boilerplate repeats.

## Bazel Targets

Load from `@rules_python//python:defs.bzl`. Three rules matter:

- `py_library` -- reusable code
- `py_binary` -- scripts with entry point
- `py_test` -- test suites

One BUILD snippet covers all three. No repeating per-target variations.

```starlark
load("@rules_python//python:defs.bzl", "py_library", "py_binary", "py_test")

py_library(
    name = "lib",
    srcs = glob(["src/**/*.py"]),
    visibility = ["//visibility:public"],
)

py_binary(
    name = "cli",
    srcs = ["src/cli.py"],
    main = "src/cli.py",
    deps = [":lib"],
)

py_test(
    name = "tests",
    srcs = glob(["tests/**/*.py"]),
    deps = [":lib"],
)
```

External deps go through `pip_parse` in `MODULE.bazel`. Reference via `"@<dep_name>//:all"` in BUILD.

Commands:

```bash
bazel build //...          # compile all
bazel test //...           # run all tests
bazel run //pkg:cli        # exec target
bazel coverage //pkg/tests:all
```

## CLI Scripts

Structure every script the same way. No deviation.

```python
#!/usr/bin/env python3
"""One-line description."""

from __future__ import annotations
import argparse
from pathlib import Path

DEFAULT_IN = "input.dat"

def core(input_path: Path, out_dir: Path) -> None:
    """Business logic. Testable in isolation."""
    ...

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="...")
    p.add_argument("--out-dir", type=Path, default="output/", help="...")
    return p.parse_args()

def main() -> None:
    a = parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    core(Path(DEFAULT_IN), a.out_dir)

if __name__ == "__main__":
    main()
```

Rules: kebab-case args. `type=Path` for paths. Validate existence in `main()`, not inside logic. Separate parse -> main -> core. Always.

## Error Handling

Build exception hierarchy for packages. No flat exceptions.

```python
class AppError(Exception):           # base
    pass

class ParseError(AppError):          # specific cases inherit
    pass
```

Catch specific types only. Never bare `except:`. Always chain with `from exc`.

Heavy deps (torch, hailo_sdk)? Lazy import inside the function. Not at module top. Same code tree, partial installs. Works everywhere.

Test paths? Relative to file. Never absolute.

```python
DATA = Path(__file__).resolve().parent / "data"   # correct
# Path("/home/user/project/data")                 # wrong
```

## Testing

pytest. Tests mirror source under `tests/`. Heavy deps imported inside test functions, not at top. Fixtures live in `conftest.py` or under `tests/data/`. Target 80%+ coverage.

Parametrize data sets. Skip conditional on platform or missing optional dep with `@pytest.mark.skipif`.

## Tooling

- `ruff` -- lint + sort (replaces isort)
- `mypy` -- type check (config: `strict = true`)
- `pytest` -- test runner + coverage

Run both before commit. Both must pass clean.

## Checklists

Before Python commit:

- [ ] `from __future__ import annotations` at top
- [ ] params + returns typed
- [ ] argparse pattern followed (parse -> main -> core)
- [ ] only specific exceptions caught
- [ ] paths use `Path`, not string or os.path
- [ ] coverage >= 80% on new code
- [ ] ruff + mypy clean

Before new project:

- [ ] src/ tree with `__init__.py`
- [ ] tests/ mirrors src/
- [ ] README.md present
- [ ] BUILD.bazel if bazel-builtin target
