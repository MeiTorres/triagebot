# SPEC.md — Contrato funcional de TriageBot

> Este archivo es especialmente importante para los equipos **Spec-Driven**.  
> Los equipos Vibe pueden leerlo, pero no deberían convertirlo en una especificación larga durante el Lab 1.

## 1. Objetivo

Construir una aplicación web interna para registrar, clasificar y consultar tickets de soporte.

## 2. Modelo de datos

### Ticket

Campos mínimos:

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | int | Autogenerado |
| `title` | str | Obligatorio, 1–200 caracteres tras trim |
| `description` | str | Obligatorio, 1–5000 caracteres tras trim |
| `category` | str | `bug`, `feature_request`, `question`, `urgent` |
| `priority` | str | `P1`, `P2`, `P3` |
| `tags` | list[str] | Lista, puede estar vacía |
| `status` | str | `open`, `in_progress`, `closed` |
| `created_at` | datetime | UTC, generado en servidor |
| `updated_at` | datetime | UTC, actualizado en cambios relevantes |

Valores por defecto:

- `status`: `open`
- fallback de clasificación: `category="question"`, `priority="P3"`, `tags=[]`

## 3. Arquitectura de módulos

Estructura recomendada:

```text
app/
  __init__.py
  main.py          # FastAPI app y endpoints HTTP
  models.py        # Modelos de dominio / persistencia
  db.py            # Conexión y operaciones SQLite
  classifier.py    # ÚNICO módulo que llama a Anthropic

templates/
  index.html
  _tickets_table.html

tests/
  test_acceptance.py
```

Regla importante:

> Todo lo que llame a la API de Anthropic vive solo en `app/classifier.py`.  
> Si hay llamadas al SDK de Anthropic en `main.py`, algo se ha torcido.

## 4. API HTTP

### `GET /health`

Devuelve estado básico de la app.

Response esperado:

```json
{"status": "ok"}
```

### `POST /tickets`

Crea un ticket y lo clasifica.

Request JSON:

```json
{
  "title": "La app no carga",
  "description": "Desde esta mañana aparece una pantalla en blanco al iniciar sesión"
}
```

Response `201`:

```json
{
  "id": 1,
  "title": "La app no carga",
  "description": "Desde esta mañana aparece una pantalla en blanco al iniciar sesión",
  "category": "bug",
  "priority": "P1",
  "tags": ["login", "blank-screen"],
  "status": "open",
  "created_at": "2026-06-29T09:30:00Z",
  "updated_at": "2026-06-29T09:30:00Z"
}
```

Errores:

- `422` si `title` está vacío o supera 200 caracteres.
- `422` si `description` está vacía o supera 5000 caracteres.

### `GET /tickets`

Lista tickets.

Query params opcionales:

- `category`
- `priority`
- `status`

Ejemplo:

```text
GET /tickets?category=bug&priority=P1&status=open
```

Response `200`:

```json
[
  {
    "id": 1,
    "title": "La app no carga",
    "category": "bug",
    "priority": "P1",
    "tags": ["login"],
    "status": "open",
    "created_at": "2026-06-29T09:30:00Z",
    "updated_at": "2026-06-29T09:30:00Z"
  }
]
```

### `PATCH /tickets/{ticket_id}`

Actualiza campos editables.

Request JSON permitido:

```json
{
  "status": "in_progress",
  "priority": "P2"
}
```

Campos editables:

- `status`: `open`, `in_progress`, `closed`
- `priority`: `P1`, `P2`, `P3`

Errores:

- `404` si no existe el ticket.
- `422` si el valor no pertenece al enum permitido.

## 5. Clasificador IA

Función esperada:

```python
def classify_ticket(title: str, description: str) -> dict:
    ...
```

Contrato de salida:

```python
{
    "category": "bug" | "feature_request" | "question" | "urgent",
    "priority": "P1" | "P2" | "P3",
    "tags": list[str],
}
```

Reglas:

- Debe pedir a Claude que devuelva exclusivamente JSON válido.
- Debe parsear y validar la respuesta.
- No debe propagar excepciones del SDK.
- Si Anthropic falla, devuelve fallback:

```python
{"category": "question", "priority": "P3", "tags": []}
```

## 6. Frontend mínimo

`GET /` devuelve una página HTML con:

1. Formulario para crear ticket.
2. Tablero de tickets.
3. Filtros por categoría, prioridad y estado.

Recomendación:

- Usar Jinja2 templates.
- Usar HTMX para refrescar la tabla sin recargar toda la página.
- No escribir HTML grande como string dentro de `main.py`.

## 7. Tests obligatorios

El archivo `tests/test_acceptance.py` contiene los 5 tests de aceptación. No se modifica.

Los tests comprueban:

1. Crear un ticket válido devuelve `201` y clasificación.
2. El ticket creado queda persistido y aparece en `GET /tickets`.
3. Input inválido devuelve `422`.
4. Si el clasificador falla, se aplica fallback y la app no cae.
5. Se puede actualizar estado/prioridad y filtrar tickets.

## 8. No negociable

- No commitear `.env`.
- No hardcodear API keys.
- No propagar excepciones del SDK de Anthropic al endpoint.
- No modificar los tests de aceptación para hacerlos pasar.
- No introducir React ni frontend complejo.
