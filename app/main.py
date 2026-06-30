from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

from app import classifier, db
from app.models import TicketCreate, TicketOut, TicketUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="TriageBot", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketCreate):
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
    return ticket


@app.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
):
    return db.list_tickets(category=category, priority=priority, status=status)


@app.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate):
    ticket = db.update_ticket(ticket_id, status=payload.status, priority=payload.priority)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
