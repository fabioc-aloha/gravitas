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

## Rendering Roadmap and Priority

### Priority 0: Complete trustworthy export plumbing

1. Add signed Blob download URLs for completed jobs.
2. Deploy the queue-backed API and render worker to the existing Container Apps environment.
3. Persist job status transitions and dual-size output provenance.

### Priority 1: Make production exports visually natural

1. Use a real, provenance-tracked celestial-sphere source layer.
2. Replace flat disk geometry with a Novikov-Thorne-inspired radial emission profile.
3. Derive the reference-mode disk inner edge from spin and flow-direction ISCO constraints.
4. Apply physically marked blackbody color and an HDR tone-mapping stage.

### Priority 2: Implement the custom Kerr production renderer

1. Add escaped-ray background deflection to the Schwarzschild baseline.
2. Add thin-disk intersection and redshift transfer.
3. Move from Schwarzschild to Kerr constants of motion and semi-analytic geodesic lookup tables.
4. Generate a low-resolution validation suite covering M87*-informed, Sgr A*-informed, face-on, and high-inclination scenes.

### Priority 3: Validate against established GRRT software

1. Containerize ipole as an offline reference-render service.
2. Build a render corpus and measure shadow, ring-position, and brightness-asymmetry differences.
3. Use GYOTO only as an isolated subprocess/service after GPL distribution review.

### Priority 4: Add optional high-compute research quality

1. Evaluate GPU-capable Odyssey only after CPU quality and demand justify it.
2. Add GRMHD snapshot, polarization, magnetic-state, and observing-frequency transfer only when the reference tier can support them.

See `docs/research/rendering-methods.md` for software evaluation, method selection, citations, and licensing guardrails.
