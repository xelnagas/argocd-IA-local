import sys
sys.path.append("/app/mcp_server")
import server

# Test edit_image
retouched = server.edit_image(
    prompt="add holographic flying vehicles and neon pink signs",
    parent_image_id="jarvis_20261003_204948_73556d.png",
    denoising_strength=0.45
)
print("[+] Retouched result:", retouched)

# Test upscale_image
upscaled = server.upscale_image(
    image_id="jarvis_20261003_204948_73556d.png",
    scale=2
)
print("[+] Upscaled result:", upscaled)
