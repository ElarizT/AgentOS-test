from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path

import sulcus
import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_project_metadata_declares_python_only_setuptools_build() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'build-backend = "setuptools.build_meta"' in pyproject
    assert 'name = "sulcus"' in pyproject
    assert 'license = "Elastic-2.0"' in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject
    assert 'version = {attr = "sulcus._version.__version__"}' in pyproject
    assert 'requires-python = ">=3.10"' in pyproject
    build_system = pyproject.split("[build-system]", 1)[1].split("[project]", 1)[0]
    assert '"setuptools>=77"' in build_system
    assert '"maturin>=1.5"' not in build_system


def test_package_metadata_matches_public_version_when_installed() -> None:
    try:
        distribution_version = importlib.metadata.version("sulcus")
        metadata = importlib.metadata.metadata("sulcus")
        distribution_name = metadata["Name"]
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("distribution metadata is available after editable or wheel installation")
    assert distribution_name == "sulcus"
    assert distribution_version == sulcus.__version__
    assert metadata["License-Expression"] == "Elastic-2.0"
    assert metadata["License-File"] == "LICENSE"


def test_manifest_and_package_discovery_exclude_development_junk() -> None:
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "recursive-include sulcus *.py" in manifest
    assert "recursive-include kernel *.py" in manifest
    assert "recursive-include examples/supervised_research_team *.py *.md" in manifest
    assert "include LICENSE" in manifest
    assert "global-exclude *.log" in manifest
    assert "prune tests" in manifest


def test_core_public_imports_remain_python_only() -> None:
    from sulcus.llm import DeterministicLLMProvider
    from sulcus.native import native_core_available
    from sulcus.runtime import AgentToolLoop
    from sulcus.tools import ToolRegistry, ToolRuntime

    assert all((DeterministicLLMProvider, AgentToolLoop, ToolRegistry, ToolRuntime))
    assert isinstance(native_core_available(), bool)
    assert sys.version_info >= (3, 10)


def test_canonical_package_owns_version_without_a_legacy_package() -> None:
    import importlib.util
    from sulcus._version import __version__
    from sulcus.runtime import AgentToolLoop
    from sulcus.tools import ToolRegistry

    assert sulcus.__version__ == __version__ == "1.0.0rc1"
    assert sulcus.AgentToolLoop is AgentToolLoop
    assert sulcus.ToolRegistry is ToolRegistry
    # Regression guard: the removed package must not be importable.
    assert importlib.util.find_spec("agentos") is None
