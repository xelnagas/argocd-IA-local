# Cartographie Matérielle & Capabilités CUDA du Cluster Kubernetes

Ce document dresse l'état des lieux matériel et logiciel consolidé des 4 nœuds du cluster Kubernetes bare-metal (K3s), mis à jour le **02 octobre 2026** suite à l'activation complète des fonctionnalités GPU et CUDA sur le worker dédié.

---

## 1. Synthèse Exécutive & État des Nœuds

| Nœud | Rôle K8s | IP Interne | CPU | RAM | Architecture & Noyau | GPU Détecté | Capacité GPU K8s (`nvidia.com/gpu`) | Statut CUDA / K8s |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`linux2`** | Control-plane & GPU | `192.168.1.160` | 24 vCPU | 31.2 Go | **amd64** (`5.15.0-194-generic`) | **NVIDIA GeForce RTX 3070** (8 Go VRAM GDDR6, GA104) | **Allocatable: 1** | **OPÉRATIONNEL** (Driver 580.178.04, CUDA 13.0, Plugin K8s Actif) |
| **`mini`** | Worker | `192.168.1.99` | 12 vCPU | 15 Go | **amd64** (`7.0.0-38-generic`) | **NVIDIA GeForce RTX 2070 SUPER** (8 Go VRAM GDDR6) | **Allocatable: 1** | Hors ligne (ou Worker secondaire) |
| **`pi1`** | Worker | `192.168.1.24` | 4 vCPU | 0.9 Go | **arm64** (`6.8.0-1064-raspi`) | Broadcom VideoCore (SoC Raspberry Pi) | Aucune (0) | Inéligible IA (Nœud Edge ARM64 standard) |
| **`piblanc`** | Worker | `192.168.1.50` | 4 vCPU | 0.9 Go | **arm64** (`6.8.0-1064-raspi`) | Broadcom VideoCore (SoC Raspberry Pi) | Aucune (0) | Inéligible IA (Nœud Edge ARM64 standard) |

---

## 2. Fiche Technique Détaillée du Nœud GPU : `mini` (`192.168.1.99`)

Le nœud **`mini`** est la machine d'exécution exclusive des charges d'inférence de la plateforme **Jarvis**.

### 2.1. Environnement Système & K8s
* **Nom du nœud** : `mini`
* **Distribution OS** : Ubuntu 26.04.1 LTS (resolute)
* **Kernel** : Linux `7.0.0-38-generic` (x86_64)
* **Moteur d'exécution conteneurs** : `containerd://2.3.4-k3s1.36`
* **Labels K8s appliqués** :
  * `accelerator=nvidia-gpu`
  * `gpu-model=rtx2070super`
  * `kubernetes.io/hostname=mini`
* **RuntimeClass associée** : `nvidia` (mappé sur `/usr/bin/nvidia-container-runtime`)

### 2.2. Spécifications du GPU Physique
* **Modèle** : `NVIDIA Corporation TU104 [GeForce RTX 2070 SUPER] (rev a1)`
* **UUID Périphérique** : `GPU-8fb9778c-e8d4-7abb-fe6e-814594e77c72`
* **Micro-architecture** : NVIDIA Turing (TU104)
* **Compute Capability (CUDA)** : **7.5**
* **Cœurs CUDA** : 2 560
* **Tensor Cores** : 320 (accélération matérielle FP16 / INT8 / INT4)
* **VRAM Dédiée** : **8 192 Mo (8 Go GDDR6)** à ~448 Go/s de bande passante
* **Pilote Hôte Actif** : `580.178.04`
* **Version CUDA Supportée** : `13.0`

### 2.3. Preuve d'Exécution `nvidia-smi` sur l'Hôte
```text
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.178.04             Driver Version: 580.178.04     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 2070 ...    Off |   00000000:01:00.0 Off |                  N/A |
|  0%   36C    P8             26W /  215W |       1MiB /   8192MiB |      0%      Default |
+-----------------------------------------+------------------------+----------------------+
```

---

## 3. Historique & Validation des Actions d'Activation CUDA

Les 4 actions d'activation ont été réalisées avec succès et validées :

### ✅ 1. Pilotes Officiels NVIDIA (Noyau Ubuntu 26.04)
* Paquet `nvidia-driver-550` installé avec compilation DKMS du module `580.178.04` pour le noyau `7.0.0-38-generic`.
* Pilote `nouveau` déchargé et blacklisté (`/etc/modprobe.d/blacklist-nouveau.conf`).
* Chargement automatique des modules `nvidia`, `nvidia-modeset`, `nvidia-drm`, `nvidia-uvm` au boot (`/etc/modules-load.d/nvidia.conf`).

### ✅ 2. NVIDIA Container Toolkit
* Version installée : `1.20.1-1`.
* CDI (Container Device Interface) configuré et généré dans `/etc/cdi/nvidia.yaml` et `/var/run/cdi/nvidia.yaml`.

### ✅ 3. Runtime containerd de K3s
* Drop-in configuré dans `/var/lib/rancher/k3s/agent/etc/containerd/config-v3.toml.d/nvidia.toml`.
* Prise en compte validée via `crictl info` avec le runtime `nvidia`.

### ✅ 4. Plugin K8s & Validation Pod
* Déploiement du DaemonSet [nvidia-device-plugin.yaml](./k8s/infrastructure/nvidia-device-plugin.yaml) (v0.17.0).
* **Ressource allouable** : `kubectl get node mini -o jsonpath='{.status.allocatable.nvidia\.com/gpu}'` renvoie bien `1`.
* **Validation applicative Pod** : Un pod de test (`nvidia/cuda:12.6.0-base-ubuntu24.04`) avec `runtimeClassName: nvidia` et `limits: { nvidia.com/gpu: 1 }` s'est exécuté avec succès et a affiché le retour de `nvidia-smi` avec les 8 Go de VRAM disponibles.

---

## 4. Analyse d'Adéquation : RTX 2070 SUPER (8 Go VRAM) vs Modèles Gemma

| Configuration Modèle | Poids / Précision | VRAM Requise | Faisabilité sur `mini` | Débit Estimé |
| :--- | :--- | :--- | :--- | :--- |
| **Gemma 4 26B / A4B** | 4-bit (AWQ / GPTQ / Q4_K_M) | ~14 à 16 Go | **Partielle (Hybride)** : ~18-20 couches déchargées dans les 8 Go VRAM, reste des couches en RAM CPU (15 Go) | ~5 à 12 tokens/s |
| **Gemma 2 9B** | 4-bit (Q4_K_M) | **~5.5 à 6.2 Go** | **100% VRAM (Recommandé)** : Le modèle tient intégralement dans les 8 Go de la RTX 2070 SUPER | **~25 à 35 tokens/s** |
| **Llama 3.1 8B / Mistral 7B** | 4-bit (Q4_K_M / AWQ) | **~5.0 à 5.8 Go** | **100% VRAM (Recommandé)** : Modèle intégralement en VRAM | **~30 à 45 tokens/s** |

### Stratégie Préconisée pour l'Inférence Jarvis :
1. **Priorité Débit / Fluidité (Chat interactif & agents réactifs)** :
   - Déployer **Gemma 2 9B Q4_K_M** (ou Llama 3.1 8B) à 100% en VRAM. Permet des temps de réponse quasi-instantanés pour l'interface Open WebUI et les boucles d'agents n8n.
2. **Priorité Raisonnement Complexe (Tâches analytiques lourdes)** :
   - Déployer le modèle **Gemma 26B A4B** avec Ollama / llama.cpp configuré avec un offload partiel (`num_gpu: 20` layers). Les calculs les plus intenses profitent des Tensor Cores de la 2070 SUPER, complétés par le CPU Intel 12 vCPUs.

---

## 5. Modèle de Manifest Pod pour Jarvis (Ciblage `mini`)

Pour déployer un conteneur d'inférence (vLLM / Ollama) sur le nœud `mini`, le manifest GitOps doit contenir les directives suivantes :

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jarvis-inference
  namespace: jarvis-system
spec:
  replicas: 1
  template:
    spec:
      # Ciblage des nœuds GPU via label standard
      nodeSelector:
        accelerator: nvidia-gpu

      # Tolérance aux éventuelles taints GPU
      tolerations:
        - key: "nvidia.com/gpu"
          operator: "Exists"
          effect: "NoSchedule"

      # Utilisation du runtime containerd NVIDIA
      runtimeClassName: nvidia

      containers:
        - name: inference-engine
          image: ollama/ollama:latest
          resources:
            limits:
              nvidia.com/gpu: "1"       # Réservation exclusive de la RTX 2070 SUPER
              memory: 12Gi
              cpu: "8"
            requests:
              nvidia.com/gpu: "1"
              memory: 8Gi
              cpu: "4"
          env:
            - name: NVIDIA_VISIBLE_DEVICES
              value: "all"
            - name: NVIDIA_DRIVER_CAPABILITIES
              value: "compute,utility"
```
