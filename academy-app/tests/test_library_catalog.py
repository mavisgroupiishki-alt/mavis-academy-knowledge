import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_keeps_only_safe_external_materials_on_tiles(self):
        catalog = server.validate_library_catalog({
            "hidden": [],
            "overrides": {
                "spk": {
                    "title": "СПК",
                    "eyebrow": "Строительство",
                    "lead": "Полный маршрут",
                    "attachments": [
                        {"title": "Рабочая таблица", "url": "https://docs.google.com/spreadsheets/d/example", "kind": "spreadsheet"},
                        {"title": "Небезопасно", "url": "javascript:alert(1)", "kind": "video"},
                    ],
                },
            },
            "custom": [{
                "id": "library-custom-materials",
                "title": "Материалы",
                "eyebrow": "Продажи",
                "lead": "Ссылки для работы",
                "content": "",
                "sources": [],
                "attachments": [{"title": "Видео", "url": "https://example.com/video", "kind": "video"}],
                "roles": ["manager"],
            }],
            "archived": [],
        })

        self.assertEqual(catalog["overrides"]["spk"]["attachments"], [{"title": "Рабочая таблица", "url": "https://docs.google.com/spreadsheets/d/example", "kind": "spreadsheet"}])
        self.assertEqual(catalog["custom"][0]["attachments"], [{"title": "Видео", "url": "https://example.com/video", "kind": "video"}])


class CourseSourceContractTests(unittest.TestCase):
    def test_staff_roles_share_library_access_and_test_hub(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const STAFF_ROLES = ['manager','expert','leader'];", source)
        self.assertIn("Тесты по базе", source)
        self.assertIn("function testHub()", source)
        for role in ("manager", "expert", "leader"):
            self.assertTrue(server.document_access_for(role, "any-course", "02 PRODUCTS/valid.md"))

    def test_reader_controls_expose_the_open_section_and_selected_material(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn('aria-pressed="${!state.referenceView}"', source)
        self.assertIn('aria-current="${index===selectedIndex?\'page\':\'false\'}"', source)
        self.assertIn("state.readerNotice", source)

    def test_trainee_spk_is_a_standalone_curriculum_lesson(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("id:'tr-spk'", source)
        self.assertIn("СПК: свидетельство", source)
        self.assertIn("const TRAINEE_COURSE_IDS=new Set", source)
        self.assertNotIn("const TRAINEE_SOURCE_COURSES", source)

    def test_trainee_keeps_the_four_day_curriculum_instead_of_staff_reference_tabs(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const TRAINEE_DAYS = [", source)
        self.assertIn("sources:[],sourceCourse:'',fallbackContent:''", source)
        self.assertIn("const courseLessonCount=course=>", source)

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
            "tool-rental": {"09 SOP/Учебный маршрут — аренда инструментов.md"},
            "product-cert": {
                "02 PRODUCTS/Чек-лист — СГР и сертификация красок.md",
                "02 PRODUCTS/Чек-лист — техническое свидетельство и декларация.md",
            },
            "bitrix": {"06 BITRIX24/Регламент — работа с делами и воронкой производства.md"},
        }

        for course_id, paths in expected.items():
            self.assertTrue(paths.issubset(set(manifest[course_id]["p"])))
            for path in paths:
                self.assertTrue((server.KNOWLEDGE_ROOT / path).is_file(), path)

        self.assertEqual(set(manifest["contacts"]["r"]), {"trainee", "manager", "expert", "leader"})

    def test_tool_rental_route_keeps_the_source_screenshots(self):
        route = server.KNOWLEDGE_ROOT / "09 SOP/Учебный маршрут — аренда инструментов.md"
        source = route.read_text(encoding="utf-8")

        for number in range(1, 7):
            image = f"media/tool-rental-step-{number:02}.png"
            self.assertIn(image, source)
            self.assertTrue((server.ROOT / image).is_file(), image)


class PersistentStateTransportTests(unittest.TestCase):
    def test_state_request_uses_authenticated_rpc_and_never_exposes_access_token_in_url(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"value":{"custom":[]}}'

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["timeout"] = timeout
            return Response()

        with patch.dict(server.os.environ, {
            "ACADEMY_RESULTS_URL": "https://example.supabase.co",
            "ACADEMY_RESULTS_SERVICE_KEY": "public-key",
            "ACADEMY_RESULTS_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            payload = server.persistent_state_request("GET", "academy:library-catalog")

        self.assertEqual(payload, {"value": {"custom": []}})
        self.assertEqual(captured["url"], "https://example.supabase.co/rest/v1/rpc/academy_get_dashboard_state")
        self.assertNotIn("server-only-token", captured["url"])

    def test_cloudflare_state_request_uses_header_token_and_does_not_expose_it_in_url(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"value":{"custom":[]}}'

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            return Response()

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            payload = server.persistent_state_request("POST", "academy:library-catalog", {"custom": []})

        self.assertEqual(payload, {"value": {"custom": []}})
        self.assertEqual(captured["url"], "https://mavis-academy-state.example.workers.dev/state?key=academy%3Alibrary-catalog")
        self.assertEqual(captured["method"], "PUT")
        self.assertEqual(captured["headers"]["X-academy-state-token"], "server-only-token")
        self.assertEqual(captured["headers"]["User-agent"], "Mavis-Academy-State/1.0")
        self.assertNotIn("server-only-token", captured["url"])


if __name__ == "__main__":
    unittest.main()
