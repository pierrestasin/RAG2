#!/usr/bin/env python3
"""
Test du RAG amélioré avec nettoyage des références
"""
import sys
import os

# Ajoute le backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pdf_processor import PDFProcessor
from vector_store import VectorStore
from llm_service import LLMService

def test_improved_rag():
    print("🧪 Test du RAG amélioré\n")

    # 1. Traite le PDF scientifique
    print("📄 Traitement du PDF scientifique...")
    processor = PDFProcessor()
    pdf_path = "sciadv.ady9493.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF {pdf_path} non trouvé")
        return

    result = processor.process_pdf(pdf_path, "sciadv.ady9493.pdf")
    print(f"✓ {result['total_pages']} pages → {len(result['chunks'])} chunks\n")

    # 2. Réinitialise et réindexe dans ChromaDB
    print("🔄 Réindexation dans ChromaDB...")

    # Note: VectorStore se réinitialise automatiquement au démarrage
    # Pour forcer la réinitialisation, on pourrait supprimer le dossier chroma_db

    vector_store = VectorStore()

    # Supprime l'ancien document s'il existe
    try:
        vector_store.delete_document("sciadv.ady9493.pdf")
    except:
        pass

    # Ajoute le nouveau
    vector_store.add_document(
        filename=result["filename"],
        chunks=result["chunks"],
        metadatas=result["metadatas"]
    )
    print("✓ Document indexé\n")

    # 3. Test de recherche
    print("🔍 Test de recherche...")
    test_queries = [
        "What is the long chronology for Sahul peopling?",
        "What methods were used in this study?",
        "What are the main findings about genomic evidence?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")

        search_results = vector_store.search(
            query=query,
            selected_files=["sciadv.ady9493.pdf"],
            n_results=5,
            model_name="gemini-2.5-flash",
            use_reranking=True
        )

        print(f"   Chunks récupérés: {search_results['n_results']}")
        print(f"   Reranking utilisé: {search_results.get('reranking_used', False)}")

        # Affiche le premier chunk récupéré
        if search_results["documents"]:
            first_doc = search_results["documents"][0]
            first_meta = search_results["metadatas"][0]
            print(f"   Top chunk (page {first_meta['page']}):")
            print(f"   {first_doc[:300]}...")

    print("\n✅ Test terminé avec succès!")
    print("\n💡 Les chunks devraient maintenant être plus pertinents,")
    print("   sans pollution par les références bibliographiques.")

if __name__ == "__main__":
    test_improved_rag()
