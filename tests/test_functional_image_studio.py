#!/usr/bin/env python3
"""
Test Fonctionnel : Studio Visuel J.A.R.V.I.S. (SDXL Lightning & FastAPI)
Vérifie la disponibilité du pipeline, la génération d'images, la retouche et le service de fichiers.
"""
import urllib.request
import json
import time
import sys

BASE_URL = "http://192.168.1.160:30850"

def test_studio_health():
    print("[-] 1. Vérification de l'endpoint /health du Studio Visuel...")
    req = urllib.request.Request(f"{BASE_URL}/health")
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode())
        print(f"    Statut du pipeline: {res}")
        assert res.get("status") == "ready", "Pipeline non prêt ou en erreur!"
        print("    [OK] Health check Studio Visuel validé.")

def test_studio_t2i():
    print("\n[-] 2. Test Text-to-Image (SDXL Lightning 1024x1024)...")
    payload = {
        "prompt": "futuristic quantum server room, glowing blue circuits, ultra-detailed photorealistic, 8k",
        "size": "1024x1024",
        "steps": 4,
        "guidance_scale": 1.5
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
        print(f"    [OK] Rendu T2I généré avec succès en {elapsed:.2f}s !")
        img_url = res["data"][0]["url"]
        img_id = res["data"][0]["image_id"]
        print(f"    Image ID : {img_id}")
        print(f"    Image URL: {img_url}")
        return img_id, img_url

def test_studio_image_serving(img_url):
    print("\n[-] 3. Vérification de la distribution HTTP du fichier image...")
    filename = img_url.split("/")[-1]
    direct_url = f"{BASE_URL}/images/{filename}"
    req = urllib.request.Request(direct_url)
    with urllib.request.urlopen(req, timeout=15) as r:
        content_type = r.headers.get("Content-Type")
        data = r.read()
        print(f"    Statut: {r.status} OK | Type: {content_type} | Poids: {len(data)} octets")
        assert r.status == 200, "Échec téléchargement image!"
        assert "image/png" in content_type, f"Content-type inattendu: {content_type}"
        print("    [OK] Distribution HTTP de l'image confirmée.")

def test_studio_upscale(img_id):
    print("\n[-] 4. Test Upscale Ultra-HD (super-résolution)...")
    payload = {
        "image_id": img_id,
        "scale": 2
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
        print(f"    [OK] Upscale terminé en {elapsed:.2f}s !")
        upscaled_url = res["data"][0]["url"]
        print(f"    Upscaled URL: {upscaled_url}")
        return upscaled_url

if __name__ == "__main__":
    print("=" * 60)
    print(" SUITE TEST FONCTIONNEL : STUDIO VISUEL GPU (SDXL LIGHTNING)")
    print("=" * 60)
    test_studio_health()
    img_id, img_url = test_studio_t2i()
    test_studio_image_serving(img_url)
    upscaled_url = test_studio_upscale(img_id)
    test_studio_image_serving(upscaled_url)
    print("\n" + "=" * 60)
    print(" TOUS LES TESTS DU STUDIO VISUEL ONT RÉUSSI !")
    print("=" * 60)
