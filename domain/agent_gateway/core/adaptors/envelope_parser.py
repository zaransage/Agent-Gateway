from __future__ import annotations

from domain.agent_gateway.core.adaptors.i_envelope_parser import IEnvelopeParser
from domain.agent_gateway.core.envelope import Envelope


class EnvelopeParser(IEnvelopeParser):
    """
    Parses a raw agent protocol v1 envelope string into an Envelope dataclass.

    Format:
        AGENT/<verb> <version>
        <key>: <value>
        ...
        ---
        <optional body>
    """

    def parse(self, raw: str) -> Envelope:
        raw = raw.strip()
        if not raw:
            raise ValueError("Empty envelope")

        header_block, _, body_block = raw.partition("\n---\n")
        body = body_block.strip() or None

        lines = [line for line in header_block.splitlines() if line.strip()]
        if not lines:
            raise ValueError("No header lines found")

        first = lines[0].strip()
        verb, version = self._parse_first_line(first)

        fields: dict[str, str] = {}
        for line in lines[1:]:
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()

        return Envelope(verb=verb, version=version, fields=fields, body=body)

    @staticmethod
    def _parse_first_line(line: str) -> tuple[str, str]:
        # Expected: "AGENT/<verb> <version>"
        if not line.startswith("AGENT/"):
            raise ValueError(f"First line must start with 'AGENT/': {line!r}")
        rest = line[len("AGENT/"):]
        parts = rest.split()
        if len(parts) != 2:
            raise ValueError(f"First line must be 'AGENT/<verb> <version>': {line!r}")
        return parts[0], parts[1]
