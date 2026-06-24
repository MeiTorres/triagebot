# CLAUDE.md

Este repo es una plantilla docente para construir **TriageBot**, una aplicación
FastAPI que clasifica tickets de soporte con la API de Claude.

## Stack (innegociable)

- Python 3.11+
- FastAPI
- SQLite
- HTMX + Jinja2
- Tailwind (por CDN)
- SDK oficial de Anthropic
- pytest
- ruff

## Reglas del taller

Estas reglas no son metodología: son condiciones del bootcamp. Se cumplen seas
del equipo que seas.

1. No modifiques `tests/test_acceptance.py` salvo que el profesor lo indique
   expresamente.
2. Nunca hardcodees una API key en el código.
3. Lee la API key desde la variable de entorno.
4. `.env` nunca se commitea. Comprueba que está en `.gitignore` antes de tu
   primer commit.

## Comandos útiles

```bash
pytest -v
pytest --cov=app
ruff check .
uvicorn app.main:app --reload
```
