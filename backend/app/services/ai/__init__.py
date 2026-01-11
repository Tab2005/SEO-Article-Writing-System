# backend/app/services/ai/__init__.py
from .zeabur_client import ZeaburAIClient
from .intent_classifier import AIIntentClassifier

try:
    from .gemini_client import GoogleGeminiClient
except ImportError:
    GoogleGeminiClient = None

__all__ = ["ZeaburAIClient", "AIIntentClassifier", "GoogleGeminiClient"]
