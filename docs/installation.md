# Installation

Sulcus uses `sulcus` as its Python distribution and public import package.
Version 1.0.0rc1 is a release candidate available from source or locally
built artifacts; it is not published to PyPI yet.

Once published, install it with:

```bash
python -m pip install sulcus
```

Sulcus is source-available under the Elastic License 2.0 (ELv2). ELv2 is not
an OSI-approved open-source license. See [LICENSE](../LICENSE) for the complete
license terms.

## Python-only installation

Python 3.10 or newer is supported; Python 3.14 is the primary development
environment used for this repository.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .
python examples\public_api_quickstart.py
sulcus check
```

The compatibility command `sulcus-check` prints the same capability report.
Use `sulcus --help` to list installed diagnostics and offline demos.

Projects may add an optional `sulcus.toml` in their working directory:

```toml
[sulcus]
execution_mode = "sequential"
```

Run `sulcus config check` to validate it. The complete format and precedence
rules are documented in [configuration.md](configuration.md).

Unix/macOS shells:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
pip install -e .
python examples/public_api_quickstart.py
sulcus check
```

This supports the public LLM, tools, timeline, and agent tool-loop APIs without
Rust. Native dashboard, IPC, memory, and WASM features remain unavailable until
the extension is built.

## Optional extras

```powershell
pip install -e .[openai]       # OpenAI-compatible provider SDK
pip install -e .[dashboard]    # Textual/Rich dashboard dependencies
pip install -e .[dev]          # pytest, build, and native development tools
pip install -e .[native-dev]
cd native
python -m maturin develop --locked
cd ..
```

For a full local development environment:

```powershell
pip install -e .[dev,dashboard,openai,native-dev]
cd native
python -m maturin develop --locked
cd ..
```

## Build distributions

```powershell
python -m build
```

This produces a Python-only wheel and source distribution in `dist/`; neither
base artifact compiles or bundles the optional Rust extension. To test a wheel
from outside the source tree, create a fresh environment and install the wheel
file with `pip install dist\sulcus-<version>-py3-none-any.whl`.

## Troubleshooting

See the dedicated [troubleshooting guide](troubleshooting.md) for native-core,
Maturin, optional OpenAI SDK, configuration, checkpoint, CLI, and editable
install failures.

## Optional native distribution boundary

`pip install sulcus` never installs the Rust extension. The native development
extra supplies Maturin and the Python `wasmtime` WAT assembler; Rust/Cargo must
be installed separately. Build from a Git checkout's `native/` directory to
install `sulcus-core` alongside `sulcus`. Never run the native build from the
repository root, whose metadata belongs to the Python-only distribution.
Native sources and tooling are intentionally absent from the normal sdist.
See [local native development](../native/README.md).

The `dev` extra includes the dashboard and HTTP-client dependencies needed by
the existing test suite. The `openai` extra explicitly declares both the SDK
and the HTTP client used by the synchronous fallback and async adapter.
