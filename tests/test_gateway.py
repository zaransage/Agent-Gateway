import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient


class TestGatewayQueryTransport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._previous_tasks_dir = os.environ.get("TASKS_DIR")
        os.environ["TASKS_DIR"] = cls._tmp.name

        import gateway

        cls._gateway = gateway
        cls._client = TestClient(gateway.app)

    @classmethod
    def tearDownClass(cls):
        if cls._previous_tasks_dir is None:
            os.environ.pop("TASKS_DIR", None)
        else:
            os.environ["TASKS_DIR"] = cls._previous_tasks_dir
        cls._tmp.cleanup()

    def test_url_encoded_literal_plus_survives_query_decoding(self):
        envelope = "AGENT/TASK:submit v1\ntitle: C++ parser\ndesc: Preserve C++"
        response = self._client.get("/agent?msg=" + quote(envelope, safe=""))

        self.assertEqual(response.status_code, 200)
        backlog_files = list((Path(self._tmp.name) / "backlog").glob("*.json"))
        self.assertEqual(len(backlog_files), 1)
        task = json.loads(backlog_files[0].read_text())
        self.assertEqual(task["title"], "C++ parser")
        self.assertEqual(task["description"], "Preserve C++")


if __name__ == "__main__":
    unittest.main()
