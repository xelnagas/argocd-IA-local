# Plan d'Action : Déploiement du Studio Visuel J.A.R.V.I.S. (Génération & Retouche d'Images Vocales Bi-GPU)

| Métadonnée | Valeur |
| :--- | :--- |
| **Projet** | J.A.R.V.I.S. Studio Visuel & Retouche d'Images Photoréalistes par Commande Vocale |
| **Cahier des Charges** | [projetimage.md](file:///d:/devia/IAlocal/argocd-IA-local/projetimage.md) |
| **Dépôt GitOps** | `https://github.com/xelnagas/argocd-IA-local.git` (Branche `main`) |
| **Orchestration GitOps** | ArgoCD (Application `jarvis` dans `k8s/base/`) |
| **Nœud Primaire (Cognitif & Stockage)** | `linux2` (`192.168.1.160`, RTX 3070 8 Go VRAM, `/stockage` 2 To libres) |
| **Nœud Dédié (Studio Graphique)** | `mini` (`192.168.1.99`, RTX 2070 SUPER 8 Go VRAM) |
| **Haute Disponibilité** | Migration dynamique automatique des pods GPU inter-nœuds (Failover < 45s) |
| **Statut Global** | 🟡 **Planifié & Prêt pour Implémentation** |

---

## 1. Vue d'Ensemble & Jalons du Projet

```mermaid
gantt
    title Déploiement du Studio Visuel J.A.R.V.I.S. (Bi-GPU Élastique)
    dateFormat  YYYY-MM-DD
    section Phase 0 : Socle & Stockage
    Préparation dossier /stockage & NFS RWX    :p0_1, 2026-10-05, 1d
    section Phase 1 : Spécifications
    Contrat API OpenAI & schéma métadonnées    :p1_1, after p0_1, 1d
    section Phase 2 : Microservice Image
    Développement jarvis-image-gen (FastAPI)   :p2_1, after p1_1, 2d
    Intégration SDXL Lightning & Real-ESRGAN  :p2_2, after p2_1, 2d
    section Phase 3 : K8s & GitOps
    Manifests K8s (Affinité, Failover, PVC)   :p3_1, after p2_2, 2d
    Intégration ArgoCD & Ingress HTTP         :p3_2, after p3_1, 1d
    section Phase 4 : Voix & Tool Calling
    Outil MCP / Open WebUI Function image_gen :p4_1, after p3_2, 1d
    System Prompt J.A.R.V.I.S. (Photo 85mm)   :p4_2, after p4_1, 1d
    section Phase 5 : Retouche Conversationnelle
    Cycle Image-to-Image & Upscaling 4K       :p5_1, after p4_2, 2d
    section Phase 6 : Recette & Documentation
    Test vocal E2E, Test Failover & Manuel.md :p6_1, after p5_1, 2d
```

---

## 2. Déroulé Détaillé des Phases & Actions

### 📦 Phase 0 : Socle Matériel & Stockage Partagé Inter-Nœuds (NFS RWX)
*Objectif : Mettre en place l'espace partagé sur `/stockage` pour que `linux2` et `mini` partagent les mêmes images et poids de modèles sans duplication.*

* [ ] **0.1. Création de l'arborescence sur `/stockage` (`linux2`)** :
  ```bash
  ssh julien@192.168.1.160 "sudo mkdir -p /stockage/system-storage/generated-images /stockage/system-storage/diffusers-cache && sudo chown -R 1000:1000 /stockage/system-storage/generated-images /stockage/system-storage/diffusers-cache"
  ```
* [ ] **0.2. Configuration du serveur NFS sur `linux2`** :
  - Exposer `/stockage/system-storage/generated-images` et `/stockage/system-storage/diffusers-cache` vers le réseau local `192.168.1.0/24` en lecture/écriture (`rw,sync,no_subtree_check,no_root_squash`).
* [ ] **0.3. Création du StorageClass & PersistentVolume K8s partagé (RWX)** :
  - Créer `k8s/base/image-gen/pvc-shared.yaml` monté en `accessModes: [ReadWriteMany]`.
* [ ] **0.4. Validation du montage NFS sur le nœud `mini`** :
  - Vérifier que `mini` peut lire et écrire instantanément dans le volume partagé.

---

### 📑 Phase 1 : Spécifications & Contrat d'Interface
*Objectif : Définir les protocoles HTTP et formats de messages entre Open WebUI, le LLM et le moteur de diffusion.*

* [ ] **1.1. Spécification des endpoints API standardisés** :
  - `POST /v1/images/generations` :
    ```json
    {
      "prompt": "Professional photograph of a modern loft...",
      "n": 1,
      "size": "1024x1024",
      "aspect_ratio": "16:9",
      "seed": 42
    }
    ```
  - `POST /v1/images/edits` :
    ```json
    {
      "parent_image_id": "photo_20261003_120401.png",
      "prompt": "Add a leather club armchair near the window",
      "denoising_strength": 0.45
    }
    ```
  - `POST /v1/images/upscale` :
    ```json
    {
      "image_id": "photo_20261003_120401.png",
      "scale": 4,
      "restore_faces": true
    }
    ```
  - `GET /images/{filename}` : Service HTTP pour le téléchargement et l'affichage direct dans Open WebUI.
* [ ] **1.2. Schéma de réponse & métadonnées JSON** :
  - Horodatage, identifiant unique, seed utilisé, URL web, temps d'inférence (ms).

---

### 🎨 Phase 2 : Développement du Microservice `jarvis-image-gen`
*Objectif : Construire le conteneur GPU combinant SDXL Lightning, Real-ESRGAN et l'API FastAPI.*

* [ ] **2.1. Initialisation du projet dans `services/image-gen/`** :
  - `Dockerfile` basé sur `nvidia/cuda:12.4.1-runtime-ubuntu22.04` ou `python:3.11-slim`.
  - Installation des dépendances : `torch`, `torchvision`, `diffusers`, `transformers`, `accelerate`, `xformers`, `fastapi`, `uvicorn`, `realesrgan`.
* [ ] **2.2. Pipeline de Diffusion Photoréaliste SDXL Lightning** :
  - Téléchargement du modèle de référence : `SG161222/RealVisXL_V4.0_Lightning` (inférence en 4 à 8 steps).
  - Intégration de la compilation de graphe et des optimisations VRAM (`enable_vae_slicing()`, `enable_vae_tiling()`).
  - Implémentation du mode dégradé `enable_model_cpu_offload()` activé automatiquement si le pod détecte qu'il partage un GPU avec Ollama.
* [ ] **2.3. Pipeline d'Édition Image-to-Image (I2I)** :
  - Chargement de l'image parent, conversion en espace latent, application de la force de débruitage modulée (`denoising_strength: 0.30 - 0.60`).
* [ ] **2.4. Module de Super-Résolution 4K (Real-ESRGAN / CodeFormer)** :
  - Intégration de la passe d'upscaling x4 pour passer de 1024x1024 à 4K Ultra-HD sur demande.
* [ ] **2.5. Serveur Web FastAPI & Endpoints** :
  - Implémentation des routes `/health`, `/v1/images/generations`, `/v1/images/edits`, `/v1/images/upscale` et `/images/{filename}`.
* [ ] **2.6. Build et publication de l'image de conteneur locale** :
  - Image taguée `jarvis-image-gen:latest` déployée sur le registre local ou importée dans containerd sur les nœuds.

---

### 🚀 Phase 3 : Manifests Kubernetes, Migration Élastique & GitOps ArgoCD
*Objectif : Déployer le service dans le cluster avec scheduling préférentiel sur `mini` et bascule transparente sur `linux2`.*

* [ ] **3.1. Création des manifests dans `k8s/base/image-gen/`** :
  - `deployment.yaml` :
    - Image : `jarvis-image-gen:latest`.
    - `runtimeClassName: nvidia`.
    - `resources.limits: { "nvidia.com/gpu": "1", "memory": "8Gi" }`.
    - **Affinité préférentielle** : Poids 100 sur `mini` (`gpu-model: rtx2070super`), fallback poids 50 sur `linux2` (`accelerator: nvidia-gpu`).
    - **Tolerations réactives (30s)** :
      ```yaml
      tolerations:
        - key: "node.kubernetes.io/not-ready"
          operator: "Exists"
          effect: "NoExecute"
          tolerationSeconds: 30
        - key: "node.kubernetes.io/unreachable"
          operator: "Exists"
          effect: "NoExecute"
          tolerationSeconds: 30
      ```
  - `service.yaml` : ClusterIP sur port 8000 + NodePort `30850`.
  - `pvc.yaml` : Montage du volume partagé NFS sur `/app/storage`.
  - `ingress.yaml` : Route Traefik `http://images.local/` et `http://jarvis.local/images/`.
* [ ] **3.2. Câblage dans `k8s/base/kustomization.yaml`** :
  - Ajouter `image-gen` dans la liste des composants `resources:`.
* [ ] **3.3. Déploiement et synchronisation via ArgoCD** :
  - Valider l'état **Synced** et **Healthy** dans ArgoCD.
  - Vérifier avec `kubectl get pod -n jarvis-system -o wide` que le pod tourne sur `mini` en mode nominal.

---

### 🎙️ Phase 4 : Intelligence Vocale, Tool Calling & Prompt Engineering
*Objectif : Permettre à J.A.R.V.I.S. de déclencher automatiquement la génération d'image sur simple consigne vocale.*

* [ ] **4.1. Développement du Tool MCP / Open WebUI Function** :
  - Créer l'outil `generate_image` appelant `http://jarvis-image-gen.jarvis-system.svc.cluster.local:8000/v1/images/generations`.
  - Renvoie le lien Markdown `![Description](http://jarvis.local/images/photo_xxx.png)`.
* [ ] **4.2. Intégration du System Prompt Expert Photographe dans le Modelfile de J.A.R.V.I.S.** :
  - Mettre à jour `k8s/base/inference-engine/configmap-modelfile.yaml` :
    ```dockerfile
    SYSTEM """
    Tu es J.A.R.V.I.S., assistant personnel et superviseur d'ingénierie.
    Lorsque Monsieur te demande de générer, imaginer, dessiner ou créer une image ou une photo :
    1. Déclenche immédiatement l'outil generate_image.
    2. Traduis et enrichis la demande en anglais sous forme d'un prompt photographique professionnel
       (focale 85mm f/1.4, éclairage volumétrique, grain de pellicule 35mm, textures réalistes, photorealistic raw photo).
    3. Confirme vocalement et courtoisement en français : "Voici le cliché demandé, Monsieur. Souhaitez-vous que j'y apporte des modifications ?"
    """
    ```
* [ ] **4.3. Re-génération du modèle `jarvis:latest` dans Ollama** :
  - Appliquer la mise à jour via `kubectl exec -n jarvis-system deploy/jarvis-inference -- ollama create jarvis:latest -f /etc/ollama/Modelfile`.

---

### 🔄 Phase 5 : Retouche Conversationnelle & Cycle Itératif (Edits / Upscale)
*Objectif : Permettre la modification continue de l'image précédente par consigne vocale ou texte.*

* [ ] **5.1. Développement du Tool `edit_image` et `upscale_image`** :
  - Détection automatique de référence à l'image précédente dans le contexte du chat.
  - Envoi de la requête `POST /v1/images/edits` avec l'identifiant parent.
* [ ] **5.2. Test du cycle de retouche** :
  - Test 1 : Commande initiale (*« Génère une photo de plage tropicale »*).
  - Test 2 : Modification (*« Ajoute un voilier au large et passe le ciel au coucher de soleil »*).
  - Validation du maintien de la composition et de la cohérence visuelle.
* [ ] **5.3. Test de la commande d'upscaling 4K** :
  - Commande (*« Agrandis l'image en 4K »*) ➔ Vérification de la livraison du fichier 3840x2160 pixels.

---

### ✅ Phase 6 : Recette de Bout-en-Bout, Stress-Tests & Documentation
*Objectif : Valider la fluidité, la résilience aux pannes et mettre à jour la documentation utilisateur.*

* [ ] **6.1. Recette Vocale E2E** :
  - Dictée au microphone dans Open WebUI :
    `Microphone ➔ Faster-Whisper STT ➔ Ollama LLM ➔ jarvis-image-gen (SDXL) ➔ Affichage WebUI ➔ Kokoro TTS (ff_siwis)`.
  - Chronométrage de la boucle complète (< 6 secondes).
* [ ] **6.2. Test de Migration Dynamique & Résilience (Failover Test)** :
  - Simuler l'extinction du nœud `mini` (`sudo poweroff` ou arrêt de k3s-agent).
  - Constater l'éviction sous 30 secondes et le redémarrage automatique du pod sur `linux2` (RTX 3070).
  - Vérifier qu'une génération d'image fonctionne sur `linux2` sans crash mémoire d'Ollama.
  - Rallumer `mini` et constater la reprise de charge par le worker dédié.
* [ ] **6.3. Documentation Utilisateur dans `manuel.md`** :
  - Ajouter la section **« Studio Visuel J.A.R.V.I.S. : Génération & Retouche d'Images à la Voix »**.
  - Documenter les exemples de phrases vocales et les astuces de retouche.
* [ ] **6.4. Git Commit & Push Final** :
  - Valider l'historique Git et pousser sur `origin/main`.

---

## 3. Matrice de Recette & Critères de Validation

| ID | Test | Résultat Attendu | Statut |
| :---: | :--- | :--- | :---: |
| **T01** | Génération T2I depuis Open WebUI (Bouton/Chat) | Image 1024x1024 photoréaliste affichée en < 5s | ⏳ À tester |
| **T02** | Déclenchement automatique par commande vocale | Jarvis transcrit, amplifie le prompt et génère l'image sans clic | ⏳ À tester |
| **T03** | Réponse vocale simultanée Kokoro (`ff_siwis`) | Jarvis lit sa réponse en français pendant l'affichage | ⏳ À tester |
| **T04** | Retouche conversationnelle (Image-to-Image) | Modification réussie en conservant la scène initiale | ⏳ À tester |
| **T05** | Super-Résolution / Upscaling 4K | Rendu 4K net (3840x2160) généré en < 8s | ⏳ À tester |
| **T06** | Isolation VRAM nominale (`mini` actif) | VRAM `linux2` dédiée à 100% au LLM, VRAM `mini` dédiée à l'image | ⏳ À tester |
| **T07** | Migration automatique sur extinction de `mini` | Pod re-schedulé sur `linux2` en < 45s avec CPU-offload actif | ⏳ À tester |
| **T08** | Persistance du stockage `/stockage` | Zéro perte de modèles ni d'images après reboot | ⏳ À tester |

---

*Ce plan d'action constitue la feuille de route opérationnelle pour la réalisation de `projetimage.md`.*
