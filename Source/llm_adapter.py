"""
Adaptateur Google Gemini avec interface identique au SDK Anthropic.
Cle gratuite : https://aistudio.google.com
"""

import os
from google import genai
from google.genai import types

__version__ = "llm_adapter/gemini-2.0-flash"

# Correspondance des modeles Claude -> Gemini
_MODEL_MAP = {
    "claude-sonnet-4-5":          "gemini-2.0-flash",
    "claude-haiku-4-5-20251001":  "gemini-2.0-flash",
    "claude-opus-4-7":            "gemini-2.0-flash",
    "claude-sonnet-4-6":          "gemini-2.0-flash",
}

_client_instance = None


class _Content:
    def __init__(self, text: str):
        self.text = text


class _Usage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _Response:
    def __init__(self, text: str, input_tokens: int, output_tokens: int):
        self.content = [_Content(text)]
        self.usage = _Usage(input_tokens, output_tokens)


class _Messages:
    def create(self, model: str, max_tokens: int, system: str, messages: list) -> _Response:
        global _client_instance
        if _client_instance is None:
            raise RuntimeError("Anthropic client non initialise. Appelez Anthropic(api_key=...)")

        gemini_model = _MODEL_MAP.get(model, "gemini-2.0-flash")

        user_content = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_content = msg["content"]
                break

        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        )

        for attempt in range(5):
            try:
                response = _client_instance.models.generate_content(
                    model=gemini_model,
                    contents=user_content,
                    config=config,
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < 4:
                    import time as _time
                    wait = 60 * (attempt + 1)
                    print(f"  [Rate limit] Attente {wait}s avant réessai ({attempt+1}/4)...")
                    _time.sleep(wait)
                else:
                    raise

        input_tokens  = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
        output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
        text = response.text or ""

        return _Response(text, input_tokens, output_tokens)


class Anthropic:
    def __init__(self, api_key: str = None):
        global _client_instance
        api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY manquante.\n"
                "Obtenez-la gratuitement sur : https://aistudio.google.com\n"
                "Puis ajoutez dans .env : GEMINI_API_KEY=AIza..."
            )
        _client_instance = genai.Client(api_key=api_key)
        self.messages = _Messages()

    @property
    def __version__(self):
        return f"llm_adapter/gemini-2.0-flash"


# Compatibilite avec les blocs except anthropic.APIError / RateLimitError
class APIError(Exception):
    pass

class RateLimitError(APIError):
    pass


class GeminiEmbeddingFunction:

    EMBEDDING_MODEL = "models/gemini-embedding-001"
    BATCH_SIZE = 100  # max textes par appel API Gemini

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY manquante dans .env\n"
                "Cle gratuite : https://aistudio.google.com"
            )
        self._client = genai.Client(api_key=api_key)

    def name(self) -> str:
        return "GeminiEmbeddingFunction"

    def _embed(self, input) -> list:
        all_embeddings = []
        for i in range(0, len(input), self.BATCH_SIZE):
            batch = list(input[i : i + self.BATCH_SIZE])
            for attempt in range(5):
                try:
                    result = self._client.models.embed_content(
                        model=self.EMBEDDING_MODEL,
                        contents=batch,
                    )
                    all_embeddings.extend([e.values for e in result.embeddings])
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 4:
                        wait = 15 * (attempt + 1)
                        import time as _time
                        _time.sleep(wait)
                    else:
                        raise
        return all_embeddings

    def __call__(self, input) -> list:
        return self._embed(input)

    def embed_query(self, input) -> list:
        return self._embed(input)
