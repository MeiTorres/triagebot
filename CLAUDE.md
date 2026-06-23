# CLAUDE.md — Instrucciones para Claude Code

Este repo es una plantilla docente para construir **TriageBot**, una aplicación FastAPI que clasifica tickets de soporte con Claude API.

## Stack

- Python 3.11+
- FastAPI
- SQLite
- HTMX + Jinja2
- Tailwind por CDN
- Anthropic SDK oficial
- pytest
- ruff

## Estructura esperada

```text
app/main.py          # FastAPI app y endpoints
app/models.py        # Modelos y validaciones
app/db.py            # SQLite: conexión, init, queries
app/classifier.py    # Único módulo que llama a Anthropic
templates/           # HTML/Jinja2
tests/               # Tests pytest
```

## Reglas importantes

1. No modifiques `tests/test_acceptance.py` salvo que el profesor lo indique expresamente.
2. No hardcodees API keys.
3. Lee la API key desde `ANTHROPIC_API_KEY`.
4. `.env` nunca debe commitearse.
5. `app/classifier.py` es el único archivo que puede importar `anthropic`.
6. Los endpoints HTTP viven en `app/main.py`, no en `classifier.py`.
7. Si Claude/Anthropic falla, la app debe usar fallback y no devolver 500.
8. Usa errores HTTP claros: `422` para validación, `404` si no existe un ticket.
9. Mantén funciones pequeñas y legibles.
10. Después de cambios relevantes, ejecuta `pytest -v`.

## Comandos útiles

```bash
pytest -v
pytest --cov=app
ruff check .
uvicorn app.main:app --reload
```

## Flujo recomendado para equipos Spec-Driven

Antes de implementar una feature:

1. Leer `SPEC.md`.
2. Pedir `/plan`.
3. Revisar el plan.
4. Implementar.
5. Ejecutar tests.
6. Commit pequeño.

Prompt tipo:

```text
Implementa POST /tickets siguiendo SPEC.md sección 4.
Respeta CLAUDE.md.
No modifiques tests/test_acceptance.py.
El clasificador debe llamarse a través de app.classifier.classify_ticket.
Termina ejecutando pytest -v.
```

## Flujo recomendado para equipos Vibe

Puedes trabajar conversacionalmente, pero con contexto suficiente:

```text
Voy a construir TriageBot según BRIEF.md. Respeta esta estructura:
app/main.py para endpoints, app/models.py para validaciones,
app/db.py para SQLite y app/classifier.py como único módulo que llama a Claude.
Empieza implementando POST /tickets y ejecuta los tests.
```
