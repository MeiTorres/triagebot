# Bug Report — Escenarios de robustez TriageBot

Fecha: 2026-06-30

---

## Bug 1 (CRÍTICO) — PATCH acepta valores de `status` inválidos

**Escenario:** `PATCH /tickets/{id}` con `{"status": "inventado"}`

**Comportamiento observado:** El servidor respondía `200 OK` y guardaba el valor `"inventado"` en la base de datos sin ninguna validación. El ticket quedaba en un estado desconocido que ningún filtro ni transición de la UI podía manejar.

**Causa raíz:** `TicketUpdate` en `app/models.py` no tenía validadores para los campos `status` ni `priority`. Pydantic los aceptaba como cualquier string arbitrario.

**Impacto:** Corrupción silenciosa de datos. Un ticket con `status="inventado"` no aparece en ningún filtro estándar y sus botones de acción en la tabla quedan vacíos (`next_status.get("inventado", [])` devuelve `[]`).

**Corrección aplicada:** Se añadieron `@field_validator` en `TicketUpdate` para `status` y `priority`, rechazando con `422 Unprocessable Entity` cualquier valor fuera de los conjuntos permitidos (`ALLOWED_STATUSES`, `ALLOWED_PRIORITIES`).

---

## Bug 2 (MEDIO) — Los botones de cambio de estado no enviaban JSON

**Escenario:** Usuario autenticado y responsable de un ticket pulsa "▶ En curso".

**Comportamiento observado:** El estado no cambiaba. El servidor recibía el PATCH como `application/x-www-form-urlencoded` y FastAPI no podía parsear el cuerpo como `TicketUpdate` (que espera JSON), devolviendo `422` silenciosamente. La UI no mostraba ningún error.

**Causa raíz:** Los botones `hx-patch` en `_tickets_table.html` no tenían `hx-ext="json-enc"`, a diferencia del formulario de creación. HTMX sin esa extensión envía los datos como form-encoded.

**Impacto:** La funcionalidad de cambio de estado era completamente inoperativa desde la interfaz web para todos los usuarios.

**Corrección aplicada:** Se añadió `hx-ext="json-enc"` a cada botón de acción en `templates/_tickets_table.html`.

---

## Observaciones sin bug (comportamiento correcto o esperado)

| Escenario | Veredicto | Nota |
|-----------|-----------|------|
| Title vacío o solo espacios | ✅ Correcto | `@field_validator` en `TicketCreate` rechaza con 422 |
| Title > 200 chars | ✅ Correcto | Límite aplicado en `TicketCreate` |
| Emojis y unicode | ✅ Correcto | SQLite y Python manejan UTF-8 sin problemas |
| HTML/JS en descripción (XSS) | ✅ Seguro | El script se almacena tal cual pero Jinja2 escapa `{{ variable }}` por defecto; nunca se ejecuta |
| Inyección SQL | ✅ Seguro | Todas las queries usan placeholders `?`; el input nunca se interpola en el SQL |
| LLM caído | ✅ Correcto | El clasificador captura la excepción y devuelve `FALLBACK_CLASSIFICATION` |
| Ticket duplicado | ✅ Esperado | No hay deduplicación; cada envío genera un ID nuevo (decisión de diseño) |
| IDs malformados (`-1`, `abc`, `99999999999`) | ✅ Correcto | FastAPI devuelve 422 para tipos incorrectos y 404 para IDs inexistentes |
| 20 POSTs concurrentes | ✅ Correcto | 20/20 exitosos; SQLite con WAL soporta escrituras concurrentes moderadas |
