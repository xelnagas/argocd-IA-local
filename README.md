# J.A.R.V.I.S. - Plateforme IA Locale Multimodale & Studio Visuel Bi-GPU (GitOps / ArgoCD)

Plateforme d'Intelligence Artificielle générative, de synthèse vocale temps réel, de recherche web en direct et de **Studio Visuel photoréaliste par commande vocale**, auto-hébergée sur un cluster Kubernetes bare-metal bi-GPU et pilotée intégralement par GitOps (ArgoCD).

* **Dépôt GitOps :** `https://github.com/xelnagas/argocd-IA-local.git` (Branche `main`)
* **Application ArgoCD :** `jarvis` (Namespace `jarvis-system`)
* **Nœud Master & Cœur Cognitif :** `linux2` (`192.168.1.160`) — **NVIDIA GeForce RTX 3070 (8 Go VRAM)** + Stockage centralisé `/stockage` (2 To libres)
* **Nœud Dédié Studio Visuel :** `mini` (`192.168.1.99`) — **NVIDIA GeForce RTX 2070 SUPER (8 Go VRAM)** (Failover transparent < 10s vers `linux2`)

---

## ⚡ Accès Rapide aux Services (Réseau Local)

| Service | Accès Direct LAN (IP:Port) | Accès Ingress (Nom convivial) | Rôle |
| :--- | :--- | :--- | :--- |
| **Open WebUI** | **[`http://192.168.1.160:30080`](http://192.168.1.160:30080)** | **`http://jarvis.local/`** | Chat, RAG, Audio & Studio Visuel |
| **Studio Visuel API** | **[`http://192.168.1.160:30850`](http://192.168.1.160:30850)** | **`http://images.local/`** | API OpenAI Image (SDXL Lightning, I2I, Upscale 4K) |
| **Galerie d'Images** | **`http://192.168.1.160:30850/images/`** | **`http://jarvis.local/images/`** | Galerie permanente sur `/stockage` |
| **Ollama GPU API** | **`http://192.168.1.160:31434`** | **`http://ollama.local/`** | Inférence LLM (`jarvis:latest`, `llama3.1:8b`, `gemma2:9b`) |
| **Serveur FastMCP** | **`http://192.168.1.160:30800/mcp`** | **`http://mcp.local/mcp`** | Recherche Web DuckDuckGo & Tool calling |
| **Qdrant Vector DB** | **`http://192.168.1.160:30333`** | **`http://qdrant.local/`** | Mémoire vectorielle (Second Cerveau) |
| **ArgoCD Server** | **`https://192.168.1.160/`** | - | Console d'administration GitOps |

---

## 📚 Documentation Complète du Projet

* 📖 **[Manuel Utilisateur & Exploitation (manuel.md)](./manuel.md)** : Guide pratique pas-à-pas (Commandes vocales, Studio Visuel, RAG, dépannage et exploitation).
* 🎨 **[Cahier des Charges du Studio Visuel (projetimage.md)](./projetimage.md)** : Spécifications complètes du Studio Visuel, génération SDXL photoréaliste, retouche conversationnelle et bascule failover bi-GPU.
* 🎯 **[Plan d'Action du Studio Visuel (planactionimage.md)](./planactionimage.md)** : Déroulé opérationnel de la Phase 7, tests techniques, benchmarks réels et recette de bout en bout.
* 📄 **[Fiche Produit (ficheproduit.md)](./ficheproduit.md)** : Vision, architecture fonctionnelle et technique, matrice réseau et spécifications des composants.
* 🚀 **[Feuille de Route & Évolutions (evolution.md)](./evolution.md)** : Historique des phases déployées (0 à 7) et roadmap future (domotique Home Assistant, vision Frigate).
* 🖥️ **[Cartographie Matérielle & GPU (cudanode.md)](./cudanode.md)** : Répartition de la charge sur les deux cartes graphiques RTX 3070 et RTX 2070 SUPER.
* 📋 **[Norme GitOps ArgoCD (normegitops.md)](./normegitops.md)** : Standards GitOps, conventions K8s, runtime NVIDIA et politiques de synchronisation.
* 🎯 **[Plan d'Action Historique (planaction.md)](./planaction.md)** : Phases initiales 0 à 6 (Socle K8s, LLM, WebUI, MCP, Voix, Qdrant).
