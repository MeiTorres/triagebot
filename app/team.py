import random

TEAM = [
    "Ana García",
    "Carlos López",
    "Mei Torres",
    "Naroa Etxebarria",
    "David Sanz",
]

_ASSIGNEE_COUNT = {"P1": (2, 3), "P2": (1, 2), "P3": (1, 1)}


def auto_assign(priority: str, category: str) -> list[str]:
    """Return a random subset of team members based on priority (and urgency)."""
    lo, hi = _ASSIGNEE_COUNT.get(priority, (1, 1))
    # urgent category always gets at least 2 assignees
    if category == "urgent" and hi < 2:
        hi = 2
    count = random.randint(lo, min(hi, len(TEAM)))
    return random.sample(TEAM, count)
