#!/usr/bin/env python3
"""
Test Fonctionnel : Pipeline Vocal Voice-to-Voice (Kokoro TTS & Faster-Whisper STT)
Vérifie la disponibilité des services audio et la synthèse vocale française.
"""
import urllib.request
import json
import time
import sys

INGRESS_IP = "192.168.1.160"

def test_stt_health():
    print("[-] 1. Vérification du service Faster-Whisper STT (/health)...")
    req = urllib.request.Request(
        f"http://{INGRESS_IP}/health",
        headers={"Host": "stt.local"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=15) as r:
        elapsed = time.time() - t0
        assert r.status == 200, f"Code HTTP STT inattendu: {r.status}"
        print(f"    [OK] Faster-Whisper STT répond 200 OK en {elapsed:.3f}s")

def test_tts_health():
    print("\n[-] 2. Vérification du service Kokoro TTS (/health)...")
    req = urllib.request.Request(
        f"http://{INGRESS_IP}/health",
        headers={"Host": "tts.local"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=15) as r:
        elapsed = time.time() - t0
        assert r.status == 200, f"Code HTTP TTS inattendu: {r.status}"
        print(f"    [OK] Kokoro TTS répond 200 OK en {elapsed:.3f}s")

def test_tts_synthesis():
    print("\n[-] 3. Test de synthèse vocale française (voix ff_siwis)...")
    payload = {
        "model": "kokoro",
        "input": "Bonjour Monsieur Julien. Tous les systèmes sont nominaux.",
        "voice": "ff_siwis",
        "response_format": "mp3"
    }
    req = urllib.request.Request(
        f"http://{INGRESS_IP}/v1/audio/speech",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Host": "tts.local",
            "Content-Type": "application/json"
        }
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30) as r:
        assert r.status == 200, f"Erreur génération audio TTS: {r.status}"
        audio_data = r.read()
        elapsed = time.time() - t0
        print(f"    Synthèse audio générée en {elapsed:.2f}s | Taille du fichier: {len(audio_data)} octets")
        assert len(audio_data) > 1000, "Données audio trop petites ou corrompues!"
        print("    [OK] Synthèse vocale française validée avec succès.")

if __name__ == "__main__":
    print("=" * 60)
    print(" SUITE TEST FONCTIONNEL : PIPELINE VOCAL (STT / TTS)")
    print("=" * 60)
    test_stt_health()
    test_tts_health()
    test_tts_synthesis()
    print("\n" + "=" * 60)
    print(" TOUS LES TESTS VOCAUX ONT RÉUSSI !")
    print("=" * 60)
