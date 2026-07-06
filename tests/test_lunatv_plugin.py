import unittest

from scripts.plugins.lunatv import Plugin


class LunaTVPluginTests(unittest.TestCase):
    def test_search_queries_configured_maccms_sources_and_maps_results(self):
        calls = []

        def fake_request_json(url):
            calls.append(url)
            return {
                "code": 1,
                "list": [
                    {
                        "vod_name": "苹果",
                        "vod_year": "2007",
                        "vod_actor": "范冰冰,梁家辉",
                        "vod_remarks": "HD国语",
                        "vod_play_url": "正片$https://example.test/apple.m3u8",
                    }
                ],
            }

        plugin = Plugin(
            config={
                "max_sources": 1,
                "sites": {
                    "lzi": {
                        "name": "量子资源",
                        "api": "https://cj.example.test/api.php/provide/vod",
                    }
                },
            }
        )
        plugin.request_json = fake_request_json

        results = plugin.search("范冰冰 苹果")

        self.assertEqual(len(results), 1)
        self.assertIn("ac=detail", calls[0])
        self.assertIn("wd=", calls[0])
        self.assertEqual(results[0].source, "online")
        self.assertEqual(results[0].site, "lunatv")
        self.assertEqual(results[0].title, "苹果 (2007) - 量子资源 - HD国语")
        self.assertEqual(results[0].url, "https://example.test/apple.m3u8")
        self.assertEqual(results[0].extra["actor"], "范冰冰,梁家辉")

    def test_extract_link_returns_none_because_lunatv_is_not_quark_storage(self):
        plugin = Plugin(config={"sites": {}})

        self.assertIsNone(plugin.extract_link(object()))


if __name__ == "__main__":
    unittest.main()
