from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from domain.agent_gateway.core.ports.i_task_queue import ITaskQueue, TaskRef, TaskStatus


class AgentTasksQueue(ITaskQueue):
    """
    Outbound port implementation: bridges agent-gateway to an agent-tasks
    task queue on the local filesystem.

    Reads/writes the same backlog/, active/, done/ directories that
    agent-tasks/task_cli.py uses. No subprocess — direct file I/O.
    """

    STALE_HOURS = 2

    def __init__(self, tasks_dir: Path) -> None:
        self._backlog = tasks_dir / "backlog"
        self._active  = tasks_dir / "active"
        self._done    = tasks_dir / "done"
        for d in (self._backlog, self._active, self._done):
            d.mkdir(parents=True, exist_ok=True)

    # ── ITaskQueue ────────────────────────────────────────────────────────────

    def submit(
        self,
        title:       str,
        description: str,
        priority:    str = "normal",
        tags:        list[str] | None = None,
    ) -> TaskRef:
        task_id = self._next_id()
        slug    = self._slug(title)
        path    = self._backlog / f"{task_id}_{slug}.json"
        task    = {
            "id":          task_id,
            "title":       title,
            "description": description,
            "priority":    priority,
            "tags":        tags or [],
            "created_at":  self._now(),
            "created_by":  "agent-gateway",
        }
        path.write_text(json.dumps(task, indent=2) + "\n")
        return TaskRef(task_id=task_id, status="queued", poll=f"/task/status?id={task_id}")

    def status(self, task_id: str) -> TaskStatus:
        # done takes priority
        done_path = self._done / f"{task_id}.json"
        if done_path.exists():
            rec = json.loads(done_path.read_text())
            bl  = self._backlog_data(task_id)
            return TaskStatus(
                task_id=task_id,
                status="done",
                title=bl.get("title", "") if bl else "",
                agent=rec.get("agent_id"),
                notes=rec.get("notes"),
                pr_url=rec.get("pr_url") or None,
            )

        # active?
        claim = self._active_claim(task_id)
        if claim:
            bl = self._backlog_data(task_id)
            return TaskStatus(
                task_id=task_id,
                status="active",
                title=bl.get("title", "") if bl else "",
                agent=claim.get("agent_id"),
                notes=claim.get("notes") or None,
            )

        # backlog?
        bl = self._backlog_data(task_id)
        if bl:
            return TaskStatus(task_id=task_id, status="queued", title=bl.get("title", ""))

        raise KeyError(f"Task {task_id!r} not found")

    def board(self) -> list[TaskStatus]:
        results: dict[str, TaskStatus] = {}

        for f in sorted(self._backlog.glob("*.json")):
            try:
                bl = json.loads(f.read_text())
                tid = bl["id"]
                results[tid] = TaskStatus(task_id=tid, status="queued", title=bl.get("title", ""))
            except Exception:
                pass

        for f in self._active.glob("*.json"):
            if f.name == ".gitkeep":
                continue
            try:
                cl  = json.loads(f.read_text())
                tid = cl["task_id"]
                bl  = self._backlog_data(tid)
                results[tid] = TaskStatus(
                    task_id=tid,
                    status="active",
                    title=bl.get("title", "") if bl else "",
                    agent=cl.get("agent_id"),
                    notes=cl.get("notes") or None,
                )
            except Exception:
                pass

        for f in sorted(self._done.glob("*.json")):
            try:
                rec = json.loads(f.read_text())
                tid = rec["task_id"]
                bl  = self._backlog_data(tid)
                results[tid] = TaskStatus(
                    task_id=tid,
                    status="done",
                    title=bl.get("title", "") if bl else "",
                    agent=rec.get("agent_id"),
                    pr_url=rec.get("pr_url") or None,
                )
            except Exception:
                pass

        return sorted(results.values(), key=lambda t: t.task_id)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _next_id(self) -> str:
        existing = [f.stem.split("_")[0] for f in self._backlog.glob("*.json")]
        nums = [int(x) for x in existing if x.isdigit()]
        return str(max(nums, default=0) + 1).zfill(3)

    def _backlog_data(self, task_id: str) -> Optional[dict]:
        matches = list(self._backlog.glob(f"{task_id}_*.json"))
        if not matches:
            return None
        try:
            return json.loads(matches[0].read_text())
        except Exception:
            return None

    def _active_claim(self, task_id: str) -> Optional[dict]:
        for f in self._active.glob(f"*_{task_id}.json"):
            try:
                return json.loads(f.read_text())
            except Exception:
                pass
        return None

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", text.lower())[:40].strip("_")
