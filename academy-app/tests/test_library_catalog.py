import sys
import json
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server  # noqa: E402


class LibraryCatalogValidationTests(unittest.TestCase):
    def setUp(self):
        self.original_paths = server.knowledge_paths
        server.knowledge_paths = lambda: ["02 PRODUCTS/valid.md"]

    def tearDown(self):
        server.knowledge_paths = self.original_paths

    def test_keeps_a_completely_blank_tile_as_a_draft(self):
        catalog = server.validate_library_catalog({
            "hidden": [],
            "overrides": {},
            "custom": [{
                "id": "library-custom-draft",
                "title": "",
                "eyebrow": "",
                "lead": "",
                "content": "",
                "sources": [],
                "roles": ["leader"],
            }],
            "archived": [],
        })

        self.assertEqual(catalog["custom"][0]["id"], "library-custom-draft")
        self.assertEqual(catalog["custom"][0]["sources"], [])
        self.assertEqual(catalog["custom"][0]["content"], "")

    def test_keeps_a_deleted_custom_tile_in_archive_for_restore(self):
        catalog = server.validate_library_catalog({
            "hidden": [],
            "overrides": {},
            "custom": [],
            "archived": [{
                "id": "library-custom-restore",
                "title": "Вернуть плитку",
                "eyebrow": "Регламент",
                "lead": "Данные остаются в корзине до восстановления.",
                "content": "<p>Собственный текст плитки.</p>",
                "sources": ["02 PRODUCTS/valid.md"],
                "roles": ["manager", "expert", "leader"],
            }],
        })

        self.assertEqual(catalog["archived"][0]["id"], "library-custom-restore")
        self.assertEqual(catalog["archived"][0]["sources"], ["02 PRODUCTS/valid.md"])
        self.assertEqual(catalog["archived"][0]["content"], "<p>Собственный текст плитки.</p>")


class CourseSourceContractTests(unittest.TestCase):
    def test_new_working_materials_are_readable_by_their_assigned_roles(self):
        manifest = json.loads(server.COURSE_ACCESS_FILE.read_text(encoding="utf-8"))

        expected = {
            "gpn": {
                "02 PRODUCTS/Полный чек-лист — Госпромнадзор АХУ, резервуары и сварка.md",
                "02 PRODUCTS/КП — Госпромнадзор: газ и резервуары.md",
            },
            "iso-suot": {"02 PRODUCTS/Шпаргалка — ISO и СУОТ: решение для тендеров.md"},
            "sales": {
                "03 SALES/Подсказка — вести звонок к конкретному действию.md",
                "03 SALES/Скрипт — получение рекомендаций.md",
            },
            "contacts": {"09 SOP/Важные контакты — органы, экспертиза и обучение.md"},
        }

        for course_id, paths in expected.items():
            self.assertTrue(paths.issubset(set(manifest[course_id]["p"])))
            for path in paths:
                self.assertTrue((server.KNOWLEDGE_ROOT / path).is_file(), path)

        self.assertEqual(set(manifest["contacts"]["r"]), {"trainee", "manager", "expert", "leader"})


if __name__ == "__main__":
    unittest.main()
