from dotenv import load_dotenv

load_dotenv()  # debe ejecutarse antes que cualquier otro import de la app

from contextlib import asynccontextmanager  # noqa: E402
from datetime import UTC, datetime, timedelta  # noqa: E402

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402

from app import classifier, db  # noqa: E402
from app.models import TicketCreate, TicketOut, TicketUpdate  # noqa: E402

templates = Jinja2Templates(directory="templates")

_PRIORITY_DAYS = {"P1": 0, "P2": 1, "P3": 2}


def _enrich(tickets: list[dict]) -> list[dict]:
    now = datetime.now(UTC)
    for t in tickets:
        created = datetime.fromisoformat(t["created_at"])
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        days = _PRIORITY_DAYS.get(t["priority"], 2)
        due = created + timedelta(days=days)
        t["due_date"] = due.strftime("%Y-%m-%d")
        t["overdue"] = due < now and t["status"] not in ("resolved", "closed")
    return tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="TriageBot", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    tickets = _enrich(db.list_tickets(status="open"))
    return templates.TemplateResponse("index.html", {"request": request, "tickets": tickets})


@app.post("/tickets", status_code=201)
def create_ticket(request: Request, payload: TicketCreate):
    try:
        classification = classifier.classify_ticket(payload.title, payload.description)
    except Exception:
        classification = classifier.FALLBACK_CLASSIFICATION

    ticket = db.create_ticket(
        title=payload.title,
        description=payload.description,
        category=classification["category"],
        priority=classification["priority"],
        tags=classification["tags"],
    )

    if "text/html" in request.headers.get("accept", ""):
        tickets = _enrich(db.list_tickets())
        return templates.TemplateResponse(
            "_tickets_table.html", {"request": request, "tickets": tickets}
        )
    return TicketOut.model_validate(ticket)


@app.get("/tickets")
def list_tickets(
    request: Request,
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
):
    tickets = _enrich(
        db.list_tickets(category=category, priority=priority, status=status, assignee=assignee)
    )

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "_tickets_table.html", {"request": request, "tickets": tickets}
        )
    return tickets


@app.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(request: Request, ticket_id: int, payload: TicketUpdate):
    ticket = db.update_ticket(
        ticket_id,
        status=payload.status,
        priority=payload.priority,
        assignees=payload.assignees,
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if "text/html" in request.headers.get("accept", ""):
        tickets = _enrich(db.list_tickets())
        return templates.TemplateResponse(
            "_tickets_table.html", {"request": request, "tickets": tickets}
        )
    return ticket
