import unittest
import io
from urllib.error import HTTPError
from unittest.mock import Mock, patch

from scripts.agent_config import AgentModelConfig
from scripts.llm import OpenAICompatibleClient


class LLMTests(unittest.TestCase):
    def test_openai_client_posts_chat_completion_request(self):
        config = AgentModelConfig(
            provider="openai_compatible",
            base_url="https://api.example/v1/",
            model="demo-model",
            api_key="secret",
        )
        response = Mock()
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "hello",
                        "tool_calls": [],
                    }
                }
            ]
        }
        response.raise_for_status.return_value = None

        with patch("scripts.llm.httpx.Client") as client_cls:
            client_cls.return_value.post.return_value = response
            client = OpenAICompatibleClient(config)
            result = client.chat([{"role": "user", "content": "hi"}], tools=[])

        client_cls.return_value.post.assert_called_once()
        url = client_cls.return_value.post.call_args.args[0]
        payload = client_cls.return_value.post.call_args.kwargs["json"]
        self.assertEqual(url, "https://api.example/v1/chat/completions")
        self.assertEqual(payload["model"], "demo-model")
        self.assertIn("User-Agent", client.headers)
        self.assertEqual(result["content"], "hello")

    def test_openai_client_reports_http_status_without_exposing_key(self):
        config = AgentModelConfig(
            provider="openai_compatible",
            base_url="https://api.example/v1/",
            model="demo-model",
            api_key="secret-key",
        )

        with patch("scripts.llm.httpx.Client", None), patch("scripts.llm.urllib.request.urlopen") as urlopen:
            urlopen.side_effect = HTTPError(
                url="https://api.example/v1/chat/completions",
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=io.BytesIO(b""),
            )
            client = OpenAICompatibleClient(config)

            with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
                client.chat([{"role": "user", "content": "hi"}], tools=[])

    def test_openai_client_streams_sse_content_chunks(self):
        config = AgentModelConfig(
            provider="openai_compatible",
            base_url="https://api.example/v1/",
            model="demo-model",
            api_key="secret",
        )

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def __iter__(self):
                return iter(
                    [
                        b'data: {"choices":[{"delta":{"content":"he"}}]}\n',
                        b'data: {"choices":[{"delta":{"content":"llo"}}]}\n',
                        b"data: [DONE]\n",
                    ]
                )

        with patch("scripts.llm.httpx.Client", None), patch("scripts.llm.urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeResponse()
            client = OpenAICompatibleClient(config)
            events = list(client.stream_chat([{"role": "user", "content": "hi"}], tools=[]))

        payload = json_from_request(urlopen.call_args.args[0])
        self.assertTrue(payload["stream"])
        self.assertEqual(events[0], {"type": "content", "content": "he"})
        self.assertEqual(events[1], {"type": "content", "content": "llo"})
        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(events[-1]["message"]["content"], "hello")



if __name__ == "__main__":
    unittest.main()


def json_from_request(request):
    import json

    return json.loads(request.data.decode("utf-8"))
