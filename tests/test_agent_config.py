import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.agent_config import (
    AgentModelConfig,
    load_agent_model_config,
    safe_config_summary,
    update_quark_cookie,
)


class AgentConfigTests(unittest.TestCase):
    def test_load_agent_model_config_prefers_environment_over_file(self):
        config = {
            "agent": {
                "provider": "openai_compatible",
                "base_url": "https://file.example/v1",
                "model": "file-model",
                "api_key_env": "CUSTOM_KEY",
                "history_limit": 7,
            }
        }

        with patch.dict(
            os.environ,
            {
                "CUSTOM_KEY": "from-custom",
                "OPENAI_BASE_URL": "https://env.example/v1",
                "OPENAI_MODEL": "env-model",
            },
            clear=True,
        ):
            model_config = load_agent_model_config(config)

        self.assertEqual(
            model_config,
            AgentModelConfig(
                provider="openai_compatible",
                base_url="https://env.example/v1",
                model="env-model",
                api_key="from-custom",
                history_limit=7,
                allow_shell="confirm",
            ),
        )

    def test_load_agent_model_config_can_read_local_api_key_when_env_missing(self):
        config = {
            "agent": {
                "provider": "openai_compatible",
                "base_url": "https://newapi.example",
                "model": "gemini-3.1-flash-lite",
                "api_key": "local-secret",
            }
        }

        with patch.dict(os.environ, {}, clear=True):
            model_config = load_agent_model_config(config)

        self.assertEqual(model_config.api_key, "local-secret")
        self.assertEqual(model_config.base_url, "https://newapi.example")
        self.assertEqual(model_config.model, "gemini-3.1-flash-lite")

    def test_safe_config_summary_masks_secrets(self):
        summary = safe_config_summary(
            {
                "quark": {"cookie": "abc123456789"},
                "agent": {"model": "demo-model", "base_url": "https://api.example/v1"},
            }
        )

        self.assertTrue(summary["quark"]["configured"])
        self.assertEqual(summary["quark"]["cookie_length"], 12)
        self.assertNotIn("abc123456789", json.dumps(summary))
        self.assertEqual(summary["agent"]["model"], "demo-model")

    def test_update_quark_cookie_preserves_existing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(
                json.dumps({"save_folder": "夸克影视", "quark": {"cookie": "old"}}),
                encoding="utf-8",
            )

            update_quark_cookie(config_path, "new-cookie-value")

            data = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(data["save_folder"], "夸克影视")
            self.assertEqual(data["quark"]["cookie"], "new-cookie-value")


if __name__ == "__main__":
    unittest.main()
