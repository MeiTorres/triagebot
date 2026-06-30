"""
Elimina tickets sin responsables e inserta los tickets del seed_tickets.json
clasificándolos con la IA (con fallback si falla).

Uso: python scripts/seed.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import classifier, db  # noqa: E402
from app.team import auto_assign  # noqa: E402

SEED_FILE = Path(__file__).parent.parent / "seed_tickets.json"


def main():
    # 1. Eliminar tickets sin responsables
    with db.get_conn() as conn:
        deleted = conn.execute(
            "DELETE FROM tickets WHERE assignees = '[]' OR assignees IS NULL"
        ).rowcount
    print(f"Eliminados {deleted} ticket(s) sin responsables.")

    # 2. Leer seed
    tickets_data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    print(f"Insertando {len(tickets_data)} tickets del seed…")

    ok = 0
    for i, item in enumerate(tickets_data, 1):
        title = item["title"]
        description = item["description"]
        created_at = item["created_at"]

        try:
            cl = classifier.classify_ticket(title, description)
        except Exception:
            cl = classifier.FALLBACK_CLASSIFICATION

        assignees = auto_assign(cl["priority"], cl["category"])

        with db.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO tickets
                    (title, description, category, priority,
                     tags, assignees, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)
                """,
                (
                    title, description,
                    cl["category"], cl["priority"],
                    json.dumps(cl["tags"]),
                    json.dumps(assignees),
                    created_at, created_at,
                ),
            )
        ok += 1
        label = f"{cl['priority']} {cl['category']:15s}"
        print(f"  [{i:>3}/{len(tickets_data)}] {label} → {title[:50]}")

    print(f"\nListo. {ok} tickets insertados.")


if __name__ == "__main__":
    main()
