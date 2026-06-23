# QA_CHECKLIST.md — Lab 5 Adversarial QA

Probád todos los escenarios y anotad el resultado.

| # | Escenario | ¿Bug? | Evidencia / notas |
|---|---|---|---|
| 1 | Title vacío o solo espacios |  |  |
| 2 | Title de 5000 caracteres |  |  |
| 3 | Emojis y caracteres unicode no latinos |  |  |
| 4 | HTML/JS en la descripción, posible XSS |  |  |
| 5 | Inyección SQL básica |  |  |
| 6 | LLM caído con API key falsa |  |  |
| 7 | Mismo ticket enviado dos veces seguidas |  |  |
| 8 | IDs malformados: -1, abc, 99999999999 |  |  |
| 9 | PATCH con valores inválidos: status inventado |  |  |
| 10 | 20 POSTs concurrentes |  |  |

Regla: primero encontrad y documentad bugs; después, si queda tiempo, arreglad los más graves.
