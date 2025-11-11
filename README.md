# textuv

Scaffold a Textual + uv application.

- GitHub: https://github.com/totsuxyz/textuv

## Install & Run (Usage)

- Zero-install (recommended): use the bare form (no `new`)

```bash
uvx textuv --help
uvx textuv my-textual-app
```

- Or install the CLI locally:

```bash
uv tool install .
textuv --help
textuv my-textual-app
```

Note:
- The `new` subcommand form (`textuv new <name>`) is not supported at the moment due to argument parsing precedence. Please use the bare form: `textuv <name>`.

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

## License

MIT


