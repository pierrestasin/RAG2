# 🚀 Guide de Déploiement Cloud

## Architecture Cloud

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                            │
│                  Vercel / Netlify                        │
│              (Static Site Hosting)                       │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      BACKEND API                         │
│                  Render / Railway                        │
│              (FastAPI + Python)                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   VECTOR DATABASE                        │
│              ChromaDB (local) ou Pinecone (cloud)        │
└─────────────────────────────────────────────────────────┘
```

---

## Option 1 : Déploiement Rapide (Recommandé)

### Backend : Render.com

**Avantages** :
- ✅ Gratuit pour commencer (750h/mois)
- ✅ Support Python natif
- ✅ Variables d'environnement faciles
- ✅ Déploiement automatique depuis Git
- ✅ Stockage persistant inclus

**Étapes** :

1. **Créer un compte sur [Render](https://render.com)**

2. **Préparer le projet pour Render**

```bash
# Créer les fichiers de configuration
touch render.yaml
```

3. **Créer `render.yaml`** (configuration Render) :

```yaml
services:
  - type: web
    name: rag-backend
    env: python
    region: oregon
    plan: free
    branch: main
    buildCommand: "pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: COHERE_API_KEY
        sync: false
      - key: CHROMA_DB_PATH
        value: /opt/render/project/src/data/chroma_db
      - key: PDF_UPLOAD_PATH
        value: /opt/render/project/src/data/pdfs
    disk:
      name: rag-data
      mountPath: /opt/render/project/src/data
      sizeGB: 1
```

4. **Push sur GitHub** :

```bash
git add .
git commit -m "Add Render configuration"
git push origin main
```

5. **Déployer sur Render** :
   - Aller sur [dashboard.render.com](https://dashboard.render.com)
   - Cliquer "New +" → "Web Service"
   - Connecter ton repo GitHub
   - Render détectera automatiquement le `render.yaml`
   - Ajouter les variables d'environnement (clés API)
   - Cliquer "Create Web Service"

6. **URL Backend** : `https://rag-backend-xxx.onrender.com`

---

### Frontend : Vercel

**Avantages** :
- ✅ Complètement gratuit
- ✅ CDN mondial ultra-rapide
- ✅ Déploiement en 2 minutes
- ✅ HTTPS automatique

**Étapes** :

1. **Mettre à jour l'URL de l'API dans le frontend**

Créer `frontend/.env.production` :

```env
VITE_API_URL=https://rag-backend-xxx.onrender.com
```

Modifier `frontend/app.js` :

```javascript
// Configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://rag-backend-xxx.onrender.com'; // Remplacer par ton URL Render
```

2. **Créer `vercel.json`** (configuration Vercel) :

```json
{
  "version": 2,
  "buildCommand": "echo 'No build needed'",
  "outputDirectory": "frontend",
  "routes": [
    {
      "src": "/.*",
      "dest": "/index.html"
    }
  ]
}
```

3. **Déployer sur Vercel** :

```bash
# Installer Vercel CLI
npm i -g vercel

# Déployer
cd frontend
vercel --prod
```

Ou via l'interface web :
- Aller sur [vercel.com](https://vercel.com)
- Connecter ton repo GitHub
- Configurer : Root Directory = `frontend`
- Déployer !

4. **URL Frontend** : `https://rag-xxx.vercel.app`

---

## Option 2 : Déploiement Avancé

### Backend : Railway.app

**Avantages** :
- ✅ $5 de crédit gratuit/mois
- ✅ Très facile à utiliser
- ✅ Redémarrages automatiques
- ✅ Base de données PostgreSQL incluse

**Étapes** :

1. **Créer un compte sur [Railway](https://railway.app)**

2. **Créer `railway.json`** :

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

3. **Créer `nixpacks.toml`** :

```toml
[phases.setup]
nixPkgs = ["python311", "pip"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
```

4. **Déployer** :
   - Aller sur [railway.app/new](https://railway.app/new)
   - Connecter ton repo GitHub
   - Ajouter les variables d'environnement
   - Railway déploie automatiquement !

---

## Option 3 : Déploiement Production (Scalable)

### Backend : AWS / Google Cloud / Azure

Pour une solution production avec auto-scaling :

**Stack recommandée** :
- **Compute** : AWS ECS Fargate / Google Cloud Run
- **Vector DB** : Pinecone (cloud-native)
- **Storage** : AWS S3 / Google Cloud Storage
- **CDN** : CloudFront / Cloud CDN

**Étapes** :

1. **Migrer vers Pinecone (Vector DB cloud)**

```python
# backend/vector_store_pinecone.py
import pinecone
from sentence_transformers import SentenceTransformer
import os

class PineconeVectorStore:
    def __init__(self):
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENV")
        )

        # Create index
        index_name = "rag-documents"
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=1024,  # BGE-Large
                metric="cosine"
            )

        self.index = pinecone.Index(index_name)
        self.embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')

    # ... reste du code similaire à vector_store.py
```

2. **Créer `Dockerfile`** :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Créer `docker-compose.yml`** :

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - COHERE_API_KEY=${COHERE_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_ENV=${PINECONE_ENV}
    volumes:
      - ./data:/app/data
```

4. **Déployer sur AWS ECS / Google Cloud Run**

---

## Configuration des Variables d'Environnement

### Backend (Render/Railway)

Ajouter ces variables dans le dashboard :

```env
# API Keys (obligatoires)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...
COHERE_API_KEY=...  # Optionnel

# Configuration
ENVIRONMENT=production
CHROMA_DB_PATH=/data/chroma_db
PDF_UPLOAD_PATH=/data/pdfs
MAX_FILE_SIZE_MB=50

# CORS (important !)
ALLOWED_ORIGINS=https://rag-xxx.vercel.app,https://rag-xxx.netlify.app
```

### Modifier `backend/main.py` pour CORS :

```python
# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Checklist de Déploiement

### Avant de déployer :

- [ ] Tester localement : `python backend/main.py`
- [ ] Vérifier que toutes les clés API fonctionnent
- [ ] Tester l'upload de PDF
- [ ] Tester les requêtes avec différents modèles
- [ ] Vérifier les logs d'erreur

### Après déploiement :

- [ ] Tester l'URL du backend : `https://xxx.onrender.com/health`
- [ ] Vérifier les logs dans le dashboard
- [ ] Tester l'upload depuis le frontend
- [ ] Vérifier que le stockage persistant fonctionne
- [ ] Tester avec un PDF scientifique réel

---

## Coûts Estimés

### Option Gratuite (Starter)
- **Render Free** : 750h/mois (suffit pour 1 instance)
- **Vercel Free** : 100GB bandwidth/mois
- **Total** : **$0/mois** ✅

### Option Pro (Recommandé)
- **Render Starter** : $7/mois (persistent disk)
- **Vercel Pro** : $20/mois (plus de bandwidth)
- **Cohere Free** : 1000 calls/mois (gratuit)
- **Total** : **$27/mois**

### Option Production
- **AWS ECS Fargate** : ~$30-50/mois
- **Pinecone Starter** : $70/mois (1M vecteurs)
- **S3 + CloudFront** : ~$10/mois
- **Total** : **~$110-130/mois**

---

## Surveillance et Monitoring

### Logs

**Render** :
```bash
# Voir les logs en temps réel
render logs -s rag-backend -f
```

**Railway** :
- Logs disponibles dans le dashboard

### Monitoring

Ajouter des endpoints de health check :

```python
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time,
        "chroma_db": os.path.exists(CHROMA_DB_PATH)
    }

@app.get("/metrics")
async def metrics():
    return {
        "documents_count": len(vector_store.list_documents()),
        "cache_size": vector_store.query_cache.size(),
        "models_available": ["openai", "claude", "gemini"]
    }
```

---

## Backup et Restauration

### Backup ChromaDB

```bash
# Backup automatique (cron job)
tar -czf backup-$(date +%Y%m%d).tar.gz data/chroma_db
```

### Restauration

```bash
# Restaurer depuis backup
tar -xzf backup-20250106.tar.gz -C /opt/render/project/src/
```

---

## Dépannage

### Problème : Backend ne démarre pas
```bash
# Vérifier les logs
render logs -s rag-backend

# Problème courant : dépendances manquantes
pip install -r requirements.txt
```

### Problème : CORS Error
```javascript
// Vérifier que l'URL backend est correcte
console.log('API_URL:', API_URL);
```

### Problème : Stockage plein
```bash
# Nettoyer le cache
rm -rf data/query_cache/*
```

---

## 🎯 Recommandation Finale

**Pour démarrer** : Render (backend) + Vercel (frontend)
- ✅ Gratuit
- ✅ Facile à configurer
- ✅ Parfait pour MVP et tests

**Pour production** : Railway (backend) + Vercel (frontend) + Pinecone
- ✅ Plus stable
- ✅ Meilleure performance
- ✅ Scalable

---

## Prochaines Étapes

1. **Créer un compte Render** : https://render.com
2. **Créer un compte Vercel** : https://vercel.com
3. **Configurer les fichiers** : `render.yaml`, `vercel.json`
4. **Déployer !**

Tu veux que je t'aide à créer les fichiers de configuration pour un déploiement spécifique ?
