"""Register Jarvis Studio Visuel tool in Open WebUI"""
import urllib.request
import json
import sqlite3
import sys

# Get user token
conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()
c.execute('SELECT id FROM user LIMIT 1')
row = c.fetchone()
if not row:
    print("No user found in DB")
    sys.exit(1)
user_id = row[0]
conn.close()

sys.path.insert(0, '/app/backend')
from open_webui.utils.auth import create_token
token = create_token({'id': user_id})

tool_content = '''"""
title: Jarvis Studio Visuel
author: Jarvis
description: Génération et retouche d'images photoréalistes en haute résolution sur GPU local
version: 1.0.0
"""

import requests
import json

class Tools:
    def __init__(self):
        pass

    def generate_image(self, prompt: str) -> str:
        """
        Génère une image photoréaliste ou artistique via le Studio Visuel GPU local.
        :param prompt: Description photographique détaillée en anglais (cadrage, lumière, sujet, style 85mm photo).
        :return: Le lien Markdown de l'image générée.
        """
        try:
            res = requests.post(
                "http://jarvis-image-gen.jarvis-system.svc.cluster.local:8000/v1/images/generations",
                json={"prompt": prompt, "steps": 6, "guidance_scale": 2.0},
                timeout=120
            )
            data = res.json()
            item = data["data"][0]
            url = item["url"]
            img_id = item.get("image_id", "")
            dur = item.get("duration_seconds", 0)
            if "svc.cluster.local" in url:
                url = f"http://jarvis.local/images/{img_id}"
            return f"![Image générée]({url})\\n\\n*(Image `{img_id}` générée en {dur}s)*"
        except Exception as e:
            return f"Erreur génération d'image: {e}"

    def edit_image(self, prompt: str, parent_image_id: str = "") -> str:
        """
        Retouche ou modifie une image existante.
        :param prompt: Consignes des modifications souhaitées en anglais.
        :param parent_image_id: Identifiant de l'image précédente.
        :return: Le lien Markdown de l'image retouchée.
        """
        try:
            payload = {"prompt": prompt, "denoising_strength": 0.45, "steps": 6, "guidance_scale": 2.0}
            if parent_image_id:
                payload["parent_image_id"] = parent_image_id
            res = requests.post(
                "http://jarvis-image-gen.jarvis-system.svc.cluster.local:8000/v1/images/edits",
                json=payload,
                timeout=120
            )
            data = res.json()
            item = data["data"][0]
            url = item["url"]
            img_id = item.get("image_id", "")
            dur = item.get("duration_seconds", 0)
            if "svc.cluster.local" in url:
                url = f"http://jarvis.local/images/{img_id}"
            return f"![Image retouchée]({url})\\n\\n*(Image `{img_id}` retouchée en {dur}s)*"
        except Exception as e:
            return f"Erreur retouche d'image: {e}"
'''

payload = {
    'id': 'jarvis_image_studio',
    'name': 'Jarvis Studio Visuel',
    'content': tool_content,
    'meta': {
        'description': "Génération et retouche d'images photoréalistes sur GPU local"
    }
}

req = urllib.request.Request(
    'http://localhost:8080/api/v1/tools/create',
    data=json.dumps(payload).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
)

try:
    with urllib.request.urlopen(req) as r:
        print("TOOL CREATED:")
        print(r.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode())
except Exception as e:
    print("ERROR:", e)
