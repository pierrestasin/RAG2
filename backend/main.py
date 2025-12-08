"""
RAG Application - Backend API
FastAPI application with multi-model support (OpenAI, Claude, Gemini)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import json
from dotenv import load_dotenv

# Charge le .env depuis le répertoire parent (override=True pour écraser les variables d'environnement système)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

# Import des services
from pdf_processor import pdf_processor
from config import vector_store  # Import du vector store selon le mode (local ou cloud)
from llm_service import llm_service

app = FastAPI(
    title="RAG API",
    description="RAG avec support multi-modèles (OpenAI, Claude, Gemini)",
    version="2.0.0"
)

# CORS - Configuration dynamique pour production
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = allowed_origins_env.split(",") if allowed_origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PDF_UPLOAD_PATH = os.getenv("PDF_UPLOAD_PATH", "./data/pdfs")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# Création des dossiers nécessaires
os.makedirs(PDF_UPLOAD_PATH, exist_ok=True)
os.makedirs(os.getenv("CHROMA_DB_PATH", "./data/chroma_db"), exist_ok=True)

# Models Pydantic
class QueryRequest(BaseModel):
    question: str
    model: str  # "openai", "claude", "gemini"
    selected_files: List[str] = []  # Liste des fichiers à interroger

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    sources_summary: Optional[str] = None  # Résumé lisible des sources
    model_used: str
    tokens_used: Optional[int] = None
    cache_hit: Optional[bool] = None
    chunks_retrieved: Optional[int] = None
    optimal_chunks: Optional[int] = None
    reranking_used: Optional[bool] = None

# Routes
@app.get("/")
async def root():
    return {"message": "RAG API v2.0 - Ready", "status": "ok"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models_available": ["openai", "openai-mini", "claude", "claude-haiku", "gemini", "gemini-exp"],
        "chroma_db": os.path.exists(os.getenv("CHROMA_DB_PATH", "./data/chroma_db"))
    }

@app.get("/models")
async def get_available_models():
    """Retourne la liste des modèles disponibles pour chaque provider"""
    try:
        # Charge le fichier des modèles disponibles
        models_file = os.path.join(os.path.dirname(__file__), 'available_models.json')

        if not os.path.exists(models_file):
            # Si le fichier n'existe pas, génère-le
            import subprocess
            subprocess.run([
                os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'python'),
                os.path.join(os.path.dirname(__file__), 'fetch_models.py')
            ], check=True, capture_output=True)

        with open(models_file, 'r', encoding='utf-8') as f:
            models = json.load(f)

        # Organise les modèles avec des métadonnées
        organized_models = {
            "openai": {
                "provider": "OpenAI",
                "models": [
                    {"id": m, "name": m.replace("-", " ").title(), "available": True}
                    for m in models.get("openai", [])
                ]
            },
            "anthropic": {
                "provider": "Anthropic",
                "models": [
                    {"id": m, "name": m.replace("-", " ").title(), "available": True}
                    for m in models.get("anthropic", [])
                ]
            },
            "google": {
                "provider": "Google",
                "models": [
                    {"id": m, "name": m.replace("-", " ").title(), "available": True}
                    for m in models.get("google", [])
                ]
            }
        }

        return organized_models

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des modèles: {str(e)}")

@app.get("/documents")
async def list_documents():
    """Liste tous les documents uploadés"""
    try:
        documents = vector_store.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des documents: {str(e)}")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload et indexation d'un PDF"""

    # Validation du fichier
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    # Vérifie la taille du fichier
    file.file.seek(0, 2)  # Va à la fin du fichier
    file_size = file.file.tell()  # Obtient la position (taille)
    file.file.seek(0)  # Retourne au début

    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Fichier trop volumineux (max {MAX_FILE_SIZE_MB}MB)")

    try:
        # Sauvegarde le fichier
        file_path = os.path.join(PDF_UPLOAD_PATH, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Traite le PDF
        processed = pdf_processor.process_pdf(file_path, file.filename)

        # Indexe dans ChromaDB
        result = vector_store.add_document(
            filename=processed["filename"],
            chunks=processed["chunks"],
            metadatas=processed["metadatas"]
        )

        return {
            "message": "Upload et indexation réussis",
            "filename": file.filename,
            "total_pages": processed["total_pages"],
            "chunks_added": result["chunks_added"]
        }

    except Exception as e:
        # Nettoie le fichier en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")

@app.post("/query", response_model=ChatResponse)
async def query(request: QueryRequest):
    """Interroge les documents avec le modèle choisi"""

    try:
        # Recherche dans ChromaDB avec optimisations (adaptative n_results, reranking, cache)
        search_results = vector_store.search(
            query=request.question,
            selected_files=request.selected_files if request.selected_files else None,
            n_results=10,  # Base: 10 chunks (adapté automatiquement selon le modèle)
            model_name=request.model,
            use_reranking=True  # Active le réranking Cohere si disponible
        )

        # Vérifie si on a des résultats
        if not search_results["documents"]:
            return ChatResponse(
                answer="Aucun document trouvé. Veuillez d'abord uploader des PDFs.",
                sources=[],
                model_used=request.model,
                tokens_used=None
            )

        # Prépare le contexte pour le LLM
        context = "\n\n".join([
            f"[Document: {meta['filename']}, Page {meta['page']}]\n{doc}"
            for doc, meta in zip(search_results["documents"], search_results["metadatas"])
        ])

        # Interroge le LLM
        llm_response = llm_service.query(
            question=request.question,
            context=context,
            model=request.model
        )

        # Prépare les sources (groupées par fichier)
        # Groupe par fichier et collecte toutes les pages
        file_pages = {}
        for meta in search_results["metadatas"]:
            filename = meta["filename"]
            page = meta["page"]
            if filename not in file_pages:
                file_pages[filename] = set()
            file_pages[filename].add(page)

        # Crée une seule source par fichier avec toutes les pages
        sources = []
        for filename, pages_set in file_pages.items():
            pages_sorted = sorted(list(pages_set))
            sources.append({
                "filename": filename,
                "pages": pages_sorted,  # Liste de toutes les pages utilisées
                "page_count": len(pages_sorted)
            })

        # Génère un résumé lisible des sources
        if len(sources) == 0:
            sources_summary = "Aucune source"
        elif len(sources) == 1:
            filename = sources[0]["filename"]
            pages = sources[0]["pages"]
            if len(pages) == 1:
                sources_summary = f"Page {pages[0]} ({filename})"
            elif len(pages) <= 5:
                pages_str = ", ".join(map(str, pages))
                sources_summary = f"Pages {pages_str} ({filename})"
            else:
                pages_preview = ", ".join(map(str, pages[:3]))
                sources_summary = f"Pages {pages_preview}... ({len(pages)} pages) - {filename}"
        else:
            total_pages = sum(s["page_count"] for s in sources)
            sources_summary = f"{total_pages} pages de {len(sources)} documents"

        return ChatResponse(
            answer=llm_response["answer"],
            sources=sources,
            sources_summary=sources_summary,
            model_used=llm_response["model"],
            tokens_used=llm_response["tokens"],
            cache_hit=search_results.get("cache_hit", False),
            chunks_retrieved=search_results.get("n_results", 0),
            optimal_chunks=search_results.get("optimal_chunks", 0),
            reranking_used=search_results.get("reranking_used", False)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la requête: {str(e)}")

@app.post("/cache/clear")
async def clear_cache():
    """Vide le cache de requêtes"""
    try:
        result = vector_store.clear_cache()
        return {"status": "success", "message": "Cache cleared", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du vidage du cache: {str(e)}")

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Supprime un document"""

    try:
        # Supprime de ChromaDB
        result = vector_store.delete_document(filename)

        # Supprime le fichier physique
        file_path = os.path.join(PDF_UPLOAD_PATH, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        if result["deleted"] > 0:
            return {
                "message": f"Document {filename} supprimé avec succès",
                "chunks_deleted": result["deleted"]
            }
        else:
            raise HTTPException(status_code=404, detail=f"Document {filename} non trouvé")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
