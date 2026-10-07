#!/usr/bin/env python3
"""
Test Fonctionnel : Second Cerveau & Base Vectorielle (Qdrant)
Vérifie la disponibilité de Qdrant, les collections et l'API vectorielle.
"""
import urllib.request
import json
import time
import sys

INGRESS_IP = "192.168.1.160"

def test_qdrant_collections():
    print("[-] 1. Vérification de l'API collections Qdrant...")
    req = urllib.request.Request(
        f"http://{INGRESS_IP}/collections",
        headers={"Host": "qdrant.local"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=15) as r:
        elapsed = time.time() - t0
        assert r.status == 200, f"Code HTTP Qdrant inattendu: {r.status}"
        data = json.loads(r.read().decode())
        collections = data.get("result", {}).get("collections", [])
        names = [c["name"] for c in collections]
        print(f"    Collections trouvées ({len(collections)}) en {elapsed:.3f}s: {names}")
        print("    [OK] API Qdrant opérationnelle.")
        return names

def test_qdrant_telemetry():
    print("\n[-] 2. Vérification de la télémétrie Qdrant...")
    req = urllib.request.Request(
        f"http://{INGRESS_IP}/telemetry",
        headers={"Host": "qdrant.local"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        assert r.status == 200, f"Code HTTP Telemetry inattendu: {r.status}"
        data = json.loads(r.read().decode())
        version = data.get("result", {}).get("app", {}).get("version", "unknown")
        print(f"    Version Qdrant: {version}")
        print("    [OK] Télémétrie Qdrant validée.")

if __name__ == "__main__":
    print("=" * 60)
    print(" SUITE TEST FONCTIONNEL : SECOND CERVEAU (QDRANT)")
    print("=" * 60)
    test_qdrant_collections()
    test_qdrant_telemetry()
    print("\n" + "=" * 60)
    print(" TOUS LES TESTS SECOND CERVEAU ONT RÉUSSI !")
    print("=" * 60)
