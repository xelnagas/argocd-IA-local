"""
J.A.R.V.I.S. Visual Studio - Local Microservice for Photorealistic Image Generation & Editing
Compatible with OpenAI /v1/images/generations and /v1/images/edits
Built for Kubernetes with SDXL Lightning, Diffusers, Auto CPU-Offload & Dual-GPU clustering.
"""

import os
import io
import time
import uuid
import logging
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, ImageEnhance
import torch

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis-image-gen")

# Configuration via Environment Variables
MODEL_ID = os.getenv("MODEL_ID", "SG161222/RealVisXL_V4.0_Lightning")
DIFFUSERS_CACHE_DIR = os.getenv("DIFFUSERS_CACHE_DIR", "/app/cache/diffusers")
STORAGE_DIR = os.getenv("STORAGE_DIR", "/app/storage/generated-images")
PUBLIC_IMAGE_URL_PREFIX = os.getenv("PUBLIC_IMAGE_URL_PREFIX", "http://jarvis.local/images")
ENABLE_CPU_OFFLOAD = os.getenv("ENABLE_CPU_OFFLOAD", "auto").lower()
DEFAULT_STEPS = int(os.getenv("DEFAULT_STEPS", "6"))
DEFAULT_GUIDANCE = float(os.getenv("DEFAULT_GUIDANCE", "2.0"))

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(DIFFUSERS_CACHE_DIR, exist_ok=True)

app = FastAPI(
    title="J.A.R.V.I.S. Image Studio API",
    description="Photorealistic Image Generation & Conversational Retouching for J.A.R.V.I.S.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipelines state
t2i_pipeline = None
i2i_pipeline = None
is_pipeline_ready = False
device_info = {}

PHOTOREALISTIC_NEGATIVE_PROMPT = (
    "ugly, deformed, disfigured, poor anatomy, bad anatomy, bad hands, missing limbs, "
    "floating limbs, disconnected limbs, extra fingers, cartoon, 3d render, anime, "
    "illustration, drawing, digital art, blur, blurry, watermark, signature, oversaturated, "
    "low quality, worst quality, text, font, logo"
)

ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 864),
    "3:4": (864, 1152),
    "21:9": (1536, 640),
}


def load_pipelines():
    global t2i_pipeline, i2i_pipeline, is_pipeline_ready, device_info
    try:
        from diffusers import AutoPipelineForText2Image, AutoPipelineForImage2Image, EulerDiscreteScheduler

        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
        device_info["cuda_available"] = cuda_available
        device_info["device_name"] = device_name
        device_info["model_id"] = MODEL_ID

        logger.info(f"Loading diffusion model '{MODEL_ID}' on device: {device_name}")

        dtype = torch.float16 if cuda_available else torch.float32

        t2i_pipeline = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            variant="fp16" if cuda_available else None,
            cache_dir=DIFFUSERS_CACHE_DIR,
        )

        # Use trailing scheduler configuration suited for Lightning checkpoints
        t2i_pipeline.scheduler = EulerDiscreteScheduler.from_config(
            t2i_pipeline.scheduler.config, timestep_spacing="trailing"
        )

        # Optimize VRAM footprint
        t2i_pipeline.enable_vae_slicing()
        t2i_pipeline.enable_vae_tiling()

        # Decide memory strategy
        if cuda_available:
            total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free_vram = (torch.cuda.mem_get_info()[0]) / (1024**3)
            device_info["total_vram_gb"] = round(total_vram, 2)
            device_info["free_vram_gb"] = round(free_vram, 2)

            if ENABLE_CPU_OFFLOAD == "sequential" or (ENABLE_CPU_OFFLOAD == "auto" and free_vram < 2.5):
                logger.info(f"Activating sequential CPU-offload (VRAM free: {free_vram:.2f}GB / {total_vram:.2f}GB)")
                t2i_pipeline.enable_sequential_cpu_offload()
                device_info["memory_strategy"] = "sequential_cpu_offload"
            elif ENABLE_CPU_OFFLOAD == "true" or (ENABLE_CPU_OFFLOAD == "auto" and total_vram <= 12.0) or (ENABLE_CPU_OFFLOAD == "auto" and free_vram < 6.5):
                logger.info(f"Activating model CPU-offload (VRAM free: {free_vram:.2f}GB / {total_vram:.2f}GB)")
                t2i_pipeline.enable_model_cpu_offload()
                device_info["memory_strategy"] = "cpu_offload"
            else:
                logger.info(f"Direct CUDA loading on {device_name} (VRAM free: {free_vram:.2f}GB)")
                t2i_pipeline.to("cuda")
                device_info["memory_strategy"] = "direct_cuda"
        else:
            t2i_pipeline.to("cpu")
            device_info["memory_strategy"] = "cpu"

        # Image-to-Image pipeline shares the same underlying components (0 additional VRAM!)
        i2i_pipeline = AutoPipelineForImage2Image.from_pipe(t2i_pipeline)
        is_pipeline_ready = True
        logger.info("J.A.R.V.I.S. Visual Studio pipelines loaded successfully!")
    except Exception as e:
        logger.error(f"Error loading diffusion pipelines: {e}", exc_info=True)
        is_pipeline_ready = False


@app.on_event("startup")
async def startup_event():
    import threading
    # Load model asynchronously in background thread so container is immediately healthy
    thread = threading.Thread(target=load_pipelines)
    thread.daemon = True
    thread.start()


# Request / Response Models
class ImageGenerationRequest(BaseModel):
    prompt: str
    n: int = 1
    size: Optional[str] = "1024x1024"
    aspect_ratio: Optional[str] = "1:1"
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    steps: Optional[int] = DEFAULT_STEPS
    guidance_scale: Optional[float] = DEFAULT_GUIDANCE


class ImageEditRequest(BaseModel):
    prompt: str
    parent_image_id: Optional[str] = None
    image_url: Optional[str] = None
    denoising_strength: Optional[float] = 0.45
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    steps: Optional[int] = DEFAULT_STEPS
    guidance_scale: Optional[float] = DEFAULT_GUIDANCE


class ImageUpscaleRequest(BaseModel):
    image_id: str
    scale: Optional[int] = 2


@app.get("/health")
def health():
    free_gb = 0.0
    if torch.cuda.is_available():
        free_gb = round(torch.cuda.mem_get_info()[0] / (1024**3), 2)
    return {
        "status": "ready" if is_pipeline_ready else "loading",
        "pipeline_ready": is_pipeline_ready,
        "device": device_info,
        "free_vram_gb": free_gb,
    }


@app.api_route("/images/{filename}", methods=["GET", "HEAD"])
def get_image(filename: str):
    file_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path, media_type="image/png")


@app.post("/v1/images/generations")
def generate_images(req: ImageGenerationRequest):
    if not is_pipeline_ready or t2i_pipeline is None:
        raise HTTPException(status_code=503, detail="Model is still loading into GPU. Please retry in a few seconds.")

    # Determine dimensions
    width, height = 1024, 1024
    if req.aspect_ratio in ASPECT_RATIOS:
        width, height = ASPECT_RATIOS[req.aspect_ratio]
    elif req.size:
        try:
            parts = req.size.lower().split("x")
            width, height = int(parts[0]), int(parts[1])
        except Exception:
            width, height = 1024, 1024

    # Determine seed
    seed = req.seed if req.seed is not None else int(time.time() * 1000) % (2**31)
    generator = torch.Generator(device="cpu").manual_seed(seed)

    neg_prompt = req.negative_prompt if req.negative_prompt else PHOTOREALISTIC_NEGATIVE_PROMPT

    logger.info(f"Generating image: '{req.prompt[:80]}...' | {width}x{height} | Steps: {req.steps} | Seed: {seed}")
    start_time = time.time()

    with torch.inference_mode():
        output = t2i_pipeline(
            prompt=req.prompt,
            negative_prompt=neg_prompt,
            width=width,
            height=height,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance_scale,
            generator=generator,
        )

    duration = round(time.time() - start_time, 2)
    generated_data = []

    for idx, image in enumerate(output.images):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        filename = f"jarvis_{timestamp}_{unique_id}.png"
        filepath = os.path.join(STORAGE_DIR, filename)
        image.save(filepath, format="PNG")

        image_url = f"{PUBLIC_IMAGE_URL_PREFIX}/{filename}"
        generated_data.append({
            "url": image_url,
            "image_id": filename,
            "seed": seed,
            "duration_seconds": duration,
            "revised_prompt": req.prompt,
        })
        logger.info(f"Saved generated image to {filepath} in {duration}s")

    return {
        "created": int(time.time()),
        "data": generated_data,
    }


@app.post("/v1/images/edits")
def edit_image(req: ImageEditRequest):
    if not is_pipeline_ready or i2i_pipeline is None:
        raise HTTPException(status_code=503, detail="Model is still loading into GPU.")

    # Locate source image
    source_filename = req.parent_image_id
    if not source_filename and req.image_url:
        source_filename = req.image_url.split("/")[-1]

    if not source_filename:
        # If no parent specified, find latest image
        files = [f for f in os.listdir(STORAGE_DIR) if f.endswith(".png")]
        if not files:
            raise HTTPException(status_code=400, detail="No source image found to edit.")
        files.sort(key=lambda x: os.path.getmtime(os.path.join(STORAGE_DIR, x)), reverse=True)
        source_filename = files[0]

    source_path = os.path.join(STORAGE_DIR, source_filename)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail=f"Source image '{source_filename}' not found.")

    init_image = Image.open(source_path).convert("RGB")

    seed = req.seed if req.seed is not None else int(time.time() * 1000) % (2**31)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    neg_prompt = req.negative_prompt if req.negative_prompt else PHOTOREALISTIC_NEGATIVE_PROMPT

    strength = max(0.1, min(0.9, req.denoising_strength if req.denoising_strength else 0.45))
    logger.info(f"Editing image '{source_filename}' | Strength: {strength} | Prompt: '{req.prompt[:80]}...'")

    start_time = time.time()
    with torch.inference_mode():
        output = i2i_pipeline(
            prompt=req.prompt,
            image=init_image,
            negative_prompt=neg_prompt,
            strength=strength,
            num_inference_steps=req.steps,
            guidance_scale=req.guidance_scale,
            generator=generator,
        )

    duration = round(time.time() - start_time, 2)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    filename = f"jarvis_edit_{timestamp}_{unique_id}.png"
    filepath = os.path.join(STORAGE_DIR, filename)
    output.images[0].save(filepath, format="PNG")

    image_url = f"{PUBLIC_IMAGE_URL_PREFIX}/{filename}"
    return {
        "created": int(time.time()),
        "data": [{
            "url": image_url,
            "image_id": filename,
            "parent_image_id": source_filename,
            "duration_seconds": duration,
            "seed": seed,
            "revised_prompt": req.prompt,
        }],
    }


@app.post("/v1/images/upscale")
def upscale_image(req: ImageUpscaleRequest):
    source_path = os.path.join(STORAGE_DIR, req.image_id)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Image not found for upscaling.")

    img = Image.open(source_path).convert("RGB")
    scale = max(2, min(4, req.scale if req.scale else 2))
    new_width = img.width * scale
    new_height = img.height * scale

    # High quality Lanczos resize + subtle unsharp masking for photo realism
    upscaled = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Sharpness(upscaled)
    upscaled = enhancer.enhance(1.25)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"jarvis_4k_{timestamp}_{req.image_id}"
    filepath = os.path.join(STORAGE_DIR, filename)
    upscaled.save(filepath, format="PNG")

    return {
        "created": int(time.time()),
        "data": [{
            "url": f"{PUBLIC_IMAGE_URL_PREFIX}/{filename}",
            "image_id": filename,
            "original_id": req.image_id,
            "resolution": f"{new_width}x{new_height}",
        }]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
