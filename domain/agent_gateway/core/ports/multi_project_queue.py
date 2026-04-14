from __future__ import annotations

from pathlib import Path

from domain.agent_gateway.core.ports.agent_tasks_queue import AgentTasksQueue
from domain.agent_gateway.core.ports.i_task_queue import ITaskQueue, TaskRef, TaskStatus


class MultiProjectQueue(ITaskQueue):
    """
    Outbound port implementation: aggregates multiple AgentTasksQueue instances,
    one per project. Submit routes to a named project; status and board search all.

    projects: dict mapping project name → tasks directory path
              e.g. {"ipo_scanner": Path("/home/.../ipo_scanner/tasks"),
                    "creepos":     Path("/home/.../creepos/tasks")}

    default_project: name used when TASK:submit omits the 'project' field.
    """

    def __init__(self, projects: dict[str, Path], default_project: str | None = None) -> None:
        if not projects:
            raise ValueError("At least one project must be provided")
        self._queues: dict[str, AgentTasksQueue] = {
            name: AgentTasksQueue(path, project=name)
            for name, path in projects.items()
        }
        self._default = default_project or next(iter(projects))

    # ── ITaskQueue ────────────────────────────────────────────────────────────

    def submit(
        self,
        title:        str,
        description:  str,
        priority:     str = "normal",
        tags:         list[str] | None = None,
        project:      str | None = None,
    ) -> TaskRef:
        name = project or self._default
        if name not in self._queues:
            raise KeyError(f"Unknown project: {name!r}. Known: {list(self._queues)}")
        ref = self._queues[name].submit(title, description, priority, tags)
        ref.poll = f"/task/status?id={ref.task_id}&project={name}"
        return ref

    def status(self, task_id: str, project: str | None = None) -> TaskStatus:
        if project:
            if project not in self._queues:
                raise KeyError(f"Unknown project: {project!r}")
            return self._queues[project].status(task_id)
        # search all projects
        for q in self._queues.values():
            try:
                return q.status(task_id)
            except KeyError:
                pass
        raise KeyError(f"Task {task_id!r} not found in any project")

    def board(self) -> list[TaskStatus]:
        results: list[TaskStatus] = []
        for q in self._queues.values():
            results.extend(q.board())
        return sorted(results, key=lambda t: (t.project or "", t.task_id))

    # ── extra ─────────────────────────────────────────────────────────────────

    @property
    def project_names(self) -> list[str]:
        return list(self._queues)
