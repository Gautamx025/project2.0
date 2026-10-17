from fastapi import FastAPI

app = FastAPI(title="Snap-2-Store", version="1.0.0")

@app.get("/api/health")
def health():
    return {"status": "ok", "milestone": "M1"}
