# 📚 RAG Multi-Model Application

Application RAG (Retrieval-Augmented Generation) professionnelle avec support multi-modèles (OpenAI, Claude, Gemini).

## 🌐 Démo Live

- **Backend API**: https://rag2-vbo5.onrender.com
- **Documentation API**: https://rag2-vbo5.onrender.com/docs
- **Frontend**: (Déploiement Vercel en cours)

## 🎯 Fonctionnalités

- **Upload de PDFs** : Glissez-déposez vos documents PDF pour les indexer
- **Recherche sémantique avancée** :
  - ChromaDB avec embeddings BGE-Large (1024 dimensions)
  - Réranking intelligent avec Cohere
  - Cache de requêtes pour performances optimales
- **Nettoyage intelligent des PDFs scientifiques** :
  - Filtrage automatique des références bibliographiques
  - Chunking sémantique par paragraphes
  - Nettoyage des headers/footers et métadonnées
  - Idéal pour articles académiques avec beaucoup de citations
- **Multi-modèles AI** :
  - OpenAI GPT-4o / GPT-4o Mini
  - Claude 3.5 Sonnet / Claude 3.5 Haiku
  - Gemini 2.0 Flash / Gemini Exp 1206
- **Sélection de documents** : Choisissez sur quels PDFs faire vos recherches
- **Interface moderne** : UI sombre et responsive
- **Sources citées** : Chaque réponse inclut les sources avec numéros de pages

## 🏗️ Architecture

```
RAG/
├── backend/
│   ├── main.py              # API FastAPI
│   ├── llm_service.py       # Service multi-modèles
│   ├── vector_store.py      # ChromaDB + embeddings
│   └── pdf_processor.py     # Extraction et chunking
├── frontend/
│   ├── index.html           # Interface utilisateur
│   ├── styles.css           # Design moderne
│   └── app.js               # Logique frontend
├── data/
│   ├── pdfs/                # PDFs uploadés
│   └── chroma_db/           # Base vectorielle
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone <your-repo-url>
cd RAG
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les clés API

Copiez le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

Puis éditez `.env` et ajoutez vos clés API :

```env
# OpenAI API (https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key-here

# Anthropic Claude API (https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Google Gemini API (https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=AIzaSy-your-key-here
```

**Note** : Vous n'avez besoin que des clés API des modèles que vous voulez utiliser. Par exemple, si vous voulez utiliser seulement Gemini, seule la clé `GEMINI_API_KEY` est nécessaire.

### 5. Créer les dossiers de données

```bash
mkdir -p data/pdfs data/chroma_db
```

## 🎮 Utilisation

### Démarrer le backend

```bash
cd backend
python main.py
```

Le serveur démarre sur `http://localhost:8000`

Vous pouvez vérifier que tout fonctionne :
- API docs : http://localhost:8000/docs
- Health check : http://localhost:8000/health

### Démarrer le frontend

Ouvrez simplement `frontend/index.html` dans votre navigateur, ou utilisez un serveur local :

```bash
# Avec Python
cd frontend
python3 -m http.server 3000

# Ou avec Node.js
npx serve frontend
```

Puis ouvrez http://localhost:3000

### Utilisation de l'interface

1. **Upload des PDFs** : Glissez-déposez vos PDFs dans la zone de gauche
2. **Sélection** : Cochez les documents sur lesquels vous voulez faire des recherches
3. **Choix du modèle** : Sélectionnez le modèle AI dans le menu déroulant
4. **Question** : Tapez votre question dans la zone de chat
5. **Réponse** : L'assistant répond en citant ses sources

## 📊 Modèles disponibles

| Modèle | Provider | Caractéristiques | Coût |
|--------|----------|------------------|------|
| **Gemini 2.0 Flash** | Google | Très rapide, gratuit | Gratuit |
| **Gemini Exp 1206** | Google | Expérimental, performant | Gratuit |
| **GPT-4o** | OpenAI | Meilleure qualité | $$$ |
| **GPT-4o Mini** | OpenAI | Rapide, économique | $ |
| **Claude 3.5 Sonnet** | Anthropic | Excellent raisonnement | $$ |
| **Claude 3.5 Haiku** | Anthropic | Rapide, économique | $ |

## 🔧 Configuration avancée

### Variables d'environnement

```env
# Configuration
ENVIRONMENT=development
CHROMA_DB_PATH=./data/chroma_db
PDF_UPLOAD_PATH=./data/pdfs
MAX_FILE_SIZE_MB=50
```

### Chunking intelligent (dans pdf_processor.py)

Le système utilise un **chunking sémantique** par paragraphes avec nettoyage automatique :

```python
PDFProcessor(
    chunk_size=1000,      # Taille max des chunks en caractères
    chunk_overlap=200     # Overlap entre chunks (dernières phrases)
)
```

**Fonctionnalités de nettoyage** :
- ✅ Détection automatique des sections de références
- ✅ Filtrage des pages de références (>50% de citations)
- ✅ Simplification des références inline `[1,2,3,4,5]` → `[citations]`
- ✅ Suppression des headers/footers
- ✅ Chunking respectant les limites de paragraphes

📖 Voir [AMELIORATIONS_RAG.md](AMELIORATIONS_RAG.md) pour plus de détails

### Recherche optimisée (dans main.py)

Le système adapte automatiquement le nombre de chunks selon le modèle utilisé :

```python
search_results = vector_store.search(
    query=request.question,
    selected_files=request.selected_files,
    n_results=10,              # Base (adapté automatiquement)
    model_name=request.model,  # Détermine l'optimal selon la fenêtre de contexte
    use_reranking=True         # Active Cohere reranking si disponible
)
```

**Optimisations actives** :
- 🎯 **Adaptation au modèle** : 8-20 chunks selon la fenêtre de contexte (8K-200K tokens)
- 🔄 **Réranking Cohere** : Améliore la pertinence des résultats de 30-40%
- ⚡ **Cache de requêtes** : Expire après 1h, réduit les appels API
- 📊 **Embeddings BGE-Large** : 1024 dimensions vs 384 (MiniLM)

## 📝 API Endpoints

### GET /health
Vérification du statut de l'API

### GET /documents
Liste tous les documents indexés

### POST /upload
Upload et indexation d'un PDF
- Body : `multipart/form-data` avec fichier PDF

### POST /query
Interroge les documents
```json
{
  "question": "Quelle est la capitale de la France ?",
  "model": "gemini",
  "selected_files": ["doc1.pdf", "doc2.pdf"]
}
```

### DELETE /documents/{filename}
Supprime un document

## 🐛 Dépannage

### Erreur : "No module named 'chromadb'"
```bash
pip install -r requirements.txt
```

### Erreur : "API key not found"
Vérifiez que votre fichier `.env` existe et contient les bonnes clés API.

### Erreur : "Failed to connect to server"
Vérifiez que le backend est bien démarré sur http://localhost:8000

### Erreur CORS
Si vous ouvrez directement `index.html` (file://), utilisez un serveur HTTP local.

### ChromaDB : "Collection already exists"
Supprimez le dossier `data/chroma_db` pour réinitialiser la base.

## 🚀 Déploiement Cloud (à venir)

### Backend : Render / Railway / Fly.io
- Héberge l'API FastAPI
- Variables d'environnement pour les clés API
- Stockage persistant pour ChromaDB

### Frontend : Vercel / Netlify
- Déploiement du frontend statique
- Configuration de l'URL de l'API

### Base vectorielle : Pinecone (migration future)
- Alternative cloud à ChromaDB
- Gratuit jusqu'à 1M vecteurs
- Meilleure scalabilité

## 📚 Technologies utilisées

- **Backend** : FastAPI, Python 3.11+
- **Vector DB** : ChromaDB (local), Pinecone (cloud)
- **Embeddings** : sentence-transformers (BAAI/bge-large-en-v1.5 - 1024D)
- **Reranking** : Cohere rerank-english-v3.0
- **PDF** : PyMuPDF (fitz) avec nettoyage intelligent
- **Cache** : diskcache pour optimisation des requêtes
- **AI Models** :
  - OpenAI API (openai)
  - Anthropic API (anthropic)
  - Google Gemini API (google-generativeai)
- **Frontend** : HTML5, CSS3, Vanilla JavaScript

## 📄 Licence

MIT License

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## ⚠️ Sécurité

- **Ne commitez JAMAIS votre fichier `.env`** (déjà dans .gitignore)
- Utilisez des variables d'environnement pour les clés API en production
- Limitez la taille des uploads (MAX_FILE_SIZE_MB)
- Validez les inputs utilisateurs

## 📞 Support

Pour toute question ou problème, ouvrez une issue sur GitHub.

---

**Fait avec ❤️ en Python & JavaScript**
