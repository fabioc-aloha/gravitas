FROM python:3.12-slim

WORKDIR /app
COPY services/render-worker/pyproject.toml ./
COPY services/render-worker/gravitas_renderer ./gravitas_renderer
COPY apps/web/public/backgrounds/webb-carina.webp ./gravitas_renderer/assets/webb-carina.webp
RUN pip install --no-cache-dir .

ENV RENDER_BACKGROUND_PATH=/app/gravitas_renderer/assets/webb-carina.webp
CMD ["python", "-m", "gravitas_renderer.worker"]
