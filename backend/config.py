"""
Configuration pour basculer entre version locale (lourde) et cloud (légère)
"""
import os

# Mode de déploiement
# "local" = SentenceTransformer local (~800MB RAM, gratuit après installation)
# "cloud" = OpenAI API embeddings (~50MB RAM, coût ~$0.0001 par 1000 tokens)
DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "cloud")

print(f"🔧 Deployment mode: {DEPLOYMENT_MODE}")

# Import du bon vector store selon le mode
if DEPLOYMENT_MODE == "local":
    from backend.vector_store import vector_store
    print("✓ Using local embeddings (SentenceTransformer)")
else:
    from backend.vector_store_light import vector_store
    print("✓ Using cloud embeddings (OpenAI API)")

__all__ = ["vector_store"]
