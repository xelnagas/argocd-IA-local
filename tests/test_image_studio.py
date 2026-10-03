import urllib.request
import json
import time
import sys

BASE_URL = "http://192.168.1.160:30850"

def test_health():
    print("[-] 1. Checking /health...")
    req = urllib.request.Request(f"{BASE_URL}/health")
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode())
        print(f"    Health status: {res}")
        assert res.get("status") == "ready", "Pipeline not ready!"
        print("    [OK] Health check passed.")

def test_t2i():
    print("\n[-] 2. Testing Text-to-Image (Voice -> Image prompt simulation)...")
    payload = {
        "prompt": "portrait of a high-tech female engineer in a futuristic laboratory, cinematic lighting, 8k, photorealistic",
        "size": "1024x1024",
        "steps": 6,
        "guidance_scale": 2.0
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        res = json.loads(r.read().decode())
        elapsed = time.time() - t0
        print(f"    [OK] T2I completed in {elapsed:.2f}s!")
        img_url = res["data"][0]["url"]
        img_id = res["data"][0]["image_id"]
        print(f"    Image ID: {img_id}")
        print(f"    Image URL: {img_url}")
        return img_id, img_url

def test_i2i(parent_id, img_url):
    print("\n[-] 3. Testing Image-to-Image retouching (Conversational voice feedback)...")
    payload = {
        "parent_image_id": parent_id,
        "image_url": img_url,
        "prompt": "add holographic glowing cybernetic glasses and neon blue ambient accents, highly detailed",
        "denoising_strength": 0.45,
        "steps": 6,
        "guidance_scale": 2.0
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/images/edits",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        res = json.loads(r.read().decode())
        elapsed = time.time() - t0
        print(f"    [OK] Retouching completed in {elapsed:.2f}s!")
        retouched_id = res["data"][0]["image_id"]
        retouched_url = res["data"][0]["url"]
        print(f"    Retouched Image ID: {retouched_id}")
        print(f"    Retouched Image URL: {retouched_url}")
        return retouched_id, retouched_url

def test_upscale(image_id):
    print("\n[-] 4. Testing 4K Upscale (Ultra-HD Export)...")
    payload = {
        "image_id": image_id,
        "scale": 4
    }
    req = urllib.request.Request(
        f"{BASE_URL}/v1/images/upscale",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.loads(r.read().decode())
        elapsed = time.time() - t0
        print(f"    [OK] Upscale completed in {elapsed:.2f}s!")
        upscaled_url = res["data"][0]["url"]
        resolution = res["data"][0]["resolution"]
        print(f"    Resolution: {resolution}")
        print(f"    Upscaled URL: {upscaled_url}")
        return upscaled_url

def test_image_serving(url):
    print("\n[-] 5. Verifying image HTTP serving...")
    # Test via NodePort endpoint: convert http://jarvis.local/images/<file> to BASE_URL/images/<file>
    filename = url.split("/")[-1]
    direct_url = f"{BASE_URL}/images/{filename}"
    req = urllib.request.Request(direct_url)
    with urllib.request.urlopen(req, timeout=15) as r:
        content_type = r.headers.get("Content-Type")
        content_len = len(r.read())
        print(f"    Status: {r.status} OK | Content-Type: {content_type} | Size: {content_len} bytes")
        assert r.status == 200
        assert "image/png" in content_type
        print("    [OK] Image serving verified!")

if __name__ == "__main__":
    print("=" * 60)
    print(" J.A.R.V.I.S. Visual Studio - Full E2E Functional Test")
    print("=" * 60)
    test_health()
    img_id, img_url = test_t2i()
    test_image_serving(img_url)
    retouched_id, retouched_url = test_i2i(img_id, img_url)
    test_image_serving(retouched_url)
    upscaled_url = test_upscale(retouched_id)
    test_image_serving(upscaled_url)
    print("\n" + "=" * 60)
    print(" ALL 5/5 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)
