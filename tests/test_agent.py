import sys
import unittest
from pathlib import Path

from app.agent import get_mcp_server_config, normalize_message_text


class McpServerConfigTests(unittest.TestCase):
    def test_mcp_server_config_uses_current_python_and_absolute_script_path(self):
        config = get_mcp_server_config()

        self.assertEqual(config["command"], sys.executable)
        self.assertEqual(config["transport"], "stdio")
        self.assertEqual(config["cwd"], str(Path(__file__).resolve().parents[1]))

        script_path = Path(config["args"][0])
        self.assertTrue(script_path.is_absolute())
        self.assertTrue(script_path.exists())
        self.assertEqual(script_path.name, "server.py")

    def test_normalize_message_text_handles_tool_calls(self):
        class FakeMessage:
            def __init__(self):
                self.content = ""
                self.tool_calls = [{"name": "create_github_issue"}]

        message = FakeMessage()
        self.assertIn("approval", normalize_message_text(message))


if __name__ == "__main__":
    unittest.main()
