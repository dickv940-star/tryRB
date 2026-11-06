import asyncio
import io
import logging
import os
import secrets
from functools import partial

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("tryrb")

API_TOKEN = os.getenv("TRYRB_API_TOKEN", "").strip()
if len(API_TOKEN) < 24:
    raise RuntimeError("TRYRB_API_TOKEN must be set to a random secret of at least 24 characters.")

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "25000000"))
MAX_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "50000000"))
ALLOWED_MODELS = {"birefnet-general", "birefnet-portrait", "bria-rmbg"}

app = FastAPI(title="tryRB private background-removal API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

model_sessions = {}
inference_lock = asyncio.Semaphore(1)


def check_token(authorization: str | None) -> None:
    expected = f"Bearer {API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Token akses tidak valid.")


def process_image(
    image_bytes: bytes,
    model_name: str,
    alpha_matting: bool,
    decontaminate: bool,
    vitmatte: bool,
) -> bytes:
    # Import rembg only when the first image is processed; API startup stays light.
    from rembg import new_session, remove

    session = model_sessions.get(model_name)
    if session is None:
        session = new_session(model_name)
        model_sessions[model_name] = session

    return remove(
        image_bytes,
        session=session,
        alpha_matting=alpha_matting,
        decontaminate=(decontaminate and not alpha_matting),
        vitmatte=vitmatte,
        force_return_bytes=True,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tryRB", "models": sorted(ALLOWED_MODELS)}


@app.post("/api/remove")
async def remove_background(
    file: UploadFile = File(...),
    model: str = Form("birefnet-general"),
    a: bool = Form(False),
    dc: bool = Form(True),
    vm: bool = Form(False),
    authorization: str | None = Header(default=None),
):
    check_token(authorization)

    if model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Model tidak tersedia pada versi rembg ini.")

    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Format harus JPG, PNG, atau WEBP.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="File gambar kosong.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran file melewati batas server.")

    try:
        with Image.open(io.BytesIO(content)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(status_code=415, detail="Format gambar tidak didukung.")
            if image.width * image.height > MAX_PIXELS:
                raise HTTPException(status_code=413, detail="Resolusi gambar melewati batas server.")
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="File bukan gambar valid atau gambar rusak.")

    try:
        async with inference_lock:
            output = await run_in_threadpool(
                partial(process_image, content, model, a, dc, vm)
            )
    except Exception:
        logger.exception("Background removal failed")
        raise HTTPException(status_code=500, detail="Pemrosesan gagal. Periksa log backend.")

    return Response(content=output, media_type="image/png")


@app.exception_handler(HTTPException)
async def http_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
