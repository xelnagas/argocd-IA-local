#!/usr/bin/env python3
"""
Master Test Runner : Suite Complète de Tests Fonctionnels J.A.R.V.I.S.
Exécute tous les tests de validation de bout en bout et génère un bilan consolidé.
"""
import sys
import time
import traceback

# Liste des modules de test
TESTS = [
    ("Interface WebUI & Ingress", "test_functional_webui"),
    ("Moteur Inférence LLM CUDA (Ollama)", "test_functional_llm"),
    ("Pipeline Vocal (STT Whisper & TTS Kokoro)", "test_functional_voice"),
    ("Second Cerveau Vectoriel (Qdrant)", "test_functional_second_brain"),
    ("Studio Visuel SDXL Lightning", "test_functional_image_studio"),
]

def run_suite():
    print("\n" + "=" * 70)
    print("   J.A.R.V.I.S. PLATFORM - SUITE COMPLÈTE DE TESTS FONCTIONNELS")
    print("=" * 70)
    print(f"Horodatage : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Cible      : Cluster Bi-GPU K3s (linux2 / mini)")
    print("=" * 70 + "\n")

    results = []
    total_start = time.time()

    for name, module_name in TESTS:
        print(f"\n>>> [RUNNING] {name} ({module_name}.py)...")
        t0 = time.time()
        success = False
        error_msg = ""
        try:
            # Importer dynamiquement et exécuter
            mod = __import__(module_name)
            # Exécuter les fonctions du module
            if hasattr(mod, "test_webui_frontend"):
                mod.test_webui_frontend()
                mod.test_webui_api_version()
                mod.test_webui_api_config()
            elif hasattr(mod, "test_ollama_tags"):
                models = mod.test_ollama_tags()
                mod.test_ollama_embedding()
                target_model = "jarvis:latest" if any("jarvis" in m for m in models) else ("gemma2:9b" if "gemma2:9b" in models else models[0])
                mod.test_ollama_generate(target_model)
            elif hasattr(mod, "test_stt_health"):
                mod.test_stt_health()
                mod.test_tts_health()
                mod.test_tts_synthesis()
            elif hasattr(mod, "test_qdrant_collections"):
                mod.test_qdrant_collections()
                mod.test_qdrant_telemetry()
            elif hasattr(mod, "test_studio_health"):
                mod.test_studio_health()
                img_id, img_url = mod.test_studio_t2i()
                mod.test_studio_image_serving(img_url)
                upscaled_url = mod.test_studio_upscale(img_id)
                mod.test_studio_image_serving(upscaled_url)
            success = True
        except Exception as e:
            error_msg = str(e)
            traceback.print_exc()

        elapsed = time.time() - t0
        status_label = "PASS" if success else "FAIL"
        results.append((name, status_label, elapsed, error_msg))
        print(f">>> [{status_label}] {name} terminé en {elapsed:.2f}s")

    total_duration = time.time() - total_start

    # Bilan récapitulatif
    print("\n" + "=" * 70)
    print("               SYNTHÈSE GLOBALE DES TESTS FONCTIONNELS")
    print("=" * 70)
    print(f"{'Composant':<45} | {'Statut':<8} | {'Durée':<8}")
    print("-" * 70)

    all_passed = True
    for name, status, elapsed, err in results:
        indicator = "🟢 PASS" if status == "PASS" else "🔴 FAIL"
        print(f"{name:<45} | {indicator:<8} | {elapsed:>6.2f}s")
        if status != "PASS":
            all_passed = False
            if err:
                print(f"    └── Erreur : {err}")

    print("-" * 70)
    passed_count = sum(1 for _, s, _, _ in results if s == "PASS")
    total_count = len(results)
    rate = (passed_count / total_count) * 100
    print(f"Total : {passed_count}/{total_count} passés ({rate:.0f}%) en {total_duration:.2f}s")
    print("=" * 70 + "\n")

    if all_passed:
        print("🎉 SUCCÈS TOTAL : Tous les services fonctionnent de façon nominale !")
        sys.exit(0)
    else:
        print("❌ ÉCHEC : Certains tests n'ont pas abouti.")
        sys.exit(1)

if __name__ == "__main__":
    # Ajouter le dossier courant au sys.path
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    run_suite()
