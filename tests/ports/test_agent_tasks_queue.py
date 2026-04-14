import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from domain.agent_gateway.core.ports.agent_tasks_queue import AgentTasksQueue


class TestAgentTasksQueue(unittest.TestCase):

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.queue = AgentTasksQueue(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    # --- submit ---

    def test_submit_creates_backlog_file(self):
        ref = self.queue.submit("My Task", "Do the thing")
        backlog_files = list((Path(self._tmp.name) / "backlog").glob("*.json"))
        self.assertEqual(len(backlog_files), 1)
        self.assertEqual(ref.status, "queued")
        self.assertIn(ref.task_id, ref.poll)

    def test_submit_increments_id(self):
        ref1 = self.queue.submit("Task One",   "desc")
        ref2 = self.queue.submit("Task Two",   "desc")
        ref3 = self.queue.submit("Task Three", "desc")
        self.assertEqual(ref1.task_id, "001")
        self.assertEqual(ref2.task_id, "002")
        self.assertEqual(ref3.task_id, "003")

    def test_submit_stores_tags_and_priority(self):
        ref = self.queue.submit("T", "D", priority="high", tags=["code", "backend"])
        bl  = json.loads((Path(self._tmp.name) / "backlog" / f"{ref.task_id}_t.json").read_text())
        self.assertEqual(bl["priority"], "high")
        self.assertEqual(bl["tags"], ["code", "backend"])

    # --- status: queued ---

    def test_status_queued(self):
        ref    = self.queue.submit("My Task", "desc")
        status = self.queue.status(ref.task_id)
        self.assertEqual(status.status,  "queued")
        self.assertEqual(status.title,   "My Task")
        self.assertIsNone(status.agent)

    # --- status: active ---

    def test_status_active(self):
        ref = self.queue.submit("My Task", "desc")
        # Simulate a claim file
        claim = {
            "task_id":        ref.task_id,
            "agent_id":       "claude-test",
            "claimed_at":     "2026-01-01T00:00:00+00:00",
            "last_heartbeat": "2026-01-01T00:00:00+00:00",
            "notes":          "in progress",
        }
        claim_path = Path(self._tmp.name) / "active" / f"claude-test_{ref.task_id}.json"
        claim_path.write_text(json.dumps(claim))

        status = self.queue.status(ref.task_id)
        self.assertEqual(status.status, "active")
        self.assertEqual(status.agent,  "claude-test")
        self.assertEqual(status.notes,  "in progress")

    # --- status: done ---

    def test_status_done(self):
        ref = self.queue.submit("My Task", "desc")
        done = {
            "task_id":      ref.task_id,
            "agent_id":     "claude-test",
            "pr_url":       "https://github.com/example/pull/1",
            "completed_at": "2026-01-01T01:00:00+00:00",
            "notes":        "shipped",
        }
        (Path(self._tmp.name) / "done" / f"{ref.task_id}.json").write_text(json.dumps(done))

        status = self.queue.status(ref.task_id)
        self.assertEqual(status.status, "done")
        self.assertEqual(status.pr_url, "https://github.com/example/pull/1")

    # --- status: not found ---

    def test_status_unknown_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.queue.status("999")

    # --- board ---

    def test_board_returns_all_tasks(self):
        r1 = self.queue.submit("Task A", "desc")
        r2 = self.queue.submit("Task B", "desc")
        board = self.queue.board()
        ids = [t.task_id for t in board]
        self.assertIn(r1.task_id, ids)
        self.assertIn(r2.task_id, ids)

    def test_board_done_overrides_queued(self):
        ref  = self.queue.submit("My Task", "desc")
        done = {"task_id": ref.task_id, "agent_id": "x", "pr_url": "", "completed_at": "", "notes": ""}
        (Path(self._tmp.name) / "done" / f"{ref.task_id}.json").write_text(json.dumps(done))
        board  = self.queue.board()
        record = next(t for t in board if t.task_id == ref.task_id)
        self.assertEqual(record.status, "done")


if __name__ == "__main__":
    unittest.main()
