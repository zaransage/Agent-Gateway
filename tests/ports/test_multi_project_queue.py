import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from domain.agent_gateway.core.ports.multi_project_queue import MultiProjectQueue


class TestMultiProjectQueue(unittest.TestCase):

    def setUp(self):
        self._tmp_a = TemporaryDirectory()
        self._tmp_b = TemporaryDirectory()
        self.queue = MultiProjectQueue({
            "alpha": Path(self._tmp_a.name),
            "beta":  Path(self._tmp_b.name),
        }, default_project="alpha")

    def tearDown(self):
        self._tmp_a.cleanup()
        self._tmp_b.cleanup()

    def test_submit_routes_to_default_project(self):
        ref = self.queue.submit("Task A", "desc")
        self.assertIn("alpha", ref.poll)

    def test_submit_routes_to_named_project(self):
        ref = self.queue.submit("Task B", "desc", project="beta")
        self.assertIn("beta", ref.poll)

    def test_submit_unknown_project_raises(self):
        with self.assertRaises(KeyError):
            self.queue.submit("Task C", "desc", project="nonexistent")

    def test_status_finds_across_projects(self):
        ref_a = self.queue.submit("Task Alpha", "desc", project="alpha")
        ref_b = self.queue.submit("Task Beta",  "desc", project="beta")
        # IDs are per-project sequential — use project hint to avoid ambiguity
        s_a = self.queue.status(ref_a.task_id, project="alpha")
        s_b = self.queue.status(ref_b.task_id, project="beta")
        self.assertEqual(s_a.project, "alpha")
        self.assertEqual(s_b.project, "beta")

    def test_status_with_explicit_project(self):
        ref = self.queue.submit("Task Alpha", "desc", project="alpha")
        s   = self.queue.status(ref.task_id, project="alpha")
        self.assertEqual(s.project, "alpha")

    def test_status_not_found_raises(self):
        with self.assertRaises(KeyError):
            self.queue.status("999")

    def test_board_aggregates_all_projects(self):
        self.queue.submit("Task Alpha", "desc", project="alpha")
        self.queue.submit("Task Beta",  "desc", project="beta")
        board    = self.queue.board()
        projects = {t.project for t in board}
        self.assertIn("alpha", projects)
        self.assertIn("beta",  projects)

    def test_board_sorted_by_project_then_id(self):
        self.queue.submit("Task A2", "desc", project="alpha")
        self.queue.submit("Task A1", "desc", project="alpha")
        self.queue.submit("Task B1", "desc", project="beta")
        board = self.queue.board()
        self.assertEqual(board[0].project, "alpha")
        self.assertEqual(board[-1].project, "beta")

    def test_project_names(self):
        self.assertIn("alpha", self.queue.project_names)
        self.assertIn("beta",  self.queue.project_names)

    def test_empty_projects_raises(self):
        with self.assertRaises(ValueError):
            MultiProjectQueue({})


if __name__ == "__main__":
    unittest.main()
