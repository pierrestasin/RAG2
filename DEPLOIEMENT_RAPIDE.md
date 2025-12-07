# 🚀 Déploiement Rapide (15 minutes)

## Prérequis

- Compte GitHub
- Compte Render.com (gratuit)
- Compte Vercel.com (gratuit)
- Clés API : OpenAI / Anthropic / Gemini

---

## Étape 1 : Préparer le Repository (2 min)

```bash
# Si pas encore fait, initialiser git
git init
git add .
git commit -m "Initial commit - RAG v2.1"

# Créer un repo sur GitHub et push
git remote add origin https://github.com/TON-USERNAME/rag-app.git
git branch -M main
git push -u origin main
```

---

## Étape 2 : Déployer le Backend sur Render (5 min)

### 2.1 Créer le service

1. Aller sur https://dashboard.render.com
2. Cliquer **"New +"** → **"Web Service"**
3. Connecter ton repository GitHub
4. Sélectionner le repo `rag-app`

### 2.2 Configuration

Render détecte automatiquement `render.yaml`, mais vérifie :

- **Name** : `rag-backend`
- **Region** : Oregon (ou le plus proche)
- **Branch** : `main`
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### 2.3 Ajouter les variables d'environnement

Dans la section **"Environment"**, ajouter :

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...
COHERE_API_KEY=...
```

### 2.4 Ajouter le disque persistant

Dans **"Disk"** :
- **Name** : `rag-data`
- **Mount Path** : `/opt/render/project/src/data`
- **Size** : 1 GB

### 2.5 Déployer

Cliquer **"Create Web Service"**

⏳ Attendre 3-5 minutes que le déploiement se termine...

✅ Tu obtiens une URL : `https://rag-backend-xxx.onrender.com`

### 2.6 Tester

```bash
curl https://rag-backend-xxx.onrender.com/health
```

Réponse attendue :
```json
{"status":"ok","models_available":["openai","claude","gemini"],"chroma_db":true}
```

---

## Étape 3 : Déployer le Frontend sur Vercel (3 min)

### 3.1 Mettre à jour l'URL de l'API

Modifier `frontend/app.js` ligne 2 :

```javascript
// Configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://rag-backend-xxx.onrender.com'; // ⚠️ REMPLACER par ton URL Render
```

### 3.2 Commit et push

```bash
git add frontend/app.js
git commit -m "Update API URL for production"
git push
```

### 3.3 Déployer sur Vercel

**Option A : Via l'interface web**

1. Aller sur https://vercel.com
2. Cliquer **"Add New..."** → **"Project"**
3. Importer ton repo GitHub
4. **Root Directory** : `frontend`
5. Cliquer **"Deploy"**

**Option B : Via CLI**

```bash
# Installer Vercel CLI
npm i -g vercel

# Se connecter
vercel login

# Déployer
cd frontend
vercel --prod
```

⏳ Attendre 1-2 minutes...

✅ Tu obtiens une URL : `https://rag-xxx.vercel.app`

### 3.4 Configurer CORS sur Render

Retourner sur Render → Environment → Ajouter :

```
ALLOWED_ORIGINS=https://rag-xxx.vercel.app
```

Redéployer le backend (bouton "Manual Deploy").

---

## Étape 4 : Tester l'Application (5 min)

1. **Ouvrir** : https://rag-xxx.vercel.app
2. **Uploader un PDF** (ex: `sciadv.ady9493.pdf`)
3. **Poser une question** : "What is this document about?"
4. **Vérifier** que la réponse arrive avec les sources

✅ **Ça marche !**

---

## Résumé des URLs

| Service | URL | Coût |
|---------|-----|------|
| **Backend API** | `https://rag-backend-xxx.onrender.com` | Gratuit (750h/mois) |
| **Frontend** | `https://rag-xxx.vercel.app` | Gratuit (100GB/mois) |
| **Docs API** | `https://rag-backend-xxx.onrender.com/docs` | - |
| **Health Check** | `https://rag-backend-xxx.onrender.com/health` | - |

---

## Monitoring

### Logs Backend (Render)

1. Aller sur https://dashboard.render.com
2. Sélectionner ton service `rag-backend`
3. Onglet **"Logs"**

### Logs Frontend (Vercel)

1. Aller sur https://vercel.com/dashboard
2. Sélectionner ton projet
3. Onglet **"Deployments"** → Cliquer sur le dernier déploiement

---

## Maintenance

### Redéployer après modifications

**Backend** :
```bash
git add .
git commit -m "Update backend"
git push
# Render redéploie automatiquement
```

**Frontend** :
```bash
git add .
git commit -m "Update frontend"
git push
# Vercel redéploie automatiquement
```

### Changer les clés API

Render → Environment → Modifier les variables → Manual Deploy

---

## Dépannage Rapide

### ❌ Erreur CORS

**Solution** :
```bash
# Vérifier ALLOWED_ORIGINS sur Render
ALLOWED_ORIGINS=https://rag-xxx.vercel.app
```

### ❌ Backend ne démarre pas

**Solution** :
```bash
# Voir les logs sur Render
# Problème courant : dépendances manquantes
pip install -r requirements.txt
```

### ❌ Upload de PDF ne fonctionne pas

**Solution** :
```bash
# Vérifier le disque persistant sur Render
# Vérifier les logs pour voir l'erreur exacte
```

---

## Améliorer les Performances

### 1. Passer à un plan payant Render

**Render Starter** ($7/mois) :
- ✅ Pas de cold start
- ✅ Toujours actif (pas de mise en veille)
- ✅ Plus de CPU/RAM

### 2. Ajouter un cache CDN

Vercel inclut déjà un CDN, mais tu peux optimiser :

```javascript
// frontend/app.js
// Ajouter un cache côté client pour les requêtes répétées
const cache = new Map();

async function queryWithCache(question, model) {
    const cacheKey = `${question}_${model}`;
    if (cache.has(cacheKey)) {
        return cache.get(cacheKey);
    }

    const result = await query(question, model);
    cache.set(cacheKey, result);
    return result;
}
```

### 3. Migrer vers Pinecone (Vector DB cloud)

Pour de meilleures performances et scalabilité :
- Voir [DEPLOIEMENT_CLOUD.md](DEPLOIEMENT_CLOUD.md) section "Pinecone"

---

## 🎉 Félicitations !

Ton application RAG est maintenant en ligne et accessible partout dans le monde !

**Next Steps** :
1. Partager l'URL avec des testeurs
2. Monitorer les logs
3. Améliorer selon les retours utilisateurs

**Questions ?** Consulte [DEPLOIEMENT_CLOUD.md](DEPLOIEMENT_CLOUD.md) pour plus de détails.
