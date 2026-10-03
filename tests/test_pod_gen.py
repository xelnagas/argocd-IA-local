import torch
import time
from diffusers import AutoPipelineForText2Image, EulerDiscreteScheduler

cache_dir = "/app/cache/diffusers"
model_id = "SG161222/RealVisXL_V4.0_Lightning"

print("[-] Loading pipeline from cache...")
t0 = time.time()
pipe = AutoPipelineForText2Image.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    variant="fp16",
    cache_dir=cache_dir,
    local_files_only=True
)
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
pipe.enable_model_cpu_offload()
print("[-] Loaded in", round(time.time() - t0, 2), "seconds")

print("[-] Generating test image...")
t0 = time.time()
gen = torch.Generator(device="cpu").manual_seed(42)
img = pipe(
    "photorealistic portrait of a robotic astronaut on Mars, 8k, cinematic lighting",
    num_inference_steps=6,
    guidance_scale=2.0,
    generator=gen
).images[0]
print("[+] Generated in", round(time.time() - t0, 2), "seconds!")
img.save("/tmp/test_cat.png")
print("[+] Saved to /tmp/test_cat.png successfully!")
