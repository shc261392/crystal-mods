# Copilot instructions — Crystal Mods

**The canonical agent rules live in [`AGENTS.md`](../AGENTS.md) at the repo root.
Read it first — it is the single source of truth for every AI agent working in
this repository, and it is kept up to date.**

This file exists only so GitHub Copilot's auto-loading convention finds a
pointer. It deliberately does not restate the rules: a second copy drifts out of
sync with `AGENTS.md` and agents then follow the stale one.

If you were looking for something that used to be here:

| Topic | Where it lives now |
| --- | --- |
| Scratch space, `/tmp` ban, `dist/` deliverable rule | `AGENTS.md` hard rule 1 |
| Validate before implementing / no over-claiming | `AGENTS.md` hard rules 4–5 |
| Data-modification approval, reversibility | `AGENTS.md` hard rules 6–7 |
| DoW DE locale + no-deploy rules | `AGENTS.md` hard rules 9–11 |
| Credential safety | `AGENTS.md` hard rule 12 |
| UI browser-verification mandate | `AGENTS.md` hard rule 14 |
| Deterministic builds (one recipe per release) | `AGENTS.md` hard rule 15 |
| Repo layout, `metadata.jsonc`, tooling | `AGENTS.md` → *Repository contract* |
| Authoring guides (Vortex, Nexus, Unity, UE…) | `AGENTS.md` → *Progressive disclosure* |
