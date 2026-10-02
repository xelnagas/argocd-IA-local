# Fiche Produit : Plateforme IA Locale "Jarvis"

| Métadonnée | Valeur |
| :--- | :--- |
| **Nom du Produit** | **Jarvis** (Local AI & Multi-Agent Platform) |
| **Version** | 1.0.0-draft |
| **Statut** | En conception / Initialisation GitOps |
| **Dépôt GitOps** | `https://github.com/xelnagas/argocd-IA-local.git` |
| **Orchestrateur GitOps** | ArgoCD (Application K8s : `jarvis`) |
| **Cluster Kubernetes** | Master Control-Plane : `192.168.1.160` (Compte administrateur : `julien`) |
| **Réseau Local** | `192.168.1.0/24` |

---

## 1. Vision & Objectifs Stratégiques

Le projet **Jarvis** vise à déployer une infrastructure d'Intelligence Artificielle générative et d'orchestration multi-agents entièrement auto-hébergée (on-premise), souveraine et résiliente, s'exécutant sur un cluster Kubernetes bare-metal domestique/lab.

### Objectifs Clés
1. **Souveraineté Totale des Données** : Aucune dépendance vis-à-vis d'APIs cloud externes (OpenAI, Anthropic, etc.). Données, prompts et fichiers conservés sur le réseau local.
2. **Accélération Matérielle Haute Performance** : Exploitation directe des cartes graphiques NVIDIA RTX (CUDA) présentes sur les worker nodes dédiés.
3. **Moteur d'Inférence Dédié** : Prise en charge de modèles open-weights avancés, notamment la famille **Gemma** (ex: *Gemma 4 26B / A4B* ou équivalents quantifiés 4-bit / AWQ / GGUF) optimisés pour la VRAM disponible.
4. **Accessibilité & Ergonomie** : Interface conversationnelle moderne accessible depuis l'ensemble des postes du réseau local via un Ingress Kubernetes.
5. **Recherche Web Temps Réel & Extensibilité MCP** : Intégration d'un serveur d'outils MCP (Model Context Protocol) dédié pour permettre au modèle de rechercher des informations sur Internet et extraire le contenu de pages web.
6. **Exploitation 100% GitOps** : Cycle de vie applicatif piloté exclusivement par ArgoCD depuis le dépôt source Git.

---

## 2. Architecture Globale du Système

```mermaid
graph TD
    subgraph LAN["Réseau Local (192.168.1.0/24)"]
        User["Utilisateur / Navigateur"]
        ExternalClients["Clients Externes LAN (VS Code / Claude Desktop)"]
    end

    subgraph K8s["Cluster Kubernetes (Master: 192.168.1.160)"]
        Ingress["Ingress Controller (Traefik)"]

        subgraph GeneralNodes["Worker Nodes CPU / Génériques"]
            WebUI["Open WebUI (Frontend / RAG / Chat)"]
            MCPSearch["jarvis-mcp-search (Serveur MCP Web Search)"]
        end

        subgraph GPUNodes["Worker Nodes GPU (NVIDIA RTX)"]
            InferenceEngine["Moteur d'Inférence (Ollama)<br/>CUDA Runtime + GPU Passthrough"]
            ModelStorage[("PV / Stockage Modèles<br/>Gemma 2 9B / Llama 3.1 8B")]
        end

        subgraph GitOpsControl["Management & GitOps"]
            ArgoCD["ArgoCD Server<br/>(App: 'jarvis')"]
        end
    end

    subgraph GitRepo["GitHub Repository"]
        Repo["xelnagas/argocd-IA-local.git"]
    end

    Repo -->|Déclaration GitOps| ArgoCD
    ArgoCD -->|Sync & Deploy| K8s
    User -->|HTTP/HTTPS LAN| Ingress
    ExternalClients -->|HTTP / MCP LAN| Ingress

    Ingress --> WebUI
    Ingress --> MCPSearch

    WebUI -->|API OpenAI-compatible| InferenceEngine
    WebUI <-->|Tool Calling MCP| MCPSearch
    MCPSearch -->|Requêtes DuckDuckGo / Web| Web["Internet"]
    InferenceEngine --> ModelStorage
```

---

## 3. Composants Applicatifs de la Stack

### 3.1. Moteur d'Inférence IA (Backend GPU)
* **Technologie retenue** : **vLLM** ou **Ollama** (exécuté en conteneur Kubernetes avec support CUDA).
  * *Option A (vLLM)* : Recommandé pour des performances optimales de débit, batching continu, API 100% compatible OpenAI `/v1/chat/completions`, support natif AWQ/GPTQ/FP8.
  * *Option B (Ollama / llama.cpp)* : Idéal pour une gestion dynamique des modèles GGUF et une empreinte mémoire adaptable.
* **Modèle cible** :
  * Modèle de type **Gemma 4 26B A4B** (ou Gemma 2 27B / quantized AWQ 4-bit / GGUF Q4_K_M).
  * Empreinte mémoire VRAM ciblée : ~16 Go à 24 Go selon la quantification et la taille du contexte (KV Cache).
* **Ressources K8s** :
  * Requête GPU : `nvidia.com/gpu: 1` (ou GPU partagé si plusieurs cartes).
  * Runtime : `nvidia` (NVIDIA Container Toolkit).
  * Stockage partagé (PVC) dédié au cache de modèles HuggingFace / Ollama models (évite le re-téléchargement à chaque redémarrage).

### 3.2. Interface Utilisateur (WebUI)
* **Technologie retenue** : **Open WebUI**.
* **Fonctionnalités** :
  * Interface épurée, responsive, compatible desktop/mobile.
  * Support multi-utilisateurs et gestion des droits/clés API.
  * RAG (Retrieval-Augmented Generation) intégré avec injection de documents (PDF, texte, web).
  * Gestion de prompts personnalisés (System Prompts) et personas d'agents.
  * Gestion d'outils (*Tool Calling*) et intégration native du protocole MCP.
  * Connexion directe au backend d'inférence via protocole OpenAI.

### 3.3. Serveur MCP & Recherche Web (jarvis-mcp-search)
* **Technologie retenue** : **FastMCP** (Streamable HTTP / SSE).
* **Rôle** :
  * Fournir des outils de recherche web en direct (`search_internet`) et de lecture de page (`fetch_web_page`).
  * Exécutable par le modèle Ollama à la demande lors d'une question nécessitant des données récentes.
  * Connectable aux clients LAN (VS Code, Claude Desktop, Cursor).

### 3.4. Réseau & Ingress
* **Ingress Controller** : Traefik (intégré k3s).
* **Exposition LAN** :
  * Routage par nom d'hôte DNS local (`jarvis.local`, `ollama.local`, `mcp.local`) ou via NodePorts directs (`30080`, `31434`, `30800`).
  * Timeout configuré à une valeur élevée pour supporter le streaming de réponses longues.

---

## 4. Matériel & Découpage de l'Infrastructure

| Rôle Node | Hôte / IP | Caractéristiques | Rôle dans Jarvis |
| :--- | :--- | :--- | :--- |
| **Control Plane** | `192.168.1.160` (admin: `julien`) | K8s Master, API Server, etcd, ArgoCD Server | Gestion GitOps, supervision, ingress |
| **GPU Worker Node** | `mini` (`192.168.1.99`) | Intel 12 vCPUs, 15 Go RAM, **NVIDIA GeForce RTX 2070 SUPER (8 Go VRAM)** | Inférence Ollama GPU (`accelerator=nvidia-gpu`), Open WebUI, MCP |
| **Edge Workers** | `pi1` (`192.168.1.24`), `piblanc` (`192.168.1.50`) | ARM64 Raspberry Pi | Trafic réseau, pods légers |

---

## 5. Exigences Non-Fonctionnelles

### 5.1. Performance & Latence
* Débit d'inférence visé : minimum **15 à 35 tokens/seconde** pour une expérience de lecture fluide en direct (atteint ~30 tokens/s sur `gemma2:9b` et ~35 tokens/s sur `llama3.1:8b`).
* Time-to-First-Token (TTFT) < 1.0s sur les requêtes locales.

### 5.2. Persistance & Stockage
* **Modèles LLM** : Volume persistant de **60 Go** (`ollama-models-pvc` sur `local-path` du nœud `mini`).
* **Données Open WebUI** : Volume persistant de 10 Go avec rétention locale.

### 5.3. Résilience & Disponibilité
* Tolérance aux pannes : redémarrage automatique des pods (`restartPolicy: Always`).
* Isolement des charges : `nodeSelector: accelerator=nvidia-gpu` garantissant le ciblage exclusif de `mini`.

---

## 6. Matrice des Flux Réseau

| Source | Destination | Port / Protocole | Description |
| :--- | :--- | :--- | :--- |
| Postes LAN (`192.168.1.*`) | Ingress Controller | 80/443 (HTTP/S) | Accès via noms d'hôtes `jarvis.local`, `ollama.local`, `mcp.local` |
| Postes LAN (`192.168.1.*`) | `jarvis-webui` Service | **30080** (TCP / NodePort) | Accès direct sans configuration DNS (`http://192.168.1.160:30080`) |
| Postes LAN (`192.168.1.*`) | `jarvis-inference` Service | **31434** (TCP / NodePort) | Accès direct API LLM (`http://192.168.1.160:31434`) |
| Postes LAN (`192.168.1.*`) | `jarvis-mcp-search` Service | **30800** (TCP / NodePort) | Accès direct Serveur MCP (`http://192.168.1.160:30800/mcp`) |
| Ingress Controller | `jarvis-webui` Service | 8080 (TCP) | Routage interne du trafic WebUI |
| Ingress Controller | `jarvis-mcp-search` Service | 8000 (TCP) | Routage interne du trafic MCP |
| Ingress Controller | `jarvis-inference` Service | 11434 (TCP) | Routage interne de l'API Ollama |
| `jarvis-webui` Pod | `jarvis-inference` Service | 11434 (TCP) | Envoi des requêtes de chat et streaming |
| `jarvis-webui` Pod | `jarvis-mcp-search` Service | 8000 (TCP) | Appels d'outils MCP pour la recherche web |
| `jarvis-mcp-search` Pod | Internet (DuckDuckGo / Web) | 443 (HTTPS) | Récupération des données web en direct |
| ArgoCD Controller | K8s API (`192.168.1.160:6443`) | 6443 (HTTPS) | Réconciliation GitOps déclarative |
| ArgoCD Controller | `github.com` | 443 (HTTPS) | Synchronisation du dépôt `argocd-IA-local.git` |

---

## 7. Roadmap & Phases de Déploiement

1. **Phase 1 : Socle GitOps & Pré-requis GPU**
   - Mise en place de l'application ArgoCD `jarvis`.
   - Validation du NVIDIA Container Toolkit et du Kubernetes NVIDIA Device Plugin sur les worker nodes RTX.
   - Configuration des StorageClasses locales.
2. **Phase 2 : Déploiement du Moteur d'Inférence**
   - Déploiement d'Ollama avec allocation GPU `1`.
   - Téléchargement et chargement en VRAM des modèles Gemma 2 9B, Llama 3.1 8B et Nomic Embed.
   - Tests de performance en requêtes directes via curl / script Python.
3. **Phase 3 : Interface Utilisateur & Ingress**
   - Déploiement d'Open WebUI connecté au backend d'inférence.
   - Exposition sur le réseau local via Ingress et NodePorts directs.
4. **Phase 4 : Serveur MCP & Recherche Web en Temps Réel**
   - Déploiement du serveur MCP `jarvis-mcp-search`.
   - Intégration du Tool Calling avec Ollama et Open WebUI.
   - Exposition locale et documentation utilisateur.
