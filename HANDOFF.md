# Gravitas Session Handoff

## Current State

- Branch `main` is deployed through GitHub Actions run `31849924673` at application commit `9ae76cd`.
- Azure Static Web Apps authentication, linked-backend isolation, hashed job ownership, and daily Blob quotas are live.
- API and worker revisions `0000008` are Ready.
- The live Azure gate passed direct-backend rejection, anonymous submission rejection, the quota-limited CI render path, and both PNG dimensions.
- G-001 and G-002 are complete. [TRACKER.md](TRACKER.md) is the source of truth for remaining work.

## Next Action

Start G-004 and G-005 together: complete the metadata sidecar, expose an authenticated metadata URL from the API, add the web download, and extend the live gate to verify provenance fields.

Required provenance includes the background source URL, credit, usage note, per-aspect crop transform, algorithm, seed, preset, and render date.

## Verification Baseline

- Web: 13 tests passed; lint and production build passed.
- Render API: 30 tests passed.
- Render worker: 15 tests passed.
- Bicep compiled without warnings before deployment.

## Known Follow-Up

- G-003: update the shared schema description from `20 / zoom` to the runtime formula `48 / zoom`.
- G-009: separate deployed MVP requirements from the reference-render roadmap.
