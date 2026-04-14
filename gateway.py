"""
gateway.py — Composition root and FastAPI application.

All endpoints are GET-only (ADR 0001: constrained LLM clients cannot POST).
The agent protocol envelope is passed as the `msg` query parameter.

Endpoints:
  GET /agent?msg=<envelope>       — submit any envelope (TASK:submit, TASK:status, AGENT:ping)
  GET /task/status?id=<id>        — poll task status by ID
  GET /board                      — full queue state
  GET /health                     — service health check
"""
import os
from dataclasses import asdict
from pathlib import Path
from urllib.parse import unquote_plus

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from domain.agent_gateway.core.adaptors.envelope_parser import EnvelopeParser
from domain.agent_gateway.core.envelope import Envelope
from domain.agent_gateway.core.ports.agent_tasks_queue import AgentTasksQueue
from domain.agent_gateway.core.ports.i_task_queue import ITaskQueue

# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

_TASKS_DIR = Path(os.environ.get("TASKS_DIR", Path(__file__).parent / "tasks"))

parser: EnvelopeParser = EnvelopeParser()
queue:  ITaskQueue     = AgentTasksQueue(_TASKS_DIR)

app = FastAPI(
    title="Agent Gateway",
    description="GET-only bridge between LLM web interfaces and the agent-tasks coordinator fleet.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _envelope_response(verb: str, version: str, fields: dict, body: str | None = None) -> str:
    lines = [f"AGENT/{verb} {version}"]
    for k, v in fields.items():
        if v is not None:
            lines.append(f"{k}: {v}")
    text = "\n".join(lines)
    if body:
        text += f"\n---\n{body}"
    return text


def _error_response(message: str, status_code: int = 400) -> PlainTextResponse:
    body = _envelope_response("TASK:error", "v1", {"reason": message})
    return PlainTextResponse(body, status_code=status_code)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "gateway": "agent-gateway/1.0"}


@app.get("/board")
def board():
    tasks = queue.board()
    return [asdict(t) for t in tasks]


@app.get("/task/status")
def task_status(id: str = Query(..., description="Task ID")):
    try:
        status = queue.status(id)
    except KeyError:
        return _error_response(f"Task {id!r} not found", status_code=404)
    return PlainTextResponse(
        _envelope_response("TASK:result", "v1", {
            "id":     status.task_id,
            "status": status.status,
            "title":  status.title,
            "agent":  status.agent,
            "notes":  status.notes,
            "pr":     status.pr_url,
            "poll":   f"/task/status?id={status.task_id}",
        })
    )


@app.get("/agent")
def agent(msg: str = Query(..., description="URL-encoded agent protocol v1 envelope")):
    raw = unquote_plus(msg)

    try:
        envelope = parser.parse(raw)
    except ValueError as exc:
        return _error_response(str(exc))

    if envelope.verb == "AGENT:ping":
        tasks  = queue.board()
        active = sum(1 for t in tasks if t.status == "active")
        queued = sum(1 for t in tasks if t.status == "queued")
        return PlainTextResponse(
            _envelope_response("AGENT:pong", "v1", {
                "gateway":      "agent-gateway/1.0",
                "queue_depth":  str(queued),
                "agents_active": str(active),
            })
        )

    if envelope.verb == "TASK:submit":
        tags = [t.strip() for t in envelope.fields.get("tags", "").split(",") if t.strip()]
        ref  = queue.submit(
            title       = envelope.fields["title"],
            description = envelope.fields.get("desc", ""),
            priority    = envelope.fields.get("pri", "normal"),
            tags        = tags or None,
        )
        return PlainTextResponse(
            _envelope_response("TASK:ack", "v1", {
                "id":     ref.task_id,
                "status": ref.status,
                "poll":   ref.poll,
            })
        )

    if envelope.verb == "TASK:status":
        task_id = envelope.fields["id"]
        try:
            status = queue.status(task_id)
        except KeyError:
            return _error_response(f"Task {task_id!r} not found", status_code=404)
        return PlainTextResponse(
            _envelope_response("TASK:result", "v1", {
                "id":     status.task_id,
                "status": status.status,
                "title":  status.title,
                "agent":  status.agent,
                "notes":  status.notes,
                "pr":     status.pr_url,
                "poll":   f"/task/status?id={status.task_id}",
            })
        )

    return _error_response(f"Verb {envelope.verb!r} not handled by this gateway")
