import tempfile
import unittest
from pathlib import Path

from scripts.install_agent_command import directory_is_case_insensitive, install_launchers


class InstallAgentCommandTests(unittest.TestCase):
    def test_install_launchers_creates_jw_and_uppercase_jw(self):
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            agent_path = Path(tmp) / "agent.py"
            agent_path.write_text("print('agent')\n", encoding="utf-8")

            created = install_launchers(bin_dir=bin_dir, agent_path=agent_path)

            expected = {"jw"} if directory_is_case_insensitive(bin_dir) else {"JW", "jw"}
            self.assertEqual({p.name for p in created}, expected)
            for launcher in created:
                text = launcher.read_text(encoding="utf-8")
                self.assertIn(str(agent_path), text)
                self.assertTrue(launcher.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
