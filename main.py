from fastapi import FastAPI
from src.presentation.api.v1.routes import router as api_router
from src.scheduler.egg_count_scheduler import EggCountScheduler
from contextlib import asynccontextmanager
from src.config.logging import setup_logging

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = EggCountScheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
