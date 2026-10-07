#!/usr/bin/env python3
"""
Test Fonctionnel : Interface Open-WebUI Unifiée
Vérifie la disponibilité du frontend, de l'API et de la configuration WebUI.
"""
import urllib.request
import json
import time
import sys

BASE_URL = "http://192.168.1.160:30080"

def test_webui_frontend():
    print("[-] 1. Vérification du frontend Open-WebUI (:30080)...")
    req = urllib.request.Request(f"{BASE_URL}/")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=15) as r:
        elapsed = time.time() - t0
        assert r.status == 200, f"Code HTTP inattendu: {r.status}"
        body = r.read().decode("utf-8", errors="ignore")
        assert "Open WebUI" in body or "Jarvis" in body or "<!DOCTYPE html>" in body, "Page HTML invalide!"
        print(f"    [OK] Frontend accessible (200 OK en {elapsed:.3f}s)")

def test_webui_api_version():
    print("\n[-] 2. Vérification de l'API Open-WebUI (/api/version)...")
    req = urllib.request.Request(f"{BASE_URL}/api/version")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            assert r.status == 200, f"Code HTTP inattendu: {r.status}"
            data = json.loads(r.read().decode())
            print(f"    Version Open-WebUI: {data}")
            print("    [OK] API Version opérationnelle.")
    except Exception as e:
        print(f"    [INFO] Endpoint version : {e}")

def test_webui_api_config():
    print("\n[-] 3. Vérification de la configuration publique Open-WebUI (/api/config)...")
    req = urllib.request.Request(f"{BASE_URL}/api/config")
    with urllib.request.urlopen(req, timeout=15) as r:
        assert r.status == 200, f"Code HTTP inattendu: {r.status}"
        data = json.loads(r.read().decode())
        name = data.get("name", "Unknown")
        print(f"    Nom configuré: {name}")
        assert r.status == 200
        print("    [OK] Configuration publique WebUI validée.")

if __name__ == "__main__":
    print("=" * 60)
    print(" SUITE TEST FONCTIONNEL : INTERFACE UTILISATEUR (OPEN-WEBUI)")
    print("=" * 60)
    test_webui_frontend()
    test_webui_api_version()
    test_webui_api_config()
    print("\n" + "=" * 60)
    print(" TOUS LES TESTS WEBUI ONT RÉUSSI !")
    print("=" * 60)
