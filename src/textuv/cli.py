from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="textuv: Scaffold a Textual + uv application.")


def to_package_name(name: str) -> str:
    slug = name.strip().lower().replace("-", "_")
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    if not slug or not re.match(r"^[a-z_]", slug):
        slug = f"a_{slug}"
    return slug


def to_script_name(name: str) -> str:
    slug = name.strip().lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    if not slug or not re.match(r"^[a-z0-9]", slug):
        slug = f"a-{slug}"
    return slug


@dataclass
class Options:
    project_name: str
    package_name: str
    script_name: str
    textual_version: str
    init_git: bool
    include_devtools: bool


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_app_py(package_name: str) -> str:
    return f'''from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Header, Footer, Label, Input
from textual.binding import Binding


class MyTextualApp(App):
    """Main Textual application."""

    CSS = """
    Screen {{
        background: $surface;
    }}

    Container {{
        padding: 1;
    }}

    Label {{
        margin: 1;
    }}

    Button {{
        margin: 1;
    }}
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Welcome to Textual App!"),
            Input(placeholder="Enter text here..."),
            Horizontal(
                Button("Submit", id="submit", variant="primary"),
                Button("Cancel", id="cancel", variant="default"),
            ),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            self.notify("Submit clicked!")
        elif event.button.id == "cancel":
            self.exit()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


def main() -> None:
    app = MyTextualApp()
    app.run()


if __name__ == "__main__":
    main()
'''


def generate_template_pyproject(project_name: str, package_name: str, script_name: str, textual_version: str, include_devtools: bool) -> str:
    dev_deps = [
        'pytest>=7.0.0',
        'black>=23.0.0',
        'ruff>=0.1.0',
    ]
    if include_devtools:
        dev_deps.insert(0, 'textual-dev>=1.2.0')
    dev_list = ",\n    ".join([f'"{d}"' for d in dev_deps])
    return f'''[project]
name = "{project_name}"
version = "0.1.0"
description = "A Textual TUI application"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "textual{textual_version}",
]

[project.optional-dependencies]
dev = [
    {dev_list}
]

[project.scripts]
{script_name} = "{package_name}.app:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.black]
line-length = 88
'''.replace("{textual_version}", textual_version)


def generate_readme(project_name: str, package_name: str, script_name: str) -> str:
    return f'''# {project_name}

A Textual TUI application scaffolded by textuv.

## Setup

```bash
uv venv
uv pip install -e .
uv pip install -e ".[dev]"
```

## Run

```bash
uv run python -m {package_name}.app
# or
uv run {script_name}
# dev mode (hot reload)
uv run textual run --dev src/{package_name}/app.py
```

## Lint & Format

```bash
uv run ruff check src/
uv run black src/
uv run ruff check --fix src/
```
'''


def generate_gitignore() -> str:
    return """__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.pytest_cache/
.ruff_cache/
.DS_Store
"""


def generate_makefile(package_name: str) -> str:
    return f'''.PHONY: install dev run run-dev test lint format clean

install:
\tuv pip install -e .

dev:
\tuv pip install -e ".[dev]"

run:
\tuv run python -m {package_name}.app

run-dev:
\tuv run textual run --dev src/{package_name}/app.py

test:
\tuv run pytest

lint:
\tuv run ruff check src/

format:
\tuv run black src/
\tuv run ruff check --fix src/

clean:
\tfind . -type d -name "__pycache__" -exec rm -rf {{}} +
\tfind . -type f -name "*.pyc" -delete
'''


def init_git(repo_dir: Path) -> None:
    try:
        subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "commit", "-m", "Initial Textual app template with uv"], cwd=str(repo_dir), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # Silently ignore git failures (e.g., no user.name configured)
        pass


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Project directory and package name base."),
    package_name: Optional[str] = typer.Option(None, "--package-name", help="Python package name (default: derived from project name)"),
    textual_version: str = typer.Option(">=0.41.0", "--textual-version", help='Version spec for textual (e.g., ">=0.41.0")'),
    init_git_flag: bool = typer.Option(True, "--init-git/--no-init-git", help="Initialize a git repository."),
    devtools: bool = typer.Option(True, "--devtools/--no-devtools", help="Include textual-dev in dev dependencies."),
) -> None:
    """Create a new Textual + uv application scaffold."""
    pkg = package_name or to_package_name(project_name)
    script_name = to_script_name(project_name)

    target = Path(project_name).resolve()
    if target.exists() and any(target.iterdir()):
        typer.secho(f"[textuv] Target directory already exists and is not empty: {target}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    ensure_dir(target)

    # src package
    write_text(target / "src" / pkg / "__init__.py", "")
    write_text(target / "src" / pkg / "components" / "__init__.py", "")
    write_text(target / "src" / pkg / "app.py", generate_app_py(pkg))

    # tests
    write_text(target / "tests" / "__init__.py", "")

    # config files
    write_text(
        target / "pyproject.toml",
        generate_template_pyproject(project_name=project_name, package_name=pkg, script_name=script_name, textual_version=textual_version, include_devtools=devtools),
    )
    write_text(target / "README.md", generate_readme(project_name, pkg, script_name))
    write_text(target / ".gitignore", generate_gitignore())
    write_text(target / "Makefile", generate_makefile(pkg))

    if init_git_flag:
        init_git(target)

    typer.secho(f"[textuv] Project created at: {target}", fg=typer.colors.GREEN)
    typer.echo("\nNext steps:")
    typer.echo(f"  cd {target.name}")
    typer.echo('  uv venv')
    typer.echo('  uv pip install -e .')
    typer.echo('  uv pip install -e ".[dev]"')
    typer.echo(f'  uv run textual run --dev src/{pkg}/app.py')


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    project_name: Optional[str] = typer.Argument(None, help="Project directory and package name base."),
    package_name: Optional[str] = typer.Option(None, "--package-name", help="Python package name (default: derived from project name)"),
    textual_version: str = typer.Option(">=0.41.0", "--textual-version", help='Version spec for textual (e.g., ">=0.41.0")'),
    init_git_flag: bool = typer.Option(True, "--init-git/--no-init-git", help="Initialize a git repository."),
    devtools: bool = typer.Option(True, "--devtools/--no-devtools", help="Include textual-dev in dev dependencies."),
) -> None:
    # If a subcommand (like 'new') is provided, do nothing here
    if ctx.invoked_subcommand:
        return
    # If user passed a project_name without 'new', treat it as 'new <project_name>'
    if project_name:
        new(
            project_name=project_name,
            package_name=package_name,
            textual_version=textual_version,
            init_git_flag=init_git_flag,
            devtools=devtools,
        )
        raise typer.Exit()
    # Otherwise, show help
    typer.echo(ctx.get_help())
    raise typer.Exit(code=0)

def main() -> None:
    app()


if __name__ == "__main__":
    main()


