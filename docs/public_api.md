# Public Python API

Sulcus uses `sulcus` as its public Python import package. The following
is the intended v1 public surface.

## Stability levels

- **Stable:** `sulcus` and `sulcus.runtime`, `sulcus.tools`, `sulcus.ipc`,
  and `sulcus.native` are the intended v1-facing APIs.
- **Advanced:** `sulcus.llm` exposes provider-neutral runtime types for
  integrations; its wider provider configuration may evolve with notice.
- **Internal:** `kernel.*` implements Sulcus. Existing imports remain
  supported for compatibility, but new applications should use `sulcus.*`.

Version 1.0.0rc1 freezes this intended v1-facing boundary for release-candidate
validation. Advanced and internal surfaces retain the qualifications above.

## Top-level `sulcus`

`AgentProcess`, process lifecycle enums, structured IPC helpers, core
tool-runtime types, agent tool-loop controls, approval/checkpoint types, and
native capability inspection are available at the top level. LLM types live in
`sulcus.llm` to keep the default namespace focused.

## Public submodules

- `sulcus.runtime`: `AgentToolLoop`, config/result, permissions, limits, and
  resumable approval types.
- `sulcus.tools`: registry, runtime, definitions, execution results, and
  tool exceptions.
- `sulcus.llm`: `LLMRuntime`, messages/responses, tool-call types, and the
  deterministic provider useful for offline integrations.
- `sulcus.ipc`: structured IPC envelopes and helpers.
- `sulcus.native`: native capability reporting and explicit requirement
  errors. It never exposes the raw extension module.

## Migration

```python
# Existing compatibility import
from kernel.tools import ToolRegistry

# Preferred public import
from sulcus.tools import ToolRegistry
```

`kernel.*` imports are not deprecated at import time: Sulcus itself uses them,
and noisy warnings would affect applications and tests. They are intentionally
internal and may receive a later, explicit compatibility-deprecation notice.

Python-only LLM and tool-loop APIs do not require `sulcus_core`. Native
dashboard, IPC, memory, and WASM runtime usage still requires it and should be
checked through `sulcus.native`.
