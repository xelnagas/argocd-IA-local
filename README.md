# Jarvis - Infrastructure IA Locale & Multi-Agents sous Kubernetes (GitOps / ArgoCD)

Plateforme d'Intelligence Artificielle générative et d'orchestration multi-agents auto-hébergée sur un cluster Kubernetes bare-metal, pilotée intégralement par ArgoCD.

* **Dépôt GitOps :** `https://github.com/xelnagas/argocd-IA-local.git`
* **Application ArgoCD :** `jarvis`
* **Nœud Master K8s :** `192.168.1.160` (admin : `julien`)

---

## Documentation du Projet

* 📄 **[Fiche Produit (ficheproduit.md)](./ficheproduit.md)** : Vision, architecture fonctionnelle et technique, spécifications des composants (moteur d'inférence GPU vLLM/Ollama, Open WebUI, n8n, modèles Gemma), matrice réseau et exigences matérielles.
* 📋 **[Norme GitOps ArgoCD (normegitops.md)](./normegitops.md)** : Règles et standards GitOps, manifest de l'application ArgoCD `jarvis`, conventions de nommage K8s, ordonnancement GPU NVIDIA RTX / CUDA, gestion des secrets (Sealed Secrets) et politiques de synchronisation/rollback.
* 🖥️ **[Cartographie CUDA & GPU (cudanode.md)](./cudanode.md)** : Audit matériel des nœuds du cluster, identification de la carte NVIDIA GeForce RTX 2070 SUPER sur le nœud `mini`, analyse VRAM vs modèles Gemma, et plan d'activation des drivers CUDA/K8s.
* 🎯 **[Plan d'Action (planaction.md)](./planaction.md)** : Feuille de route chronologique par phases (Socle GitOps, Déploiement GPU, Open WebUI, Orchestration Multi-Agents n8n, Recette et Clôture).
* 📖 **[Manuel Utilisateur & Exploitation (manuel.md)](./manuel.md)** : Guide pratique complet (Accès réseau LAN, configuration Open WebUI, RAG documentaire, chaînes multi-agents n8n, gestion des modèles Ollama et troubleshooting).
