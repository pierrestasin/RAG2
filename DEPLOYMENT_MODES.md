# Modes de Déploiement RAG

Ce projet supporte deux modes de déploiement selon vos contraintes de RAM et de coût.

## 🆓 Mode Cloud (Recommandé pour Render Free Tier)

**Utilisation:** Embeddings via API OpenAI
**RAM requise:** ~150MB
**Coût:** ~$0.0001 par 1000 tokens d'embedding
**Avantages:**
- ✅ Fonctionne sur Render free tier (512MB RAM)
- ✅ Démarrage rapide (~5 secondes)
- ✅ Pas de téléchargement de modèles lourds
- ✅ Qualité excellente (OpenAI text-embedding-3-small)

**Inconvénients:**
- ⚠️ Nécessite une clé API OpenAI
- ⚠️ Coût par requête (très faible: ~$0.02 pour 1000 pages)

### Configuration

```bash
# .env ou variables d'environnement Render
DEPLOYMENT_MODE=cloud
OPENAI_API_KEY=sk-...
```

```bash
# Installation
pip install -r requirements-light.txt
```

---

## 💪 Mode Local (Pour serveurs avec plus de RAM)

**Utilisation:** Modèle SentenceTransformer local (all-MiniLM-L6-v2)
**RAM requise:** ~800MB
**Coût:** Gratuit (après installation)
**Avantages:**
- ✅ Aucun coût par requête
- ✅ Pas de dépendance externe
- ✅ Données restent 100% privées

**Inconvénients:**
- ❌ Ne fonctionne PAS sur Render free tier (512MB)
- ⚠️ Démarrage plus lent (~30 secondes pour charger le modèle)
- ⚠️ Nécessite au moins 1GB de RAM

### Configuration

```bash
# .env ou variables d'environnement
DEPLOYMENT_MODE=local
```

```bash
# Installation
pip install -r requirements.txt
```

---

## 📊 Comparaison des Coûts

### Mode Cloud (OpenAI API)

| Scénario | Tokens | Coût |
|----------|--------|------|
| Upload 1 PDF (10 pages) | ~5,000 | $0.0005 |
| Upload 1 PDF (100 pages) | ~50,000 | $0.005 |
| 1000 requêtes (recherche) | ~30,000 | $0.003 |
| **Usage typique/mois** | ~500K | **$0.05** |

**Coût estimé:** Moins de $1/mois pour usage personnel

### Mode Local

| Ressource | Coût |
|-----------|------|
| RAM (800MB) | Plan Render Starter: $7/mois |
| Embeddings | Gratuit |
| **Total/mois** | **$7** |

---

## 🚀 Recommandations

### Pour Render Free Tier (512MB RAM)
👉 **Utilisez le mode Cloud**
- Modifier `.env`: `DEPLOYMENT_MODE=cloud`
- Sur Render: Ajouter variable `DEPLOYMENT_MODE=cloud`
- Coût total: ~$0.05-1/mois (OpenAI API)

### Pour Render Starter ($7/mois, 2GB RAM)
👉 **Utilisez le mode Local**
- Modifier `.env`: `DEPLOYMENT_MODE=local`
- Sur Render: Ajouter variable `DEPLOYMENT_MODE=local`
- Coût total: $7/mois (serveur uniquement)

### Pour serveur personnel (2GB+ RAM)
👉 **Utilisez le mode Local**
- Gratuit et privé
- Aucune dépendance externe

---

## 🔄 Basculer entre les Modes

Le code détecte automatiquement le mode via la variable `DEPLOYMENT_MODE`:

```python
# backend/config.py charge automatiquement le bon vector_store
if DEPLOYMENT_MODE == "local":
    from backend.vector_store import vector_store  # SentenceTransformer local
else:
    from backend.vector_store_light import vector_store  # OpenAI API
```

Pas besoin de changer le code, juste la variable d'environnement!

---

## 📝 Notes Techniques

### Mode Cloud
- Modèle: `text-embedding-3-small` (1536 dimensions)
- Prix: $0.00002 / 1K tokens
- Latence: ~100-300ms par requête

### Mode Local
- Modèle: `all-MiniLM-L6-v2` (384 dimensions)
- RAM: ~80MB (modèle) + ~700MB (PyTorch + dépendances)
- Latence: ~50-100ms par requête

### Qualité
Les deux modes offrent une qualité similaire grâce au **réranking Cohere** qui améliore la pertinence de +30-40% dans les deux cas.
