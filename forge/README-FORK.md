# Forge fork — STATUS: needs API rework

**Imported from:** `/home/agdis/archive/b-os/code-forge/` (pre-2026)
**Imported on:** 2026-04-11
**Status:** ⚠️ NOT FUNCTIONAL — calls dead pm-api endpoints

## What's broken

`forge.py` was written against an older PM-OS API and calls endpoints that
no longer exist:

- `POST /api/tasks/dispatch` — REMOVED
- `POST /api/tasks/submit` — REMOVED

The current `pm-api` exposes a single dispatch surface:

- `POST /api/v2/run` (`handleEngineRun` in `cmd/pm-api/handlers_v2.go`) which
  accepts 4 body shapes in priority order:
  1. `recipe_inline`: full Recipe JSON
  2. `recipe`: slug + optional params map
  3. `intent`: natural-language string
  4. `plan`: raw core.Plan JSON

## What works

`forge.py plan <input>` (the planning subcommand) does NOT call dispatch
endpoints — it only parses input + writes GCS context. Should still work
modulo `gcloud`/GCS side effects.

`forge.py run <input>` (full dispatch) is BROKEN.

## To make forge.py run work again

Estimated ~200-300 LOC of rework:

1. **`submit_task` (lines 188-196):** rewrite to wrap each sub-wave as a
   1-wave inline recipe and POST `/api/v2/run` with `{"recipe_inline": rec}`
2. **`get_task` (line 201):** no per-task GET anymore — must poll
   `GET /api/runs/{run_id}` and walk `tasks[]` to find the dispatched
   sub-wave by ID. Affects `relay_monitor` (line 601+) and
   `_dispatch_unblocked` (718+) ~80-120 LOC
3. **`forge_branch` git workflow:** old API routed dispatches straight to
   Pub/Sub with branch metadata. Worker now needs to honor branch info from
   recipe step instructions.
4. **`cmd_collect` (line 1067):** same polling rewrite as #2

## Why fork in tree

For Tier 2 mining (10 Hermes-derived recipes) we tried to use Forge but
discovered the API drift. Used parallel Task agents instead. Forge fork
kept here for the rework when needed — it's still 50KB of useful
plan-parsing + context-building logic that we don't want to re-derive.

## Audit details

See commit message of `09cc823` for the full audit done by the
recipe-creation agent (batch 5).
