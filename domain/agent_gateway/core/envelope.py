from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

SUPPORTED_VERBS = frozenset({
    "TASK:submit",
    "TASK:status",
    "TASK:result",
    "TASK:ack",
    "TASK:error",
    "AGENT:ping",
    "AGENT:pong",
})

SUPPORTED_VERSIONS = frozenset({"v1"})


@dataclass
class Envelope:
    """Canonical internal representation of a parsed agent protocol envelope."""

    verb:    str
    version: str
    fields:  dict[str, str]         = field(default_factory=dict)
    body:    Optional[str]          = None

    SUPPORTED_VERBS:    frozenset = field(default=SUPPORTED_VERBS,    init=False, repr=False, compare=False)
    SUPPORTED_VERSIONS: frozenset = field(default=SUPPORTED_VERSIONS, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.verb not in SUPPORTED_VERBS:
            raise ValueError(f"Unsupported verb: {self.verb!r}")
        if self.version not in SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version: {self.version!r}")
        if self.verb == "TASK:submit":
            if not self.fields.get("title"):
                raise ValueError("TASK:submit requires 'title' field")
            if not self.fields.get("desc"):
                raise ValueError("TASK:submit requires 'desc' field")
        if self.verb == "TASK:status":
            if not self.fields.get("id"):
                raise ValueError("TASK:status requires 'id' field")
