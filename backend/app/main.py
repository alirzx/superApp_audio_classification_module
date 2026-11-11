import asyncio
import hmac
import logging
import time
from contextlib import asynccontextmanager
from typing import Callable
from fastapi import FastAPI,UploadFile,File,Form,Header,HTTPException,Depends,Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse,Response
from prometheus_client import Counter,Histogram,CONTENT_TYPE_LATEST,generate_latest
from app.core.config import Settings,MODELS
from app.inference.classifier import EfficientATClassifier
from app.services.classification import ClassificationService
from app.audio.validation import InvalidAudio,check_upload
from app.core.request_limits import RequestBodyLimitMiddleware

logger=logging.getLogger(__name__)
COUNTER=Counter("superapp_audio_requests_total","Audio classification requests",["status"])
LATENCY=Histogram("superapp_audio_request_seconds","Classification processing latency")

def create_app(settings: Settings|None=None,engine_factory: Callable=EfficientATClassifier):
    settings=settings or Settings()
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine=engine_factory(settings)
        await run_in_threadpool(engine.initialize)
        app.state.engine=engine
        app.state.service=ClassificationService(engine,settings)
        app.state.semaphore=asyncio.Semaphore(settings.max_concurrent_inference)
        yield
    app=FastAPI(title="SuperApp Audio Classification",version="1.0.0",lifespan=lifespan,
                docs_url=None if settings.app_env=="production" else "/docs",redoc_url=None)
    app.add_middleware(RequestBodyLimitMiddleware,max_bytes=settings.max_request_bytes)
    @app.middleware("http")
    async def security_headers(request: Request,call_next):
        response=await call_next(request)
        response.headers["Cache-Control"]="no-store"
        response.headers["X-Content-Type-Options"]="nosniff"
        return response
    def authorize(x_api_key: str|None=Header(default=None)):
        if settings.api_token and not hmac.compare_digest(x_api_key or "",settings.api_token):
            raise HTTPException(status_code=401,detail="Unauthorized")
    @app.get("/health/live")
    async def live(): return {"status":"alive"}
    @app.get("/health/ready")
    async def ready():
        if not getattr(getattr(app.state,"engine",None),"ready",False):
            return JSONResponse(status_code=503,content={"status":"not_ready"})
        return {"status":"ready","model":settings.model_name,"device":"cpu"}
    @app.get("/v1/models",dependencies=[Depends(authorize)])
    async def models():
        return {"models":[{"id":name,"default":name=="mn10_as","active":name==settings.model_name,
                "release":"v0.0.1","classes":527,"device":"cpu","published_map":spec["map"]}
                for name,spec in MODELS.items()]}
    @app.get("/v1/labels",dependencies=[Depends(authorize)])
    async def labels():
        return {"model":settings.model_name,"labels":[{"id":i,"name":label}
                for i,label in enumerate(app.state.engine.labels)]}
    @app.get("/metrics",dependencies=[Depends(authorize)])
    async def metrics():
        if not settings.enable_metrics: raise HTTPException(404)
        return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
    @app.post("/v1/classify",dependencies=[Depends(authorize)])
    async def classify(file: UploadFile=File(...),top_k: int|None=Form(None),threshold: float|None=Form(None)):
        k=settings.top_k if top_k is None else top_k
        threshold=settings.score_threshold if threshold is None else threshold
        if not 1<=k<=50 or not 0<=threshold<=1:
            await file.close()
            raise HTTPException(422,"top_k must be 1..50 and threshold 0..1")
        try:
            try:
                await asyncio.wait_for(app.state.semaphore.acquire(),timeout=settings.max_queue_wait_seconds)
            except asyncio.TimeoutError as exc:
                COUNTER.labels("busy").inc()
                raise HTTPException(503,"Inference busy",headers={"Retry-After":"3"}) from exc
            start=time.perf_counter()
            try:
                content=await file.read(settings.max_upload_mb*1024*1024+1)
                check_upload(content,file.filename or "",settings.max_upload_mb*1024*1024)
                result=await run_in_threadpool(app.state.service.process,content,
                                               (file.filename or "audio")[:160],k,threshold)
                COUNTER.labels("ok").inc()
                return result
            except InvalidAudio as exc:
                COUNTER.labels("invalid").inc()
                raise HTTPException(422,str(exc)) from exc
            except Exception:
                COUNTER.labels("error").inc()
                logger.exception("Audio classification failed")
                raise HTTPException(500,"Classification failed")
            finally:
                LATENCY.observe(time.perf_counter()-start)
                app.state.semaphore.release()
        finally:
            await file.close()
    return app

app=create_app()
