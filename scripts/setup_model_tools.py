"""Associate jarvis_image_studio tool with models"""
import sqlite3
import json
import time

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

c.execute('SELECT id FROM user LIMIT 1')
user_id = c.fetchone()[0]
now = int(time.time())

models_to_configure = [
    ("jarvis:latest", "Jarvis (Assistant Principal)"),
    ("gemma2:9b", "Gemma 2 9B")
]

for model_id, model_name in models_to_configure:
    meta = {
        "toolIds": ["jarvis_image_studio"],
        "capabilities": {
            "vision": True,
            "image_generation": True,
            "web_search": True
        }
    }
    params = {}
    
    # Check if exists
    c.execute('SELECT id FROM model WHERE id = ?', (model_id,))
    if c.fetchone():
        c.execute('''
            UPDATE model SET
                name = ?,
                meta = ?,
                updated_at = ?
            WHERE id = ?
        ''', (model_name, json.dumps(meta), now, model_id))
        print(f"Updated model {model_id}")
    else:
        c.execute('''
            INSERT INTO model (id, user_id, base_model_id, name, params, meta, updated_at, created_at, is_active)
            VALUES (?, ?, NULL, ?, ?, ?, ?, ?, 1)
        ''', (model_id, user_id, model_name, json.dumps(params), json.dumps(meta), now, now))
        print(f"Inserted model {model_id}")

conn.commit()
conn.close()
print("Models successfully configured with jarvis_image_studio!")
