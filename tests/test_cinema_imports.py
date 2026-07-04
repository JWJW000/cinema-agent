import unittest


class CinemaImportTests(unittest.TestCase):
    def test_cinema_module_imports_without_httpx_installed(self):
        import scripts.cinema as cinema

        self.assertTrue(hasattr(cinema, "cmd_search"))


if __name__ == "__main__":
    unittest.main()
