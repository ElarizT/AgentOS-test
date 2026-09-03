# Sulcus primary demo production plan

This companion describes the pre-migration media preserved in the
[historical archive](archive/README.md). Its product terminology has been
updated to Sulcus; the archived recordings retain their original visuals.

## Product capabilities verified

- Sulcus 1.0.0rc1 is a release-candidate runtime layer around agent execution, not a prompt, chain, or workflow-graph framework.
- The public Python runtime provides registered and schema-validated tools, bounded `AgentToolLoop` execution, permissions, per-loop/per-round/per-tool resource limits, approval pause/resume, structured safe runtime events, and versioned local approval checkpoints.
- The process runtime provides `AgentProcess`, parent/child supervision, restart policies and budgets, structured IPC, and a native-backed Textual dashboard when the optional native core and dashboard dependencies are available.
- The flagship Supervised Research Team is deterministic, offline, and uses the real LLM/tool-loop APIs with a scripted provider and a closed bundled corpus.
- Current limitations that must remain visible in production decisions: release-candidate maturity; deterministic demos do not prove model quality; local checkpoints are not encrypted or distributed; synchronous tool timeouts do not pre-empt Python execution; the project does not claim production-grade distributed execution.

## Selected features and rationale

1. **Flagship research-team CLI** — it is the documented public entry point, deterministic, offline, and repeatable.
2. **Current runtime dashboard** — it makes the process-like model legible through Agent Tree, Runtime Timeline, Processes / IPC, and Tool / LLM Activity.
3. **Structured recovery plus resource denial** — one missing source produces a recorded tool failure and a bounded retry; tight-limit mode safely denies one extra search.
4. **Approval pause** — simulated publication stops before the side effect and is denied by default.
5. **Persistent checkpoint example** — a fresh process resumes approval state without repeating the provider request.

These features communicate execution ownership, visibility, control, and recovery in under one minute without implying unsupported security or production-readiness claims.

## Exact workflow and commands

Recording environment: 1920×1080, 24 fps, dark theme, Cascadia Mono at an effective 28–34 px, no credentials or user-specific paths shown.

```powershell
sulcus check
sulcus demo research-team --parallel --tight-limits --show-timeline --deny-publish
python main.py
# In the dashboard command bar:
run examples/research_team
python -m examples.agent_tool_loop_persistent_checkpoint_demo
```

The render uses output captured from the public CLI and persistent-checkpoint example. The dashboard frame is exported from the current `SulcusDashboard` after the bundled research-team workflow runs.

## Shot list, timing, overlays, and narration

| Time | Picture | Overlay | Narration |
| --- | --- | --- | --- |
| 0–4s | Current Sulcus dashboard already populated; fast crop toward active panes | `Agents shouldn't run unmanaged.` / `Processes, not scripts.` | “Most agents still run as scripts: hard to inspect, constrain, or recover.” |
| 4–11s | Exact public CLI command; real run summary appears immediately | `Offline. Deterministic. No API key.` | “Sulcus gives agent workloads a runtime.” |
| 11–23s | Dashboard center stage; guided crops across Agent Tree, Runtime Timeline, and Processes / IPC | `One runtime. Every boundary visible.` | “This offline research team plans, gathers evidence, critiques, and synthesizes through registered tools. Every model step and tool call becomes a structured runtime event.” |
| 23–34s | Safe timeline rows focus on `tool_execution_failed`, recovery, and `tool_call_resource_denied` | `Failure recorded → workflow continues` / `Per-tool limit enforced` | “One source read fails; the loop records it, recovers, and continues. A per-tool budget blocks an extra search before execution.” |
| 34–44s | Approval request → loop paused → denial → completion; final report remains local | `Side effects pause here.` / `Publication denied. Report kept local.` | “Publication pauses at an explicit approval boundary and stays local when denied.” |
| 44–50s | Exact persistent-checkpoint command and four-line real output | `Restart-safe approval state.` | “That paused state can be saved and resumed by a fresh process without repeating the original model request.” |
| 50–56s | Sulcus mark and GitHub URL over a quiet dashboard crop | `An operating layer for AI agents.` | “Sulcus—an operating layer for agent systems.” |

## Required assets

- Current dashboard export generated from repository code.
- Captured CLI and persistent-checkpoint output generated during the build.
- Sulcus mark recreated from the existing showcase visual language.
- Subtle generated electronic bed and restrained UI ticks; no stock footage or third-party copyrighted assets.
- 16:9 thumbnail with large product name, runtime dashboard crop, and `Processes, not scripts.`

## Presentation-only changes

- Add reproducible dashboard-capture and video-render scripts under `scripts/`.
- Add the production plan, final timeline/narration, thumbnail, and video artifacts under `showcase/`.
- Do not change the runtime, tool loop, checkpoint semantics, or dashboard product behavior for the recording.

