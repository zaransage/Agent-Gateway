import unittest
from domain.agent_gateway.core.envelope import Envelope


class TestEnvelopeValidation(unittest.TestCase):

    def test_valid_task_submit(self):
        e = Envelope(verb="TASK:submit", version="v1", fields={"title": "T", "desc": "D"})
        self.assertEqual(e.verb, "TASK:submit")
        self.assertIsNone(e.body)

    def test_task_submit_missing_title_raises(self):
        with self.assertRaises(ValueError):
            Envelope(verb="TASK:submit", version="v1", fields={"desc": "D"})

    def test_task_submit_missing_desc_raises(self):
        with self.assertRaises(ValueError):
            Envelope(verb="TASK:submit", version="v1", fields={"title": "T"})

    def test_task_status_missing_id_raises(self):
        with self.assertRaises(ValueError):
            Envelope(verb="TASK:status", version="v1", fields={})

    def test_unsupported_verb_raises(self):
        with self.assertRaises(ValueError):
            Envelope(verb="TASK:unknown", version="v1", fields={})

    def test_unsupported_version_raises(self):
        with self.assertRaises(ValueError):
            Envelope(verb="AGENT:ping", version="v99", fields={})

    def test_body_preserved(self):
        e = Envelope(verb="TASK:result", version="v1", fields={"id": "012", "status": "done"}, body="All done.")
        self.assertEqual(e.body, "All done.")


if __name__ == "__main__":
    unittest.main()
