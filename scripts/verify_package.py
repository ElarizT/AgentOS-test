"""Offline source-tree packaging verification for Sulcus contributors."""

from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sulcus
from sulcus.llm import DeterministicLLMProvider
from sulcus.native import native_core_available
from sulcus.runtime import AgentToolLoop
from sulcus.tools import ToolRegistry, ToolRuntime


def main() -> int:
    metadata_version: str | None
    try:
        metadata_version = importlib.metadata.version("sulcus")
    except importlib.metadata.PackageNotFoundError:
        metadata_version = None

    print("Sulcus package verification")
    print("Distribution: sulcus")
    print(f"Package version: {sulcus.__version__}")
    print(f"Metadata version: {metadata_version or 'not installed'}")
    print(f"Native core: {'available' if native_core_available() else 'unavailable'}")
    print("Public imports: ok")

    if metadata_version is not None and metadata_version != sulcus.__version__:
        print("ERROR: installed distribution metadata does not match sulcus.__version__")
        return 1
    if not all((AgentToolLoop, ToolRegistry, ToolRuntime, DeterministicLLMProvider)):
        print("ERROR: required public symbols are unavailable")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
