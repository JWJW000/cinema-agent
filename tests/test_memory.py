import json
import tempfile
import unittest
from pathlib import Path

from scripts.memory import MemoryManager, PersistentPreferenceMemory, SessionMemory


class SessionMemoryTests(unittest.TestCase):
    def test_session_memory_tracks_search_and_save_state(self):
        memory = SessionMemory()
        result = {"title": "苹果 (2007)", "source": "quark"}

        memory.remember_search([result])
        memory.remember_save({"path": "夸克影视/苹果 (2007)"})

        self.assertEqual(memory.last_search_results, [result])
        self.assertEqual(memory.last_saved_result["path"], "夸克影视/苹果 (2007)")

    def test_session_memory_can_forget(self):
        memory = SessionMemory()
        memory.remember_search([{"title": "苹果"}])
        memory.remember_save({"path": "夸克影视/苹果"})

        memory.forget()

        self.assertEqual(memory.last_search_results, [])
        self.assertIsNone(memory.last_saved_result)


class PersistentPreferenceMemoryTests(unittest.TestCase):
    def test_preferences_persist_to_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            memory = PersistentPreferenceMemory(path)

            memory.set("quality", "4K")

            reloaded = PersistentPreferenceMemory(path)
            self.assertEqual(reloaded.get("quality"), "4K")
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["preferences"]["quality"], "4K")

    def test_preferences_summary_masks_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = PersistentPreferenceMemory(Path(tmp) / "missing.json")

            self.assertEqual(memory.summary(), {})


class MemoryManagerTests(unittest.TestCase):
    def test_manager_summarizes_session_and_preferences(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = MemoryManager(preference_path=Path(tmp) / "memory.json")
            manager.session.remember_search([{"title": "苹果"}])
            manager.preferences.set("quality", "4K")

            summary = manager.summary()

            self.assertIn("最近搜索结果：1 个", summary)
            self.assertIn("quality = 4K", summary)


if __name__ == "__main__":
    unittest.main()
