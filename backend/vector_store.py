"""
Vector Store Service - ChromaDB avec optimisations RAG
Gestion de la base vectorielle pour le RAG avec:
- Modèle d'embedding optimisé (all-MiniLM-L6-v2) pour contraintes RAM
- Réranking avec Cohere
- Cache de requêtes
- Récupération adaptative de chunks
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
import hashlib
import cohere
from diskcache import Cache

class VectorStore:
    def __init__(self):
        # Init ChromaDB
        self.chroma_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.client = chromadb.PersistentClient(path=self.chroma_path)

        # Supprime l'ancienne collection si elle existe avec mauvaise dimension
        try:
            self.client.delete_collection(name="documents")
            print("🗑️  Deleted old collection with wrong dimensions")
        except:
            pass

        # Crée nouvelle collection avec bonnes dimensions
        self.collection = self.client.create_collection(
            name="documents",
            metadata={"description": "RAG documents collection - MiniLM 384D"}
        )

        # Modèle d'embeddings léger (all-MiniLM-L6-v2)
        # Optimisé pour Render free tier (512MB RAM)
        print("🔄 Loading MiniLM embedding model (384 dimensions)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ MiniLM model loaded (~80MB RAM)")

        # Réranker Cohere (optionnel, si clé API disponible)
        self.cohere_client = None
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                self.cohere_client = cohere.Client(cohere_key)
                print("✓ Cohere reranker enabled")
            except Exception as e:
                print(f"⚠️  Cohere reranker disabled: {e}")
        else:
            print("ℹ️  Cohere reranker disabled (no API key)")

        # Cache de requêtes (évite les recherches répétées)
        cache_path = os.path.join(os.path.dirname(self.chroma_path), "query_cache")
        self.query_cache = Cache(cache_path)
        print(f"✓ Query cache enabled at {cache_path}")

    def add_document(self, filename: str, chunks: List[str], metadatas: List[Dict]):
        """Ajoute un document chunké dans ChromaDB"""

        # Génère des IDs uniques
        doc_id = hashlib.md5(filename.encode()).hexdigest()
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

        # Génère les embeddings
        print(f"🔄 Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_model.encode(
            chunks,
            show_progress_bar=False,
            normalize_embeddings=True  # Normalisation pour meilleure similarité cosine
        ).tolist()

        # Ajoute à la collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        return {
            "filename": filename,
            "chunks_added": len(chunks),
            "doc_id": doc_id
        }

    def _get_optimal_n_results(self, model_name: str, base_n_results: int = 10) -> int:
        """
        Détermine le nombre optimal de chunks à récupérer selon le modèle

        Fenêtres de contexte:
        - GPT-4o, Claude Opus 4.5, Gemini 2.5 Pro: 200K tokens → 20 chunks
        - Claude Sonnet 4.5 (1M beta): 200K tokens → 20 chunks (ou 50+ si beta activé)
        - GPT-4o-mini, Claude Haiku: 128K-200K tokens → 15 chunks
        - Petits modèles: 8-32K tokens → 8 chunks
        """
        model_lower = model_name.lower()

        # Grands modèles avec 200K+ tokens
        if any(x in model_lower for x in ['opus-4-5', 'gpt-4o', 'gemini-2.5-pro', 'gemini-pro-latest']):
            return 20

        # Modèles moyens (128-200K tokens)
        elif any(x in model_lower for x in ['sonnet-4-5', 'haiku-4-5', 'gpt-4o-mini', 'gemini-2.5-flash', 'gemini-2.0']):
            return 15

        # Petits modèles
        elif any(x in model_lower for x in ['haiku', 'mini', 'flash-lite']):
            return 8

        # Par défaut
        return base_n_results

    def _should_bypass_rag(self, selected_files: List[str], model_name: str) -> bool:
        """
        Détermine si on doit bypasser le RAG (document assez petit pour tenir dans le contexte)

        Si le document total fait moins de 50% de la fenêtre de contexte du modèle,
        on peut envoyer tout le document directement sans RAG.
        """
        # TODO: Implémenter la logique de calcul de taille
        # Pour l'instant, toujours utiliser le RAG
        return False

    def search(
        self,
        query: str,
        selected_files: Optional[List[str]] = None,
        n_results: int = 10,
        model_name: str = "gemini-2.5-flash",
        use_reranking: bool = True
    ) -> Dict:
        """
        Recherche sémantique dans les documents avec optimisations

        Args:
            query: Question de l'utilisateur
            selected_files: Liste des fichiers à rechercher (None = tous)
            n_results: Nombre de chunks à récupérer (défaut: 10, adapté au modèle si fourni)
            model_name: Nom du modèle utilisé (pour adapter n_results)
            use_reranking: Utiliser le réranking Cohere si disponible

        Returns:
            Dict avec documents, metadatas, distances, et scores de reranking
        """

        # Cache key
        cache_key = hashlib.md5(
            f"{query}_{selected_files}_{model_name}".encode()
        ).hexdigest()

        # Vérifie le cache
        cached_result = self.query_cache.get(cache_key)
        if cached_result:
            print("✓ Cache hit")
            cached_result["cache_hit"] = True
            return cached_result

        # Adapte n_results au modèle
        optimal_n = self._get_optimal_n_results(model_name, n_results)

        # Si réranking activé, récupère plus de chunks pour mieux réranker
        initial_n = optimal_n * 2 if (use_reranking and self.cohere_client) else optimal_n

        # Génère embedding de la question
        query_embedding = self.embedding_model.encode(
            query,
            normalize_embeddings=True
        ).tolist()

        # Filtre par fichiers si spécifié
        where_filter = None
        if selected_files:
            where_filter = {"filename": {"$in": selected_files}}

        # Recherche dans ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=initial_n,
            where=where_filter
        )

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        # Réranking avec Cohere si disponible
        rerank_scores = None
        if use_reranking and self.cohere_client and documents:
            try:
                print(f"🔄 Reranking {len(documents)} chunks with Cohere...")
                rerank_response = self.cohere_client.rerank(
                    query=query,
                    documents=documents,
                    top_n=optimal_n,
                    model="rerank-english-v3.0"
                )

                # Réorganise les résultats selon le reranking
                reranked_docs = []
                reranked_metas = []
                reranked_dists = []
                rerank_scores = []

                for result in rerank_response.results:
                    idx = result.index
                    reranked_docs.append(documents[idx])
                    reranked_metas.append(metadatas[idx])
                    reranked_dists.append(distances[idx])
                    rerank_scores.append(result.relevance_score)

                documents = reranked_docs
                metadatas = reranked_metas
                distances = reranked_dists

                print(f"✓ Reranked to top {len(documents)} chunks")

            except Exception as e:
                print(f"⚠️  Reranking failed: {e}")
                # Continue sans reranking
                documents = documents[:optimal_n]
                metadatas = metadatas[:optimal_n]
                distances = distances[:optimal_n]
        else:
            # Sans réranking, garde juste les N premiers
            documents = documents[:optimal_n]
            metadatas = metadatas[:optimal_n]
            distances = distances[:optimal_n]

        result = {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
            "rerank_scores": rerank_scores,
            "n_results": len(documents),
            "cache_hit": False,
            "optimal_chunks": optimal_n,
            "initial_chunks": initial_n,
            "reranking_used": bool(use_reranking and self.cohere_client and rerank_scores)
        }

        # Met en cache (expire après 1h)
        self.query_cache.set(cache_key, result, expire=3600)

        return result

    def list_documents(self) -> List[Dict]:
        """Liste tous les documents indexés"""

        # Récupère tous les documents
        all_docs = self.collection.get()

        # Groupe par filename
        docs_dict = {}
        for metadata in all_docs["metadatas"]:
            filename = metadata.get("filename")
            if filename and filename not in docs_dict:
                docs_dict[filename] = {
                    "filename": filename,
                    "pages": metadata.get("total_pages", 0),
                    "chunks": 0
                }
            if filename:
                docs_dict[filename]["chunks"] += 1

        return list(docs_dict.values())

    def delete_document(self, filename: str):
        """Supprime un document de la base"""

        # Récupère tous les IDs du document
        results = self.collection.get(
            where={"filename": filename}
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])

            # Invalide le cache (supprime toutes les entrées)
            self.query_cache.clear()

            return {"deleted": len(results["ids"]), "filename": filename}

        return {"deleted": 0, "filename": filename}

    def clear_cache(self):
        """Vide le cache de requêtes"""
        self.query_cache.clear()
        return {"cache_cleared": True}

# Instance globale
vector_store = VectorStore()
