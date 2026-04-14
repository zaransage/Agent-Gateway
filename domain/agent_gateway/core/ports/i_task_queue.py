import abc
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskRef:
    """Minimal handle returned after a task is submitted."""
    task_id: str
    status:  str   # queued | active | done | failed
    poll:    str   # suggested poll path


@dataclass
class TaskStatus:
    """Full status record for a task."""
    task_id: str
    status:  str                  # queued | active | done | failed
    title:   str
    agent:   Optional[str]        = None
    notes:   Optional[str]        = None
    pr_url:  Optional[str]        = None


class ITaskQueue(abc.ABC):

    @abc.abstractmethod
    def submit(
        self,
        title:      str,
        description: str,
        priority:   str = "normal",
        tags:       list[str] | None = None,
    ) -> TaskRef:
        """Add a task to the backlog. Returns a TaskRef with the assigned ID."""

    @abc.abstractmethod
    def status(self, task_id: str) -> TaskStatus:
        """Return current status of a task. Raises KeyError if not found."""

    @abc.abstractmethod
    def board(self) -> list[TaskStatus]:
        """Return status for all known tasks across backlog, active, and done."""
