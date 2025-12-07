# 🎓 Comment fonctionne votre RAG ?

## 📖 Principe général du RAG

**RAG = Retrieval-Augmented Generation** (Génération Augmentée par Récupération)

Le RAG combine deux étapes :
1. **Retrieval** : Recherche sémantique dans vos documents
2. **Generation** : Le LLM génère une réponse basée sur les passages trouvés

---

## 🔄 Workflow complet de votre RAG

### 1️⃣ **Upload d'un PDF** (`/upload`)

```
PDF → PyMuPDF → Extraction texte → Chunking → Embeddings → ChromaDB
```

**Détails** :
- **Extraction** : PyMuPDF extrait le texte page par page
- **Chunking** : Le texte est découpé en morceaux de **1000 caractères** avec **200 caractères de chevauchement** (overlap)
- **Embeddings** : Chaque chunk est transformé en vecteur par `sentence-transformers` (all-MiniLM-L6-v2)
- **Stockage** : Les vecteurs + métadonnées sont stockés dans ChromaDB

**Fichier** : [`backend/pdf_processor.py:10-71`](backend/pdf_processor.py)

---

### 2️⃣ **Question de l'utilisateur** (`/query`)

```
Question → Embedding → Recherche vectorielle → Top 5 chunks → LLM → Réponse
```

**Détails** :
- Votre question est transformée en vecteur
- ChromaDB cherche les **5 chunks les plus similaires** (ligne 182 de main.py)
- Ces chunks sont combinés et envoyés au LLM comme "contexte"
- Le LLM génère une réponse basée uniquement sur ce contexte

**Fichier** : [`backend/main.py:179-182`](backend/main.py)

---

### 3️⃣ **Suppression d'un document** (`/documents/{filename}`)

✅ **OUI, la suppression enlève de la DB vectorielle**

**Processus** :
1. Récupère tous les chunks du document via `where={"filename": filename}`
2. Supprime tous les chunks de ChromaDB via `collection.delete(ids=...)`
3. Supprime le fichier PDF physique

**Fichier** : [`backend/vector_store.py:96-108`](backend/vector_store.py)

---

## 🎯 Réponses à vos questions

### ❓ **Si je supprime les documents, ça enlève de la DB vectorielle ?**

✅ **OUI** - La fonction `delete_document()` supprime :
- Tous les embeddings du document dans ChromaDB
- Le fichier PDF physique dans `data/pdfs/`

```python
# backend/vector_store.py:96-108
def delete_document(self, filename: str):
    results = self.collection.get(where={"filename": filename})
    if results["ids"]:
        self.collection.delete(ids=results["ids"])  # ← Suppression ChromaDB
    return {"deleted": len(results["ids"])}
```

---

### ❓ **Combien de chunks sont récupérés avec les questions ?**

📊 **Actuellement : 5 chunks** (ligne 182 de main.py)

```python
# backend/main.py:179-182
search_results = vector_store.search(
    query=request.question,
    selected_files=request.selected_files,
    n_results=5  # ← 5 chunks les plus pertinents
)
```

**Calcul approximatif du contexte** :
- 5 chunks × 1000 caractères = ~5000 caractères
- Soit environ **1250 tokens** envoyés au LLM

---

### ❓ **Peut-on optimiser l'utilisation du RAG en fonction de la fenêtre de contexte ?**

✅ **OUI, excellente idée !** Voici comment optimiser :

#### **Fenêtres de contexte par modèle**

| Modèle | Fenêtre contexte | Chunks optimaux |
|--------|------------------|-----------------|
| GPT-4o, Claude Opus 4.5 | 200K tokens | 100-150 chunks |
| Claude Sonnet 4.5 | 200K tokens / 1M (beta) | 100-150 / 500+ |
| Gemini 2.5 Pro | 200K tokens | 100-150 chunks |
| GPT-4o-mini | 128K tokens | 60-80 chunks |
| Claude Haiku | 200K tokens | 100-150 chunks |

#### **Stratégie d'optimisation proposée**

**Option 1 : N'utiliser le RAG que si nécessaire**
```python
# Si le contexte est petit, envoyer tout directement au LLM
# Si le contexte est énorme, utiliser le RAG pour filtrer
```

**Option 2 : Adapter le nombre de chunks au modèle**
```python
model_configs = {
    "claude-opus-4-5": {"max_tokens": 200000, "optimal_chunks": 150},
    "gpt-4o": {"max_tokens": 128000, "optimal_chunks": 80},
    "gemini-2.5-flash": {"max_tokens": 200000, "optimal_chunks": 100}
}
```

**Option 3 : RAG hybride intelligent**
```python
if total_document_size < context_window * 0.7:
    # Document assez petit → envoyer en entier au LLM
    use_full_context()
else:
    # Document trop grand → utiliser RAG
    use_rag_with_adaptive_chunks()
```

---

## 🚀 Optimisations possibles

### 1. **Nombre de chunks dynamique**

Adapter selon le modèle utilisé :

```python
def get_optimal_chunks(model_name):
    if "opus" in model_name or "sonnet-4-5" in model_name:
        return 20  # Grands modèles → plus de contexte
    elif "haiku" in model_name or "mini" in model_name:
        return 5   # Petits modèles → moins de contexte
    else:
        return 10  # Par défaut
```

### 2. **Réranking des résultats**

Améliorer la pertinence avec un modèle de réranking :

```python
# Récupère 20 chunks
results = search(n_results=20)

# Réordonne avec un modèle plus précis
reranked = reranker.rank(query, results)

# Garde les 5 meilleurs
top_5 = reranked[:5]
```

### 3. **Chunking intelligent**

Au lieu de chunks de taille fixe, découper par :
- Paragraphes
- Sections
- Sémantique (semantic chunking)

### 4. **Cache de recherche**

Si la même question est posée plusieurs fois, utiliser un cache.

---

## 📊 Configuration actuelle

| Paramètre | Valeur | Fichier |
|-----------|--------|---------|
| **Taille chunk** | 1000 caractères | `pdf_processor.py:11` |
| **Overlap chunk** | 200 caractères | `pdf_processor.py:11` |
| **Chunks récupérés** | 5 | `main.py:182` |
| **Modèle embedding** | all-MiniLM-L6-v2 | `vector_store.py:20` |
| **Base vectorielle** | ChromaDB (local) | `vector_store.py:14` |

---

## 🎯 Recommandations

### **Pour améliorer la qualité des réponses** :
1. ✅ Augmenter `n_results` de 5 → 10 chunks
2. ✅ Ajouter un réranker (ex: cohere-rerank)
3. ✅ Utiliser un meilleur modèle d'embedding (ex: bge-large)

### **Pour optimiser les coûts** :
1. ✅ Adapter le nombre de chunks au modèle
2. ✅ N'utiliser le RAG que si le document est trop grand
3. ✅ Utiliser le cache pour les questions répétées

### **Pour la production** :
1. ✅ Migrer vers Pinecone/Qdrant (cloud)
2. ✅ Ajouter des métadonnées riches (dates, auteurs, sections)
3. ✅ Implémenter un système de logging des requêtes

---

## 💡 Voulez-vous que j'implémente ces optimisations ?

Je peux ajouter :
1. **Nombre de chunks adaptatif** selon le modèle
2. **Option pour désactiver le RAG** si le document est petit
3. **Réranking** pour améliorer la pertinence
4. **Interface pour ajuster n_results** depuis le frontend

Dites-moi ce qui vous intéresse le plus ! 🚀
