# Gravitas Render Worker

This service will consume `render-jobs` from Azure Storage Queue and produce both required wallpaper dimensions with JSON provenance sidecars.

The worker is deliberately not deployed until the shared render contract and CPU renderer are implemented.
