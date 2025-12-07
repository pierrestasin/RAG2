"""
Service LLM - Support multi-modèles dynamique
Support de tous les modèles OpenAI, Claude, et Gemini
"""
import os
import json
from typing import List, Dict
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai

class LLMService:
    def __init__(self):
        # Clients créés à la demande
        self._openai_client = None
        self._anthropic_client = None
        self._gemini_configured = False

        # Charge les modèles disponibles
        self._available_models = self._load_available_models()

    def _load_available_models(self) -> Dict:
        """Charge la liste des modèles disponibles depuis le fichier JSON"""
        try:
            models_file = os.path.join(os.path.dirname(__file__), 'available_models.json')
            if os.path.exists(models_file):
                with open(models_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass

        # Fallback sur des modèles par défaut si le fichier n'existe pas
        return {
            "openai": ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"],
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
            "google": ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-exp-1206"]
        }

    def _detect_provider(self, model_id: str) -> str:
        """Détecte le provider depuis l'ID du modèle"""
        model_lower = model_id.lower()

        # Vérifie dans les modèles connus
        if model_id in self._available_models.get("openai", []):
            return "openai"
        elif model_id in self._available_models.get("anthropic", []):
            return "anthropic"
        elif model_id in self._available_models.get("google", []):
            return "google"

        # Détection par préfixe/pattern
        if model_lower.startswith(("gpt-", "o1", "o3")):
            return "openai"
        elif model_lower.startswith("claude"):
            return "anthropic"
        elif model_lower.startswith(("gemini", "gemma")):
            return "google"

        # Par défaut, essaye de deviner
        raise ValueError(f"Provider inconnu pour le modèle: {model_id}")

    def _get_openai_client(self):
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "sk-your-key-here":
                raise ValueError("OpenAI API key not configured")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key or api_key == "sk-ant-your-key-here":
                raise ValueError("Anthropic API key not configured")
            self._anthropic_client = Anthropic(api_key=api_key)
        return self._anthropic_client

    def _configure_gemini(self):
        if not self._gemini_configured:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key or api_key == "AIzaSy-your-key-here":
                raise ValueError("Gemini API key not configured")
            genai.configure(api_key=api_key)
            self._gemini_configured = True

    def query(self, question: str, context: str, model: str) -> Dict:
        """
        Interroge le modèle avec le contexte RAG

        Args:
            question: Question de l'utilisateur
            context: Contexte extrait des documents
            model: ID du modèle (ex: "gpt-4o", "claude-3-5-sonnet-20241022", "gemini-2.0-flash-exp")

        Returns:
            Dict avec answer, tokens, model
        """

        prompt = f"""Tu es un assistant d'analyse de documents.
Réponds à la question en te basant UNIQUEMENT sur le contexte fourni.
Fournis une réponse détaillée et complète, en expliquant tous les points pertinents.
Cite toujours tes sources avec les numéros de page.

CONTEXTE:
{context}

QUESTION:
{question}

RÉPONSE:"""

        # Détecte automatiquement le provider
        provider = self._detect_provider(model)

        if provider == "openai":
            return self._query_openai(prompt, model)
        elif provider == "anthropic":
            return self._query_claude(prompt, model)
        elif provider == "google":
            return self._query_gemini(prompt, model)
        else:
            raise ValueError(f"Provider inconnu: {provider}")

    def _query_openai(self, prompt: str, model: str) -> Dict:
        """Query OpenAI avec n'importe quel modèle"""
        client = self._get_openai_client()

        # Configuration adaptée selon le modèle
        config = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Les modèles o1/o3 n'acceptent pas temperature et max_tokens
        if not model.startswith(("o1", "o3")):
            config["temperature"] = 0.1
            config["max_tokens"] = 4000

        response = client.chat.completions.create(**config)

        return {
            "answer": response.choices[0].message.content,
            "tokens": response.usage.total_tokens if response.usage else None,
            "model": model
        }

    def _query_claude(self, prompt: str, model: str) -> Dict:
        """Query Claude avec n'importe quel modèle"""
        client = self._get_anthropic_client()

        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "answer": response.content[0].text,
            "tokens": response.usage.input_tokens + response.usage.output_tokens if response.usage else None,
            "model": model
        }

    def _query_gemini(self, prompt: str, model: str) -> Dict:
        """Query Gemini avec n'importe quel modèle"""
        self._configure_gemini()

        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.1,
                'max_output_tokens': 4000,
            }
        )

        return {
            "answer": response.text,
            "tokens": None,  # Gemini ne retourne pas toujours les tokens
            "model": model
        }

# Instance globale
llm_service = LLMService()
