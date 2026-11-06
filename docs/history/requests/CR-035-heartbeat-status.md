# CR-035: a heartbeat says where the job stands

- **Requested by / date:** owner, 2026-10-23 (phase 8 of the overhaul plan: the SLURM executor and its approval gate)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

A job run through SLURM is rendered as a batch, which then waits for the owner's `ponzi-worker approve`, possibly for days. The plan requires that state to be visible through the server. The worker holds the job's lease the whole time, so its heartbeats are the natural carrier.

## What changes

`ponzi_spec.api.Heartbeat.status`: `running`, `awaiting_approval` or none, which leaves the status as it is. The server keeps the job held in any of `leased`, `running` and `awaiting_approval`: each expires like a lease and accepts a heartbeat or a failure report only from the lease holder.

## Do results change?

No.

## Tests

ponzi-service: `test_slurm.py::test_the_loop_waits_for_approval_and_the_server_shows_it`. The server's lease tests still pass.

## Version

Part of `ponzi-spec` 0.3.0 (not yet released).
