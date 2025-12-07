"""
Script pour récupérer les derniers modèles disponibles pour chaque éditeur
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import json

# Charge .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

print("=" * 80)
print("RÉCUPÉRATION DES DERNIERS MODÈLES DISPONIBLES")
print("=" * 80)

models_info = {
    "openai": [],
    "anthropic": [],
    "google": []
}

# ===== OPENAI =====
print("\n📦 OpenAI Models")
print("-" * 80)
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    models = client.models.list()

    # Filtre les modèles GPT récents et pertinents
    gpt_models = []
    for model in models.data:
        model_id = model.id
        # On garde les GPT-4, GPT-4o, GPT-3.5-turbo, o1, o3
        if any(keyword in model_id for keyword in ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o1', 'o3']):
            if 'vision' not in model_id and 'instruct' not in model_id:
                gpt_models.append(model_id)

    # Trie et déduplique
    gpt_models = sorted(set(gpt_models), reverse=True)

    print(f"✓ Trouvé {len(gpt_models)} modèles GPT pertinents:")
    for model in gpt_models[:15]:  # Top 15
        print(f"  - {model}")
        models_info["openai"].append(model)

except Exception as e:
    print(f"✗ Erreur OpenAI: {e}")

# ===== ANTHROPIC (Claude) =====
print("\n📦 Anthropic Claude Models")
print("-" * 80)
try:
    # L'API Anthropic ne fournit pas de liste de modèles
    # On utilise la documentation officielle (https://platform.claude.com/docs/en/about-claude/models/overview)
    claude_models = [
        # Latest Claude 4.5 models (2025)
        "claude-opus-4-5-20251101",      # Claude Opus 4.5 (Latest - Nov 2025)
        "claude-sonnet-4-5-20250929",    # Claude Sonnet 4.5 (Latest - Sep 2025)
        "claude-haiku-4-5-20251001",     # Claude Haiku 4.5 (Latest - Oct 2025)

        # Aliases (auto-update to latest)
        "claude-opus-4-5",               # Alias → claude-opus-4-5-20251101
        "claude-sonnet-4-5",             # Alias → claude-sonnet-4-5-20250929
        "claude-haiku-4-5",              # Alias → claude-haiku-4-5-20251001

        # Legacy Claude 4 models
        "claude-opus-4-1-20250805",      # Claude Opus 4.1
        "claude-sonnet-4-20250514",      # Claude Sonnet 4
        "claude-opus-4-20250514",        # Claude Opus 4

        # Claude 3.x models (legacy)
        "claude-3-7-sonnet-20250219",    # Claude 3.7 Sonnet
        "claude-3-5-haiku-20241022",     # Claude 3.5 Haiku
        "claude-3-5-sonnet-20241022",    # Claude 3.5 Sonnet (old)
        "claude-3-opus-20240229",        # Claude 3 Opus
        "claude-3-sonnet-20240229",      # Claude 3 Sonnet
        "claude-3-haiku-20240307"        # Claude 3 Haiku
    ]

    print(f"✓ Modèles Claude depuis documentation officielle:")
    for model in claude_models:
        print(f"  - {model}")
        models_info["anthropic"].append(model)

except Exception as e:
    print(f"✗ Erreur Claude: {e}")

# ===== GOOGLE GEMINI =====
print("\n📦 Google Gemini Models")
print("-" * 80)
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Liste tous les modèles
    gemini_models = []

    # Modèles à exclure (images, embeddings, etc.)
    exclude_patterns = [
        'nano-banana',     # Image generation (Gemini 3 Pro Image)
        'gemma-',          # Gemma models (small, not suitable for RAG)
        '-image',          # Image-related models
        'embedding',       # Embedding models
        'robotics',        # Robotics models
        'computer-use'     # Computer use models
    ]

    for model in genai.list_models():
        # On garde uniquement les modèles de génération de texte
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')

            # Exclut les modèles non-texte
            should_exclude = any(pattern in model_name.lower() for pattern in exclude_patterns)

            if not should_exclude:
                gemini_models.append(model_name)

    # Trie
    gemini_models = sorted(gemini_models, reverse=True)

    print(f"✓ Trouvé {len(gemini_models)} modèles Gemini:")
    for model in gemini_models:
        print(f"  - {model}")
        models_info["google"].append(model)

except Exception as e:
    print(f"✗ Erreur Gemini: {e}")

# ===== SAUVEGARDE =====
print("\n" + "=" * 80)
print("SAUVEGARDE DES MODÈLES")
print("=" * 80)

output_file = os.path.join(os.path.dirname(__file__), 'available_models.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(models_info, f, indent=2, ensure_ascii=False)

print(f"✓ Modèles sauvegardés dans: {output_file}")
print(f"\nRésumé:")
print(f"  - OpenAI: {len(models_info['openai'])} modèles")
print(f"  - Anthropic: {len(models_info['anthropic'])} modèles")
print(f"  - Google: {len(models_info['google'])} modèles")
print("\n" + "=" * 80)
