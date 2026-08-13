# Gravitas Azure Web App Implementation Plan

**Goal:** Deliver an Azure-hosted web app that previews and exports scientifically informed black-hole wallpapers in 5120×1440 and 3440×1440.

**Architecture:** A React/WebGPU client provides rapid visual feedback. An Azure API creates render jobs; CPU workers generate deterministic final assets and metadata in Blob Storage. A GPU reference-quality path remains optional until fidelity and demand justify its cost.

**Tech Stack:** React, TypeScript, WebGPU/WebGL, Python/FastAPI renderer, Azure Static Web Apps, Azure Functions or Container Apps, Azure Storage Queues, Blob Storage, Application Insights.

---

### Task 1: Initialize the monorepo

**Files:**
- Create: `apps/web`
- Create: `services/render-api`
- Create: `services/render-worker`
- Create: `packages/render-schema`

1. Create the TypeScript web application and Python rendering services.
2. Put the shared render request/response schema in a versioned package.
3. Add format, test, and type-check commands.

### Task 2: Define the render contract

**Files:**
- Create: `packages/render-schema/src/render-request.ts`
- Create: `services/render-api/tests/test_validation.py`

1. Define required dual-size outputs, all scene controls, algorithm mode, background provenance, and seed.
2. Reject invalid spins, perspective values, disk radii, and output dimensions.
3. Require a physical/artistic palette declaration in every request.

### Task 3: Build the WebGPU preview

**Files:**
- Create: `apps/web/src/renderer/preview.ts`
- Create: `apps/web/src/components/SceneControls.tsx`

1. Render a low-cost critical curve, disk warp, Doppler asymmetry, and lensed background approximation.
2. Add controls for physical and composition axes separately.
3. Label previews as approximations and show active research preset/source.

### Task 4: Implement queued final renders

**Files:**
- Create: `services/render-api/app/routes/renders.py`
- Create: `services/render-worker/app/worker.py`
- Create: `services/render-worker/app/export.py`

1. Submit validated requests to Azure Storage Queue.
2. Render both target sizes per job with independent crop framing.
3. Upload PNGs and JSON sidecars to Blob Storage.
4. Expose job status and signed download URLs.

### Task 5: Add physically informed renderer modes

**Files:**
- Create: `services/render-worker/app/fast_renderer.py`
- Create: `services/render-worker/app/kerr_reference.py`

1. Implement deterministic fast CPU output for default jobs.
2. Add optional Kerr backwards-ray-tracing mode with adaptive sampling near the critical curve.
3. Compare selected low-resolution scenes against GYOTO or ipole reference output; document rather than conceal differences.

### Task 6: Provision Azure infrastructure

**Files:**
- Create: `infra/main.bicep`
- Create: `infra/parameters.dev.json`

1. Provision Static Web Apps, Container Apps or Functions, Queue, Blob Storage, managed identities, and Application Insights.
2. Apply least-privilege role assignments and short-lived download URLs.
3. Keep GPU infrastructure disabled by default; provision it only for the reference-quality tier.

### Task 7: Test and deploy

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`

1. Test schema validation, deterministic render fixtures, output dimensions, and metadata provenance.
2. Deploy a development environment before any production subscription resources.
3. Track render duration, queue latency, export failures, and compute cost.

## Acceptance criteria

- The app previews a scene interactively and exports both required sizes from one request.
- Output metadata identifies preset, physical parameters, background source, palette mode, and algorithm mode.
- The default service runs without a dedicated GPU.
- GPU reference rendering is isolated as an explicitly selected, costed mode.
