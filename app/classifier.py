import json
import os
import time

from openai import OpenAI

FALLBACK_CLASSIFICATION = {"category": "question", "priority": "P3", "tags": []}

_SYSTEM_PROMPT = """\
Devuelve EXCLUSIVAMENTE un objeto JSON válido. Sin markdown, sin saludos, \
sin texto antes ni después. Los valores permitidos son: \
category ∈ {bug, feature_request, question, urgent}, priority ∈ {P1, P2, P3}. \
No inventes categorías. Máximo 5 tags.

Ejemplo de respuesta válida:
{"category": "bug", "priority": "P2", "tags": ["login", "crash"]}"""

_ALLOWED_CATEGORIES = {"bug", "feature_request", "question", "urgent"}
_ALLOWED_PRIORITIES = {"P1", "P2", "P3"}

_MAX_RETRIES = 2
_RETRY_DELAY = 1  # segundos


def _parse_and_validate(raw: str) -> dict:
    """Parsea el JSON y valida los campos. Lanza ValueError si algo no es válido."""
    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("La respuesta no es un objeto JSON")

    category = data.get("category", "")
    if category not in _ALLOWED_CATEGORIES:
        raise ValueError(f"category inválida: {category!r}")

    priority = data.get("priority", "")
    if priority not in _ALLOWED_PRIORITIES:
        raise ValueError(f"priority inválida: {priority!r}")

    tags = data.get("tags", [])
    if not isinstance(tags, list):
        raise ValueError("tags no es una lista")
    tags = [t for t in tags if isinstance(t, str)][:5]

    return {"category": category, "priority": priority, "tags": tags}


def _call_llm(client: OpenAI, title: str, description: str) -> dict:
    """Llama al LLM y devuelve la clasificación validada. Lanza excepción si falla."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Title: {title}\n\nDescription: {description}"},
        ],
    )
    raw = response.choices[0].message.content.strip()
    return _parse_and_validate(raw)


def classify_ticket(title: str, description: str) -> dict:
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            return _call_llm(client, title, description)
        except Exception as exc:
            last_exc = exc  # noqa: F841
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY)

    return FALLBACK_CLASSIFICATION
