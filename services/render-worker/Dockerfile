FROM python:3.12-slim

WORKDIR /app
COPY services/render-worker/pyproject.toml ./
COPY services/render-worker/gravitas_renderer ./gravitas_renderer
RUN pip install --no-cache-dir .

CMD ["python", "-m", "gravitas_renderer.worker"]
