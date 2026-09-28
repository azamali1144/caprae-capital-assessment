from fastapi import FastAPI

app = FastAPI(title="LeadLens API", version="0.1.0")


@app.get("/")
async def root():
    return {"name": "leadlens", "status": "up"}
