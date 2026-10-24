from fastapi import FastAPI

from .api.routes import health, orders, predict

app = FastAPI(
    title="AeroSecure AI API",
    description="Backend API for the AeroSecure AI prototype",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(predict.router)
app.include_router(orders.router)


@app.get("/")
def root():
    return {"message": "AeroSecure AI backend is running"}