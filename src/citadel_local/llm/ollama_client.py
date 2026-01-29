from __future__ import annotations
import requests

def ollama_chat(base_url: str, model: str, messages: list[dict], timeout_s: int = 90) -> dict:
    """
    Minimal Ollama /api/chat wrapper.
    Returns parsed JSON if the model responds with JSON.
    """
    url = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        # Keep this minimal. Some models support format="json"; you can add when validated.
    }
    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    return data
