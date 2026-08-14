# Gravitas Delivery Tracker

**Last audited**: 2026-08-14 \
**Overall status**: MVP deployed; release controls incomplete \
**Current objective**: Bound public render access, make Azure reproducible, and complete export provenance before expanding scientific fidelity.

## Status Key

| Status | Meaning |
| --- | --- |
| Done | Exit criteria verified in code, tests, and the relevant environment |
| In progress | Work has started but exit criteria are not all verified |
| Partial | A useful subset exists; the remaining gap is explicit |
| Not started | No implementation evidence found |
| Deferred | Intentionally outside the current release objective |

## Current Health

| Area | Status | Evidence verified 2026-08-14 |
| --- | --- | --- |
| Source | Healthy | No application-code changes are pending; the deployed CI baseline is committed on `main` |
| Web quality gates | Healthy | 12 tests passed; lint and production build passed |
| Render API quality gates | Healthy | 21 tests passed |
| Render worker quality gates | Healthy | 15 tests passed |
| Static Web App | Running | `swa-gravitas-434092`; default environment Ready at 2026-08-14 22:15 UTC |
| Render API | Running | `ca-gravitas-api`; Bicep-deployed revision `0000007` Ready |
| Render worker | Running | `ca-gravitas-worker`; Bicep-deployed revision `0000007` Ready |
| Deployment automation | Healthy | GitHub Actions run `31847313897` deployed commit `4ced3d1` and passed the live Azure render gate |
| Infrastructure as code | Healthy | Foundation and application Bicep deployments succeeded in run `31847313897`; no resources were replaced |

## Next Up

| Order | Work item | Why now | First verifiable outcome |
| ---: | --- | --- | --- |
| 1 | G-002: Bound public render-job creation | The public endpoint can create unmetered Azure work; this is the largest release risk | A live Azure test proves unknown origins and over-quota submissions are rejected while the deployed web app can still render |
| 2 | G-004 and G-005: Complete and expose provenance | PNGs are trustworthy only when their metadata travels with them | The live test downloads metadata and verifies source, credit, crop, algorithm, seed, preset, and render date |
| 3 | G-009: Split MVP requirements from reference-render goals | Current requirements mix delivered fast-render behavior with future Kerr behavior | Every MVP requirement maps to a deployed control, contract field, worker effect or explicit provenance-only label, and live assertion |

**Decision needed for G-002**: choose the pre-release access model before implementation. Recommended: Static Web Apps authentication plus API authorization and a per-identity render quota. A temporary shared test token is simpler but weaker and creates secret-distribution debt.

## Delivered

- Interactive browser preview with aligned camera geometry and labeled approximation limits.
- Dual-size `5120x1440` and `3440x1440` PNG rendering with independent aspect-safe framing.
- Deterministic seeded Schwarzschild capture raster with weak-field background deflection.
- Queue-backed Azure API and worker with persisted job states and private Blob outputs.
- API-proxied downloads that verify the completed job owns the requested filename.
- Azure metadata sidecar containing the submitted request and explicit approximation labels.
- Deployed Static Web App, render API, and render worker.

## Release Blockers

| ID | Priority | Work item | Status | Evidence | Exit criteria |
| --- | --- | --- | --- | --- | --- |
| G-001 | P0 | Reproduce the live Azure deployment from source | Done | [infra/main.bicep](infra/main.bicep) covers SWA, Container Apps, queue, storage, registry, observability, GitHub OIDC bootstrap, and RBAC; run `31847313897` deployed both phases and passed the real render gate | Bicep covers the full environment and CI deploys it before the real Azure render gate |
| G-002 | P0 | Bound public render-job creation | Not started | [services/render-api/app/main.py](services/render-api/app/main.py) allows every CORS origin and exposes unauthenticated job creation without rate or quota controls | Allowed origins are explicit; render submission has an intentional authorization model and enforceable rate/quota limits; abuse-path tests pass |
| G-003 | P1 | Correct the field-of-view contract description | Not started | Runtime preview and API both use `48 / zoom`; [packages/render-schema/render-request.schema.json](packages/render-schema/render-request.schema.json) still says `20 / zoom` | The shared schema documents `48 / zoom`, and deployed contract evidence confirms clients cannot override `field_of_view` |

## Trustworthy Export Work

| ID | Priority | Work item | Status | Evidence | Exit criteria |
| --- | --- | --- | --- | --- | --- |
| G-004 | P1 | Complete background and render provenance | Partial | Azure writes metadata, but it lacks background source URL, credit, usage note, crop transform, render date, and research preset | Every output exposes a downloadable sidecar containing all required provenance and the exact crop used for each aspect ratio |
| G-005 | P1 | Expose metadata through the API and web app | Not started | Completed API responses return PNG URLs only; `metadata_blob_name` remains internal | Completed jobs return an authenticated metadata URL and the web app offers it beside both PNGs |
| G-006 | P1 | Make control effects honest end to end | Partial | Disk thickness is accepted but does not affect preview or server output; jet strength is preview-only; magnetic state and observing band are provenance-only | Each control is implemented for its declared mode or visibly disabled/labeled as provenance-only in both preview and export UI |
| G-007 | P1 | Bound client polling and support recovery | Not started | [apps/web/src/renderClient.ts](apps/web/src/renderClient.ts) polls indefinitely while a job remains queued or rendering | Polling has timeout/cancellation, bounded backoff, and a recoverable job URL or identifier; timeout and cancellation tests pass |
| G-008 | P1 | Add end-to-end deployment verification | Partial | [.github/workflows/deploy-and-test.yml](.github/workflows/deploy-and-test.yml) passed submit, status, both dimensions, and download against Azure in run `31845522738`; metadata download remains outside the current API contract | CI runs a deployed-environment smoke test that verifies submit, status, metadata, both dimensions, and download |

## Product Requirement Gaps

| ID | Priority | Work item | Status | Evidence | Exit criteria |
| --- | --- | --- | --- | --- | --- |
| G-009 | P1 | Define the supported MVP requirement surface | Partial | [docs/requirements.md](docs/requirements.md) specifies controls not present in the request contract, including research preset, camera roll, outer radius, emissivity profile, spectral index, background source, and lensing quality | Requirements distinguish current MVP acceptance criteria from reference-render roadmap; every MVP field maps through UI, schema, API, worker, metadata, and tests |
| G-010 | P2 | Add selectable provenance-rich backgrounds | Partial | The preview and worker use one packaged Webb image or procedural stars; source selection and user images are absent | Webb, Hubble, procedural, and approved user-image paths preserve source and crop provenance |

## Scientific Fidelity Roadmap

| ID | Priority | Work item | Status | Exit criteria |
| --- | --- | --- | --- | --- |
| G-011 | P2 | Implement reference Kerr backwards ray tracing | Deferred | Kerr geodesics, strong-field lensing, disk intersections, and validation corpus are isolated from the fast renderer |
| G-012 | P2 | Implement relativistic transfer and ISCO constraints | Deferred | Ray-specific redshift/Doppler transfer and spin/flow-derived ISCO are validated against an established reference |
| G-013 | P3 | Add GRMHD, polarization, and observing-frequency modes | Deferred | Research inputs and outputs have explicit provenance, validation bounds, and an isolated compute tier |
| G-014 | P3 | Evaluate an optional GPU worker | Deferred | CPU quality and demand justify cost; GPU infrastructure remains opt-in and independently metered |

## Verification Commands

Run these before changing an item to Done:

```powershell
npm --prefix apps/web test
npm --prefix apps/web run lint
npm --prefix apps/web run build
Push-Location services/render-api; python -m pytest; Pop-Location
Push-Location services/render-worker; python -m pytest; Pop-Location
```

For deployment state:

```powershell
az staticwebapp environment list --name swa-gravitas-434092 --resource-group rg-gravitas --output table
az containerapp list --resource-group rg-gravitas --output table
```

## Maintenance Rules

1. Update `Last audited` whenever health evidence or priorities are reviewed.
2. Add one row per independently verifiable outcome; avoid progress percentages.
3. Move an item to Done only after its exit criteria pass in the relevant environment.
4. Keep scientific roadmap work Deferred until the current release objective is complete or deliberately changed.
5. Record durable implementation detail in the owning code or technical document; keep this file focused on status, evidence, and exit criteria.
