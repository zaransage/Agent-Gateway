import json
import unittest
from pathlib import Path

from domain.agent_gateway.core.adaptors.envelope_parser import EnvelopeParser

FIXTURES_RAW      = Path(__file__).parents[2] / "fixtures" / "raw"      / "agent_protocol" / "v1"
FIXTURES_EXPECTED = Path(__file__).parents[2] / "fixtures" / "expected" / "agent_protocol" / "v1"


class TestEnvelopeParserFixtures(unittest.TestCase):
    """Assert raw fixture assumptions and canonical Envelope field values."""

    def setUp(self):
        self.parser = EnvelopeParser()

    def _load_expected(self, name: str) -> dict:
        with open(FIXTURES_EXPECTED / f"{name}.json") as f:
            return json.load(f)

    def _load_raw(self, name: str) -> str:
        return (FIXTURES_RAW / f"{name}.txt").read_text()

    # --- task_submit full ---

    def test_task_submit_raw_has_required_fields(self):
        raw = self._load_raw("task_submit.0.0.1")
        self.assertIn("AGENT/TASK:submit v1", raw)
        self.assertIn("title:", raw)
        self.assertIn("desc:", raw)

    def test_task_submit_parses_to_canonical(self):
        raw      = self._load_raw("task_submit.0.0.1")
        expected = self._load_expected("task_submit.0.0.1")
        envelope = self.parser.parse(raw)

        self.assertEqual(envelope.verb,    expected["verb"])
        self.assertEqual(envelope.version, expected["version"])
        self.assertEqual(envelope.fields,  expected["fields"])
        self.assertIsNone(envelope.body)

    # --- task_submit minimal ---

    def test_task_submit_minimal_parses(self):
        raw      = self._load_raw("task_submit_minimal.0.0.1")
        expected = self._load_expected("task_submit_minimal.0.0.1")
        envelope = self.parser.parse(raw)

        self.assertEqual(envelope.verb,    expected["verb"])
        self.assertEqual(envelope.fields,  expected["fields"])

    # --- ping ---

    def test_ping_parses_to_canonical(self):
        raw      = self._load_raw("ping.0.0.1")
        expected = self._load_expected("ping.0.0.1")
        envelope = self.parser.parse(raw)

        self.assertEqual(envelope.verb,    expected["verb"])
        self.assertEqual(envelope.version, expected["version"])
        self.assertEqual(envelope.fields,  expected["fields"])

    # --- body parsing ---

    def test_body_extracted_after_separator(self):
        raw = "AGENT/TASK:result v1\nid: 012\nstatus: done\n---\nAll done.\nSecond line."
        envelope = self.parser.parse(raw)
        self.assertEqual(envelope.body, "All done.\nSecond line.")

    def test_no_body_when_no_separator(self):
        raw = "AGENT/AGENT:ping v1\nfrom: test"
        envelope = self.parser.parse(raw)
        self.assertIsNone(envelope.body)

    # --- error cases ---

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            self.parser.parse("")

    def test_missing_agent_prefix_raises(self):
        with self.assertRaises(ValueError):
            self.parser.parse("TASK:submit v1\ntitle: T\ndesc: D")

    def test_unknown_verb_raises(self):
        with self.assertRaises(ValueError):
            self.parser.parse("AGENT/TASK:banana v1\ntitle: T\ndesc: D")


if __name__ == "__main__":
    unittest.main()
