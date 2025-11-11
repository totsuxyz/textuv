# textuv

Scaffold a Textual + uv application.

## Install & Run

- Zero-install:

```bash
uvx textuv --help
uvx textuv new my-textual-app
```

- Or install the CLI locally:

```bash
uv tool install .
textuv --help
textuv new my-textual-app
```

## Generated project

The scaffold includes:
- `src/<package>/app.py` — minimal Textual App
- `pyproject.toml` — with `textual` and dev extras
- `Makefile`, `.gitignore`, `tests/__init__.py`

Next steps after generation:

```bash

cd my-textual-app
uv venv
uv pip install -e .
uv pip install -e ".[dev]"
uv run textual run --dev src/<package>/app.py
```


