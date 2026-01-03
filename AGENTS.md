# AGENTS.md

This document provides guidelines for AI agents working on the `reachy-mini-apps` repository.

## Project Overview

This repository contains a collection of mini-applications for the Reachy Mini robot. The goal is to provide a set of simple and fun demos that showcase the robot's capabilities.

## Project Structure

-   **`src/demos`**: Contains the source code for the demos.
-   **`tests`**: Contains the tests for the demos.
-   **`docs`**: Contains the documentation for the project.
-   **`data`**: Contains data files used by the demos (e.g., recorded moves).

## Development Workflow

### 1. Project Setup

To get started, set up the development environment by running:

```bash
make setup
```

This will create a virtual environment, install all the required dependencies, and set up Git LFS.

For development, you can install the project in editable mode using:

```bash
make install-dev
```

### 2. Linting and Formatting

This project uses `black` for code formatting and `ruff` for linting.

-   **Check formatting**: `black --check .`
-   **Apply formatting**: `black .`
-   **Run linter**: `ruff check .`
-   **Run linter with autofix**: `ruff check . --fix`

Please ensure your code is formatted and linted before submitting any changes.

### 3. Type Checking

This project uses `mypy` for static type checking.

-   **Run type checker**: `mypy src`

Please ensure your code is type-checked before submitting any changes.

### 4. Testing

This project uses `pytest` for testing.

-   **Run all tests**: `pytest`
-   **Run a single test file**: `pytest tests/test_minimal.py`
-   **Run a single test function**: `pytest tests/test_minimal.py::test_main`

All tests must pass before submitting any changes. Please write new tests for any new functionality and update existing tests as needed.

## Code Style Guidelines

### Formatting

-   Code is formatted with `black` using a line length of 88 characters.
-   Follow PEP 8 guidelines.

### Imports

-   Imports are automatically sorted by `black`.
-   The import order is: standard library, third-party libraries, and then local application imports.
-   Example:
    ```python
    import sys
    from pathlib import Path

    import numpy as np
    from reachy_mini import ReachyMini

    from .utils import create_head_pose
    ```

### Naming Conventions

-   **Variables and functions**: `snake_case` (e.g., `my_variable`, `my_function`).
-   **Classes**: `PascalCase` (e.g., `MyClass`).
-   **Constants**: `UPPER_SNAKE_CASE` (e.g., `MY_CONSTANT`).

### Type Hinting

-   All functions and methods must have type hints for all arguments and return values.
-   Use modern Python type hints (e.g., `list[int]` instead of `typing.List[int]`).
-   The codebase should be `mypy` compliant.

### Error Handling

-   Use specific exception types instead of generic `Exception`.
-   Handle potential errors gracefully using `try...except` blocks.
-   Provide meaningful error messages.

### Docstrings

-   All public modules, classes, functions, and methods must have docstrings.
-   Use Google-style docstrings.
-   Example:
    ```python
    def my_function(arg1: int, arg2: str) -> bool:
        """This is a short description of the function.

        This is a longer description that can span multiple lines.

        Args:
            arg1: The first argument.
            arg2: The second argument.

        Returns:
            True if the function was successful, False otherwise.
        """
        # ...
    ```

### Command-Line Interfaces

-   Use `rich-click` to create command-line interfaces for the demos.
-   Use decorators to define commands and options.
-   Provide help messages for all commands and options.

## Git Workflow

-   Create a new branch for each new feature or bug fix.
-   Use a descriptive name for your branch (e.g., `feat/add-new-demo` or `fix/fix-bug-in-minimal-demo`).
-   Once your changes are ready, submit a pull request.
-   Make sure your pull request has a clear title and description.
-   Make sure all the checks pass before merging your pull request.

## Existing AI Agent Rules

There are no existing Cursor or Copilot rules in this repository. Please follow the guidelines in this document.
