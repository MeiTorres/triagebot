import json
import os

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


def classify_ticket(title: str, description: str) -> dict:
    try:
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Title: {title}\n\nDescription: {description}",
                },
            ],
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        category = data.get("category", "question")
        if category not in _ALLOWED_CATEGORIES:
            category = "question"

        priority = data.get("priority", "P3")
        if priority not in _ALLOWED_PRIORITIES:
            priority = "P3"

        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [str(t) for t in tags if isinstance(t, str)][:5]

        return {"category": category, "priority": priority, "tags": tags}

    except Exception:
        return FALLBACK_CLASSIFICATION
