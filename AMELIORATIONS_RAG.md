# Améliorations RAG pour documents scientifiques avec références

## Problème résolu

Les PDFs scientifiques avec beaucoup de références bibliographiques posent des problèmes au RAG :
- **Fragmentation du texte** : Les citations `[1,2,3]` et références inline cassent la continuité sémantique
- **Chunking inadapté** : Le découpage par taille fixe coupe les paragraphes au mauvais endroit
- **Pollution des chunks** : Les pages de références diluent le contenu pertinent
- **Métadonnées parasites** : Headers, footers, numéros de page polluent les chunks

## Solutions implémentées

### 1. Nettoyage intelligent du texte ([pdf_processor.py:91-111](backend/pdf_processor.py#L91-L111))

```python
def _clean_text(self, text: str) -> str:
    """Nettoie headers, footers et métadonnées"""
    - Supprime les numéros de page isolés
    - Filtre les copyright et dates
    - Enlève les lignes trop courtes
```

### 2. Détection des sections de références ([pdf_processor.py:113-120](backend/pdf_processor.py#L113-L120))

Détecte automatiquement les marqueurs :
- "References"
- "Bibliography"
- "Works Cited"
- "Literature Cited"

### 3. Filtrage des pages de références ([pdf_processor.py:122-139](backend/pdf_processor.py#L122-L139))

```python
def _is_mostly_references(self, text: str) -> bool:
    """Skip les pages avec >50% de références"""
    - Détecte les patterns : [1], (2023), et al., DOI, URLs
    - Skip automatiquement si >50% de lignes de références
```

### 4. Réduction des références inline ([pdf_processor.py:141-149](backend/pdf_processor.py#L141-L149))

Simplifie sans supprimer complètement :
- `[1,2,3,4,5]` → `[citations]`
- `A et al., B et al., C et al.` → `[multiple citations]`
- URLs longues → `[URL]`

### 5. Chunking sémantique par paragraphes ([pdf_processor.py:151-180](backend/pdf_processor.py#L151-180))

```python
def _create_semantic_chunks(self, text: str) -> List[str]:
    """Découpe par paragraphes au lieu de taille fixe"""
    - Split sur les doubles newlines (paragraphes)
    - Garde la cohérence sémantique
    - Overlap intelligent (dernières phrases)
```

## Résultats

### Avant
```
✗ Chunks pollués par les références
✗ Coupure au milieu des paragraphes
✗ Métadonnées parasites (headers/footers)
✗ Pages de références indexées
```

### Après
```
✓ Chunks propres, sans pollution
✓ Respect des limites de paragraphes
✓ Nettoyage automatique des métadonnées
✓ Pages de références filtrées
✓ Références inline simplifiées
```

## Test avec PDF scientifique

Testé avec `sciadv.ady9493.pdf` (17 pages, article Science Advances) :

```bash
python test_improved_rag.py
```

**Résultats** :
- ✓ 17 pages traitées → 17 chunks sémantiques propres
- ✓ Détection automatique des sections de références
- ✓ Filtrage des pages de références
- ✓ Reranking avec Cohere pour meilleure pertinence
- ✓ Chunks sans pollution par les citations

## Utilisation

Les améliorations sont **automatiques** ! Il suffit de :

1. **Uploader un nouveau PDF** via l'interface
   - Le système appliquera automatiquement le nettoyage

2. **Réindexer les anciens PDFs** (optionnel)
   ```bash
   # Supprimer et ré-uploader via l'interface
   # OU utiliser le script de test
   python test_improved_rag.py
   ```

## Configuration

Dans [pdf_processor.py](backend/pdf_processor.py) :

```python
PDFProcessor(
    chunk_size=1000,      # Taille max d'un chunk
    chunk_overlap=200     # Overlap entre chunks
)
```

## Améliorations futures possibles

1. **Détection de figures/tables** : Skip les légendes de figures
2. **Extraction de structure** : Détecter Introduction/Méthodes/Résultats
3. **Chunking adaptatif** : Varier la taille selon la densité du texte
4. **Multi-langue** : Améliorer pour articles non-anglais

## Impact sur la qualité

Les chunks plus propres améliorent :
- ✅ **Pertinence** : Le LLM reçoit du contenu pur, sans bruit
- ✅ **Précision** : Les embeddings capturent mieux la sémantique
- ✅ **Efficacité** : Moins de chunks parasites dans le contexte
- ✅ **Coût** : Moins de tokens utilisés pour le même résultat

---

**Note** : Les améliorations sont compatibles avec tous les modèles (OpenAI, Claude, Gemini).
