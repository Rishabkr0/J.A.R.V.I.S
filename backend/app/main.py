import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.ws import router as ws_router, voice_pipeline
from app.api.memory import router as memory_router

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    voice_pipeline.start()

@app.on_event("shutdown")
async def shutdown_event():
    voice_pipeline.stop()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(ws_router)
app.include_router(memory_router)

@app.get('/health')
async def health_check():
    return {
        'status': 'ok',
        'service': 'jarvis',
        'version': '0.1.0',
        'environment': settings.ENVIRONMENT
    }

if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.HOST, port=settings.PORT, reload=True)
