#!/usr/bin/env python3
"""
Test Fonctionnel : Moteur d'Inférence LLM GPU (Ollama)
Vérifie la disponibilité des modèles, la génération de texte et d'embeddings,
ainsi que l'absence d'erreurs CUDA Out Of Memory.
"""
import urllib.request
import json
import time
import sys

BASE_URL = "http://192.168.1.160:31434"

def test_ollama_tags():
    print("[-] 1. Vérification de l'endpoint /api/tags et des modèles disponibles...")
    req = urllib.request.Request(f"{BASE_URL}/api/tags")
    with urllib.request.urlopen(req, timeout=15) as r:
        assert r.status == 200, f"Code HTTP inattendu: {r.status}"
        data = json.loads(r.read().decode())
        model_names = [m["name"] for m in data.get("models", [])]
        print(f"    Modèles détectés: {model_names}")
        assert any("gemma2" in m or "jarvis" in m for m in model_names), "Aucun modèle principal trouvé!"
        assert any("nomic-embed" in m for m in model_names), "Modèle d'embedding nomic-embed-text absent!"
        print("    [OK] Endpoint /api/tags valide et modèles conformes.")
        return model_names

def test_ollama_embedding():
    print("\n[-] 2. Test du calcul d'embeddings vectoriels (nomic-embed-text)...")
    payload = {
        "model": "nomic-embed-text",
        "prompt": "J.A.R.V.I.S. Plateforme IA locale GitOps"
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as r:
        assert r.status == 200, f"Code HTTP inattendu: {r.status}"
        data = json.loads(r.read().decode())
        embedding = data.get("embedding", [])
        elapsed = time.time() - t0
        print(f"    Dimensions du vecteur: {len(embedding)} | Calculé en {elapsed:.3f}s")
        assert len(embedding) > 0, "Vecteur embedding vide!"
        print("    [OK] Calcul d'embedding réussi.")

def test_ollama_generate(model_name="gemma2:9b"):
    print(f"\n[-] 3. Test d'inférence LLM CUDA ({model_name})...")
    payload = {
        "model": model_name,
        "prompt": "Bonjour Jarvis. Donne un court statut en une phrase avec politesse.",
        "stream": False,
        "options": {
            "num_predict": 50,
            "temperature": 0.6
        }
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            assert r.status == 200, f"Code HTTP inattendu: {r.status}"
            data = json.loads(r.read().decode())
            elapsed = time.time() - t0
            response_text = data.get("response", "").strip()
            total_duration_ns = data.get("total_duration", 0)
            eval_count = data.get("eval_count", 0)
            eval_duration_ns = data.get("eval_duration", 1)
            tok_per_sec = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns else 0
            
            print(f"    Réponse générée en {elapsed:.2f}s (~{tok_per_sec:.1f} tok/s) :")
            print(f"    « {response_text} »")
            assert len(response_text) > 0, "Réponse vide générée par le modèle!"
            print("    [OK] Inférence GPU terminée avec succès (zéro CUDA error).")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"    [FAIL] HTTP Error {e.code}: {err_body}")
        assert False, f"Erreur inférence Ollama: {err_body}"

if __name__ == "__main__":
    print("=" * 60)
    print(" SUITE TEST FONCTIONNEL : MOTEUR D'INFÉRENCE LLM (CUDA)")
    print("=" * 60)
    models = test_ollama_tags()
    test_ollama_embedding()
    if any("jarvis" in m for m in models):
        test_ollama_generate("jarvis:latest")
    elif "gemma2:9b" in models:
        test_ollama_generate("gemma2:9b")
    else:
        test_ollama_generate(models[0])
    print("\n" + "=" * 60)
    print(" TOUS LES TESTS LLM CUDA ONT RÉUSSI !")
    print("=" * 60)
