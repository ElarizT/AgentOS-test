# Local native development

The normal `sulcus` wheel and source distribution are Python-only. This local
build project installs the separate `sulcus-core` distribution, imported as
`sulcus_core`. Its version comes from the unchanged root `Cargo.toml`.
The Python package version remains authoritative in `sulcus/_version.py`.

From a repository checkout, activate the intended environment and run:

```powershell
python -m pip install -e .[native-dev]
cd native
python -m maturin develop --locked
cd ..
python -c "import sulcus, sulcus_core; print(sulcus.__version__)"
sulcus check
```

Run Maturin from this directory: running it from the repository root picks up
the Python distribution's metadata and can replace that installation with an
extension-only distribution. Rust sources and the lockfile remain at the
repository root. This directory is excluded from the normal Python artifacts.
It provides local build metadata, not a native-wheel release pipeline.

`native/LICENSE` is an exact copy of the root ELv2 license for inclusion in
local native wheels. No native wheel has been published.
