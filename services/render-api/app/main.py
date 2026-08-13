from fastapi import FastAPI

app = FastAPI(title="Gravitas Render API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"service": "gravitas-render-api", "status": "ok"}
