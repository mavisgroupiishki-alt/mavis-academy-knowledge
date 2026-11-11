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

    def test_rejects_a_saved_trainee_program_from_an_old_version(self):
        stale_program = {
            "planVersion": "sales-internship-sheet-2026-11-11.2",
            "courses": [{"id": "tr-d1-company"}],
            "days": [{"courseIds": ["tr-d1-company"]}],
        }

        with patch.object(server, "read_persistent_state", return_value=stale_program):
            self.assertIsNone(server.read_trainee_curriculum())


class CourseSourceContractTests(unittest.TestCase):
    def test_staff_roles_share_library_access_and_test_hub(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const STAFF_ROLES = ['manager','expert','leader'];", source)
        self.assertIn("Тесты по базе", source)
        self.assertIn("function testHub()", source)
        for role in ("manager", "expert", "leader"):
            self.assertTrue(server.document_access_for(role, "any-course", "02 PRODUCTS/valid.md"))

    def test_test_hub_is_limited_to_product_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const PRODUCT_TEST_COURSE_IDS=new Set", source)
        self.assertIn("coursesFor().filter(course=>PRODUCT_TEST_COURSE_IDS.has(course.id))", source)
        product_ids = source.split("const PRODUCT_TEST_COURSE_IDS=new Set(", 1)[1].split(");", 1)[0]
        self.assertIn("'spk'", product_ids)
        self.assertNotIn("'company'", product_ids)
        self.assertNotIn("'contacts'", product_ids)

    def test_contact_directory_does_not_use_the_generic_product_workspace(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function contactsReader(course)", source)
        self.assertIn("if(course.id==='contacts')return contactsReader(course);", source)
        directory = source.split("function contactsReader(course)", 1)[1].split("function reader(){", 1)[0]
        self.assertIn("Телефоны и ответственные по направлениям.", directory)
        self.assertNotIn("workspace-flow", directory)
        self.assertNotIn("Открыть практику", directory)

    def test_staff_reader_uses_role_specific_workspaces(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const activeAudience=()", source)
        self.assertIn("const sourceIndexesForAudience=", source)
        self.assertIn("const ROLE_WORKSPACES=", source)
        self.assertIn("roles:['manager','leader']", source)
        self.assertIn("roles:['expert','leader']", source)
        self.assertIn("!isExpertSource(path)", source)
        self.assertIn("!isManagerSource(path)", source)
        self.assertIn("Понятие", source)
        self.assertIn("Инструменты и документы", source)
        self.assertIn("Ход работы менеджера", source)
        self.assertNotIn('<a href="#workspace-tips">Подсказки</a>', source)
        self.assertIn("const genericFlow=audience==='manager'", source)
        self.assertIn("Фокус менеджера", source)
        self.assertIn("Фокус эксперта", source)
        self.assertIn("window.academyAudience=", source)

    def test_trainee_spk_is_a_standalone_curriculum_lesson(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("id:'tr-spk'", source)
        self.assertIn("СПК: свидетельство", source)
        self.assertIn("const TRAINEE_COURSE_IDS=new Set", source)
        self.assertIn("[...TRAINEE_COURSES,...TRAINEE_FOUNDATION_COURSES].find", source)
        self.assertNotIn("const TRAINEE_SOURCE_COURSES", source)

    def test_trainee_keeps_the_four_day_curriculum_instead_of_staff_reference_tabs(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const TRAINEE_DAYS = [", source)
        self.assertIn("const TRAINEE_PRODUCT_PASSPORTS=", source)
        self.assertIn("sources:passport?[passport]:[]", source)
        self.assertIn("const courseLessonCount=course=>", source)

    def test_day_one_product_tiles_use_full_local_passports(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        passports = (
            "Паспорт продукта — 0101 СПК.md",
            "Паспорт продукта — 0104.07 Аттестация СТ.md",
            "Паспорт продукта — 0104.06 Аттестация ГС.md",
            "Паспорт продукта — 0301 Сертификат ISO 9001.md",
            "Паспорт продукта — 0302 Периодика ISO 9001.md",
            "Паспорт продукта — 0303 Сертификат СУОТ 45001.md",
            "Паспорт продукта — 0304 Периодика СУОТ 45001.md",
        )
        for passport in passports:
            self.assertIn(passport, source)
            self.assertTrue((server.KNOWLEDGE_ROOT / "02 PRODUCTS" / passport).is_file(), passport)
        company_path = "09 SOP/Учебный маршрут — Mavis Group: компания и словарь.md"
        self.assertIn(company_path, source)
        self.assertTrue((server.KNOWLEDGE_ROOT / company_path).is_file())
        self.assertIn("const TRAINEE_DAY_ONE_SOURCE_PATHS=", source)
        self.assertIn("const TRAINEE_DAY_ONE_SOURCE_COURSES=", source)
        self.assertIn("TRAINEE_DAY_ONE_SOURCE_PATHS[course.id]", source)
        self.assertIn("sourceCourse:TRAINEE_DAY_ONE_SOURCE_COURSES[course.id]||''", source)
        self.assertIn("if((access?.role||state.role)==='trainee')return reference?[]:all", source)

    def test_trainee_default_contains_only_sheet_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("let traineeCourses = bindTraineeSources([...TRAINEE_SHEET_COURSES]);", source)
        self.assertIn("courseIds:['tr-d1-company','tr-d1-spk','tr-d1-attestation-st'", source)
        self.assertNotIn("tr-d1-sales-structure","".join(source.split("const TRAINEE_DAYS = [", 1)[1].split("];", 1)[0]))
        self.assertNotIn("let traineeCourses = bindTraineeSources([...TRAINEE_SHEET_COURSES, ...TRAINEE_FOUNDATION_COURSES", source)

    def test_trainee_course_reader_is_defined(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function readerTraineeLegacy(course)", source)
        self.assertIn("academyCompleteSource('${course.id}',0)", source)

    def test_trainee_lessons_embed_materials_and_keep_submitted_work(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const TRAINEE_MATERIALS=", source)
        self.assertNotIn("const TRAINEE_ATTACHMENTS=", source)
        self.assertIn("attachments:[]", source)
        self.assertIn("Вся учебная информация находится в этой плитке", source)
        self.assertIn("Обязательное задание на сегодня", source)
        self.assertIn("Итоговая работа: диагностика и следующий шаг", source)
        self.assertIn("academySubmitTraineeAssignment", source)
        self.assertIn("courseIds:['tr-d2-repeat-products','tr-d2-script-structure','tr-d2-price-templates','tr-d2-own-script']", source)
        self.assertIn("courseIds:['tr-d4-repeat-day1','tr-d4-calls','tr-d4-call-analysis','tr-d4-exam']", source)
        final_exam = source.split("const FINAL_EXAM_BANK = [", 1)[1].split("];", 1)[0]
        self.assertEqual(final_exam.count("{q:'"), 20)

    def test_trainee_day_one_keeps_all_eight_internal_material_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        day_one = source.split("const TRAINEE_DAYS = [", 1)[1].split("},", 1)[0]
        for course_id in (
            "tr-d1-company", "tr-d1-spk", "tr-d1-attestation-st",
            "tr-d1-attestation-gs", "tr-d1-iso9001",
            "tr-d1-iso9001-periodic", "tr-d1-suot45001",
            "tr-d1-suot45001-periodic",
        ):
            self.assertIn(course_id, day_one)
        self.assertIn("TRAINEE_PLAN_VERSION='sales-internship-sheet-2026-11-11.4'", source)

    def test_incomplete_saved_trainee_plan_cannot_hide_required_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const hasCompleteTraineePlan=data=>Boolean(", source)
        self.assertIn("requiredDay.courseIds.every(id=>savedDay.courseIds.includes(id))", source)
        self.assertIn("if(hasCompleteTraineePlan(data))", source)

    def test_renaming_a_trainee_tile_does_not_turn_its_title_into_a_source(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertNotIn("if(field.dataset.field==='title')course.sources=[value]", source)
        self.assertIn("sources:[],practice:'sales'", source)

    def test_operational_endpoints_and_search_snippets_are_present(self):
        source = (server.ROOT / "server.py").read_text(encoding="utf-8")

        for endpoint in ("/api/academy/submissions", "/api/academy/submission-feedback", "/api/academy/events", "/api/academy/material-metadata", "/api/academy/revisions/restore"):
            self.assertIn(endpoint, source)
        self.assertIn("def search_knowledge_results", source)
        self.assertIn("def append_revision", source)

    def test_manager_reader_loads_full_workflow_materials(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function loadManagerDetailedWorkflow()", source)
        self.assertIn("managerWorkflowSourcesFor(course)", source)
        self.assertIn('id="manager-detailed-flow"', source)

    def test_each_product_passport_has_a_detailed_expert_flow(self):
        manifest = json.loads(server.COURSE_ACCESS_FILE.read_text(encoding="utf-8"))
        passports = [
            path
            for rule in manifest.values()
            for path in rule.get("p", [])
            if "Паспорт продукта —" in path
        ]

        self.assertGreater(len(passports), 0)
        for path in passports:
            source = (server.KNOWLEDGE_ROOT / path).read_text(encoding="utf-8")
            self.assertIn("## Лист: Ход работы эксперта", source, path)

    def test_manager_and_expert_practice_use_different_role_logic(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function practiceFor(course)", source)
        self.assertIn("if(audience!=='expert')return {check:fallbackCheck,working:fallbackWorking};", source)
        self.assertIn("Какой первый шаг эксперта по теме", source)
        self.assertIn("Выберите обязательные действия эксперта", source)

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
    def test_cloudflare_worker_allows_every_server_persistent_state_key(self):
        worker = (server.ROOT / "cloudflare" / "mavis-academy-state.js").read_text(encoding="utf-8")
        for key in server.PERSISTENT_STATE_KEYS.values():
            self.assertIn(f'"{key}"', worker)

    def test_state_request_uses_guarded_rpc_and_never_exposes_access_token_in_url(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'[{"value":{"custom":[]}}]'

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

    def test_cloudflare_rejection_falls_back_to_existing_server_side_results_store(self):
        requested_urls = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'[{"value":{"items":[]}}]'

        def fake_urlopen(request, timeout):
            requested_urls.append(request.full_url)
            if "workers.dev" in request.full_url:
                raise server.HTTPError(request.full_url, 400, "invalid_key", None, None)
            return Response()

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "cloudflare-token",
            "ACADEMY_RESULTS_URL": "https://example.supabase.co",
            "ACADEMY_RESULTS_SERVICE_KEY": "service-key",
            "ACADEMY_RESULTS_WRITE_TOKEN": "results-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            payload = server.persistent_state_request("GET", "academy:trainee-submissions")

        self.assertEqual(payload, {"value": {"items": []}})
        self.assertEqual(len(requested_urls), 2)
        self.assertIn("workers.dev/state?key=academy%3Atrainee-submissions", requested_urls[0])
        self.assertEqual(requested_urls[1], "https://example.supabase.co/rest/v1/rpc/academy_get_dashboard_state")

    def test_cloudflare_keeps_auxiliary_state_inside_the_existing_document_key(self):
        stored = {"value": {"09 SOP/Документ.md": "Текст"}}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps(stored).encode("utf-8")

        def fake_urlopen(request, timeout):
            if request.get_method() == "PUT":
                stored["value"] = json.loads(request.data.decode("utf-8"))["value"]
            return Response()

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertEqual(server.read_persistent_state("document_overrides"), {"09 SOP/Документ.md": "Текст"})
            self.assertTrue(server.write_persistent_state("revisions", {"items": [{"id": "revision-1"}]}))
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertEqual(server.read_persistent_state("document_overrides"), {"09 SOP/Документ.md": "Текст"})
            self.assertEqual(server.read_persistent_state("revisions"), {"items": [{"id": "revision-1"}]})


if __name__ == "__main__":
    unittest.main()
