import sys
import io
import json
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse
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

    def test_allows_an_unpublished_blank_trainee_tile_and_a_review_tile(self):
        curriculum = server.validate_trainee_curriculum({
            "planVersion": server.CURRENT_TRAINEE_PLAN_VERSION,
            "courses": [
                {"id": "blank-draft", "title": "", "lead": "", "eyebrow": "", "content": ""},
                {"id": "repeat-tile", "title": "Повторение", "lead": "", "eyebrow": "", "content": "<p>Текст</p>"},
            ],
            "days": [
                {"courseIds": [], "reviewCourseIds": []},
                {"courseIds": ["repeat-tile"], "reviewCourseIds": ["repeat-tile"]},
                {"courseIds": [], "reviewCourseIds": []},
                {"courseIds": [], "reviewCourseIds": []},
            ],
        })

        self.assertEqual(curriculum["courses"][0]["id"], "blank-draft")
        self.assertEqual(curriculum["days"][1]["reviewCourseIds"], ["repeat-tile"])

    def test_keeps_hidden_blank_trainee_draft_when_saving_programme(self):
        curriculum = server.validate_trainee_curriculum({
            "planVersion": server.CURRENT_TRAINEE_PLAN_VERSION,
            "courses": [{"id": "leader-draft", "title": "", "lead": "", "eyebrow": "", "content": "", "hidden": True}],
            "days": [{"courseIds": [], "reviewCourseIds": []} for _ in range(4)],
        })

        self.assertTrue(curriculum["courses"][0]["hidden"])
        self.assertEqual(curriculum["days"][0]["courseIds"], [])

    def test_trainee_curriculum_limit_accepts_the_current_live_program_size(self):
        self.assertGreater(server.MAX_TRAINEE_CURRICULUM_BYTES, 831_889)

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

    def test_curriculum_reader_never_returns_the_storage_envelope(self):
        programme = {
            "planVersion": server.CURRENT_TRAINEE_PLAN_VERSION,
            "courses": [{"id": "spk", "title": "СПК"}],
            "days": [{"courseIds": ["spk"]} for _ in range(4)],
            "_mavis_academy_auxiliary": {"revisions": {"items": [{"value": "large snapshot"}]}},
        }

        with patch.object(server, "read_persistent_state", return_value=programme):
            self.assertEqual(server.read_trainee_curriculum(), {
                "planVersion": server.CURRENT_TRAINEE_PLAN_VERSION,
                "courses": [{"id": "spk", "title": "СПК"}],
                "days": [{"courseIds": ["spk"]} for _ in range(4)],
            })


class CourseSourceContractTests(unittest.TestCase):
    def test_editor_retries_a_protected_save_after_session_expiry(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("async function renewAcademyAccess()", source)
        self.assertIn("async function academyAuthorizedFetch(url,options={})", source)
        self.assertIn("if(response.status!==401)return response", source)
        self.assertIn("if(!await renewAcademyAccess())return response", source)
        for endpoint in (
            "/api/academy/document-overrides",
            "/api/academy/library-catalog",
            "/api/academy/trainee-curriculum",
            "/api/academy/attempts",
            "/api/academy/submissions",
            "/api/academy/material-metadata",
        ):
            self.assertIn(f"academyAuthorizedFetch('{endpoint}'", source)

    def test_inline_tile_save_is_one_verified_request(self):
        client = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        backend = (server.ROOT / "server.py").read_text(encoding="utf-8")

        save = client.split("window.academySaveInlineMaterial=", 1)[1].split(
            "async function loadDocument", 1
        )[0]
        self.assertIn("/api/academy/tile-save", save)
        self.assertIn("!payload.saved||!payload.verified", save)
        self.assertIn("Не обновляйте страницу", client)
        self.assertIn("def save_tile(self):", backend)
        self.assertIn("write_persistent_states({", backend)

    def test_staff_session_loads_saved_trainee_program_after_refresh(self):
        client = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        backend = (server.ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn("if (access?.role) Promise.all([", client)
        self.assertIn("loadCurriculum(),", client)
        self.assertIn("!saved?.verified", client)
        self.assertIn("Сохраняю и проверяю запись в постоянном хранилище", client)
        self.assertIn("def write_cloudflare_shared_states(updates):", backend)

    def test_static_editor_assets_are_not_served_from_an_old_browser_cache(self):
        source = (server.ROOT / "server.py").read_text(encoding="utf-8")

        self.assertIn('static_path.endswith((".js", ".css"))', source)

    def test_blank_library_drafts_are_saved_instead_of_being_discarded(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        persist = source.split("window.academyPersistLibraryCatalog=", 1)[1].split(
            "window.academyQueueLibrarySave=", 1
        )[0]
        self.assertNotIn("incompleteLibraryTile()", persist)
        self.assertIn("Черновик сохранён", persist)

    def test_saved_blank_drafts_remain_visible_to_the_leader_after_reload(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const draftCount=editor?", source)
        self.assertIn("Черновики: ${draftCount}", source)
        self.assertIn("Открыть черновики · ${draftCount}", source)

    def test_server_and_client_use_the_same_trainee_plan_version(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        client_version = re.search(r"TRAINEE_PLAN_VERSION='([^']+)'", source)

        self.assertIsNotNone(client_version)
        self.assertEqual(server.CURRENT_TRAINEE_PLAN_VERSION, client_version.group(1))

    def test_trainee_editor_saves_placement_and_repetition_together(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("course.hidden=!day", source)
        self.assertIn("Показать в «Повторить»", source)
        self.assertIn("Скрыть у стажёра", source)
        self.assertIn("Сервер не подтвердил сохранение программы.", source)

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

    def test_case_library_uses_the_source_cases_without_generic_product_sections(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("id:'cases'", source)
        self.assertIn("Государственное предприятие «УКС Крупского района»", source)
        self.assertIn("Кейс № 8: Аттестация СТ и СПК", source)
        self.assertIn("Кейс № 10: Первое касание и «лишние» вопросы", source)
        self.assertIn("Кейс № 4: Сгоревшая папка — физический форс-мажор", source)
        self.assertIn("Кейсы — регламенты.md", source)
        self.assertNotIn("ООО «РОГА И КОПЫТА»", source)
        self.assertIn("function casesReader(course)", source)
        case_reader = source.split("function casesReader(course)", 1)[1].split("function reader(){", 1)[0]
        self.assertNotIn("workspace-people", case_reader)
        self.assertNotIn("workspace-tools", case_reader)

    def test_product_reference_sections_take_full_passport_lists_from_general_and_work_sheets(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        spk_passport = (server.ROOT.parent / "02 PRODUCTS" / "Паспорт продукта — 0101 СПК.md").read_text(encoding="utf-8")

        self.assertIn("const sheets=kind==='people'?['Общая','ВИДЫ РАБОТ']:['Общая'];", source)
        self.assertIn("'workspace-tools','Инструменты и СИ'", source)
        self.assertIn("workspace-reference-item", source)
        self.assertIn("sourcePlainText", source)
        self.assertIn("| A14 | Требования по штату специалистов |", spk_passport)
        self.assertIn("| A16 | средства измерения |", spk_passport)
        self.assertIn("рулетка измерительная металлическая", spk_passport)

    def test_product_reader_groups_source_material_and_uses_product_specific_practice(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        styles = (server.ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertIn("const sourceBlockKind=title=>", source)
        self.assertIn("function traineePassportDocument(content)", source)
        self.assertIn("? traineePassportDocument(course.content)", source)
        self.assertIn('class="passport-section passport-section--${group.kind}"', source)
        self.assertIn("contentNodes.flatMap(node=>node.classList.contains('course-sheet')", source)
        self.assertIn("node.matches('details.course-topic')", source)
        self.assertIn("mode==='full'?readableDocument(data,path,isReferenceMaterial(path)):sourceConceptDocument(data,path)", source)
        self.assertNotIn("isStaff(access?.role||state.role)?sourceConceptDocument", source)
        self.assertNotIn("Открыть полный первоисточник", source)
        self.assertIn("const PRODUCT_PRACTICE=", source)
        for product in ("spk", "attestation", "'iso-suot'"):
            self.assertIn(f"{product}:", source)
        self.assertIn("if(productPractice)return productPractice", source)
        self.assertIn(".passport-section", styles)
        self.assertIn(".passport-topic", styles)
        self.assertIn(".passport-section--tools", styles)

    def test_staff_product_tiles_are_source_grounded_and_technical_cards_are_simple(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const TECHNICAL_COURSE_IDS=new Set", source)
        self.assertIn("if(TECHNICAL_COURSE_IDS.has(course.id))return technicalReader(course);", source)
        self.assertIn("const productReferenceSourcesFor=", source)
        self.assertIn(".filter(path=>/^02 PRODUCTS\\//u.test(path)||isExpertSource(path))", source)
        self.assertIn("const sourceConceptDocument=(data,path)=>sourceStructuredDocument", source)
        self.assertIn("const sourceOtherDocument=(data,path)=>sourceStructuredDocument", source)
        self.assertIn("mode==='full'?readableDocument(data,path,isReferenceMaterial(path)):sourceConceptDocument(data,path)", source)
        self.assertIn("if(allowed.size===1&&allowed.has('overview'))", source)
        self.assertIn("groups:[first.groups[0]]", source)
        self.assertIn("function expertWorkflowFromPassport(data,path)", source)
        self.assertIn("sourceStructuredDocument(data,path,new Set(['workflow']))", source)
        self.assertIn("node.tagName==='H3'&&currentGroup?.kind==='workflow'", source)
        self.assertIn("if(currentGroup?.kind==='workflow'){\n          workflowItem=", source)
        self.assertIn('data-source-level="${level}"', source)
        self.assertIn("sourceLevel>2&&currentSheet&&sourceBlockKind(currentSheet.title)==='workflow'", source)

    def test_staff_reference_lists_accept_headed_checklists_as_well_as_sheet_rows(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function headingReferenceEntries(data,path,kind)", source)
        self.assertIn("const headingEntries=headingReferenceEntries(data,path,kind);", source)
        self.assertIn("entry.markdown?markdown(entry.content):richText(entry.content)", source)
        self.assertIn("Загружаю специалистов из первоисточников", source)
        self.assertIn("Загружаю инструменты и СИ из первоисточников", source)
        self.assertIn("|\\bлюд|сотрудник", source)
        self.assertIn("(?:^|[^а-яё])си(?:$|[^а-яё])", source)
        self.assertIn("шаг\\s*\\d", source)

    def test_metal_and_sro_have_role_checklists_with_complete_reference_lists(self):
        project = server.ROOT.parent
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        access = json.loads((server.ROOT / "course-access.json").read_text(encoding="utf-8"))

        expected = {
            "metal": [
                "03 SALES/Чек-лист — металл: менеджер.md",
                "04 EXPERT/Чек-лист — металл: эксперт.md",
            ],
            "sro": [
                "03 SALES/Чек-лист — СРО: менеджер.md",
                "04 EXPERT/Чек-лист — СРО: эксперт.md",
            ],
        }
        for course, paths in expected.items():
            for path in paths:
                self.assertIn(path, access[course]["p"])
                self.assertTrue((project / path).is_file(), path)

        metal = (project / expected["metal"][1]).read_text(encoding="utf-8")
        sro = (project / expected["sro"][1]).read_text(encoding="utf-8")
        self.assertIn("УШС-3", metal)
        self.assertIn("Лист: Ход работы эксперта", metal)
        self.assertIn("Национальный реестр специалистов НОСТРОЙ", sro)
        self.assertIn("Лист: Ход работы эксперта", sro)
        self.assertIn("const productReferenceSourcesFor=", source)
        self.assertIn("Загружаю инструменты и СИ из первоисточников", source)

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
        self.assertIn("'workspace-tools','Инструменты и СИ'", source)
        self.assertIn("loadProductReferenceLists", source)
        self.assertIn("workspace-reference-item", source)
        self.assertIn("'workspace-other','Другое'", source)
        self.assertIn("academyReturnToStaff", source)
        self.assertIn("!['full-library','company'].includes(course.id)", source)
        self.assertIn("Ход работы менеджера", source)
        self.assertIn("const MANAGER_PRODUCT_SALES_ROUTES=", source)
        self.assertIn('id="workspace-script"', source)
        self.assertIn('>Скрипт</a>', source)
        self.assertIn("function loadManagerScripts()", source)
        self.assertIn("const MANAGER_DAY_TWO_CARDS=", source)
        self.assertIn("Скрипт продаж Mavis Group", source)
        self.assertIn("Прайс и коммерческое предложение", source)
        self.assertIn("Кейс для первого КП", source)
        self.assertIn("Разбор звонков", source)
        self.assertIn("workspace-script-source", source)
        self.assertIn("function managerSalesWorkflow", source)
        self.assertIn("Проверить действующее СПК", source)
        self.assertNotIn("Материалы отдела продаж · день 2", source)
        self.assertIn("academyGovernance()", source)
        self.assertIn("academyCleanupTechnicalTrainees", source)
        self.assertNotIn('<a href="#workspace-tips">Подсказки</a>', source)
        self.assertNotIn("Подробный ход работы из паспортов", source)
        self.assertIn("workflow-document", source)
        self.assertNotIn("const roleFocus=", source)
        self.assertIn("window.academyAudience=", source)

    def test_assistant_sends_signed_out_users_to_the_login_screen(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("academy-chat-login", source)
        self.assertIn("Войти в Academy", source)
        self.assertIn("if(!access){state.chat=false;state.login=true;return render();}", source)

    def test_rex_source_snapshots_are_assistant_only_not_catalog_tiles(self):
        project = server.ROOT.parent
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        snapshots = sorted((project / "99 INBOX" / "РЭКС").rglob("*.md"))

        self.assertEqual(len(snapshots), 29)
        self.assertNotIn("99 INBOX/РЭКС/", source)
        searchable_paths = set(server.knowledge_paths())
        for snapshot in snapshots:
            self.assertIn("visibility: assistant_only", snapshot.read_text(encoding="utf-8"), snapshot)
            self.assertIn(str(snapshot.relative_to(project)), searchable_paths, snapshot)

        spk_results = server.search_knowledge_paths("новые правила с 11 марта 2026")
        self.assertIn("99 INBOX/РЭКС/02 Продукты/09 Чек-лист СПК.md", spk_results)

    def test_every_manager_product_uses_a_dedicated_sales_route(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        routes = source.split("const MANAGER_PRODUCT_SALES_ROUTES=", 1)[1].split("function managerSalesWorkflow", 1)[0]
        product_ids = (
            "spk", "attestation", "iso-suot", "iso-37001", "licences", "mchs", "gpn",
            "tr-ts", "product-cert", "sro", "foreign-spk-attestation", "windows-doors",
            "paints", "metal", "tool-rental",
        )
        for course_id in product_ids:
            self.assertRegex(routes, rf"    (?:'{re.escape(course_id)}'|{re.escape(course_id)}):\[", course_id)
        self.assertIn("менеджер не выбирает форму оценки", routes)
        self.assertIn("не запрашивает СИ", routes)

    def test_expert_regulations_are_separate_catalog_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        source_paths = (
            "Регламент — принятие клиента в работу.md",
            "Регламент — пропущенные звонки.md",
            "Регламент — опоздания.md",
            "Регламент — передача информации оформителям.md",
            "Регламент — выезды ISO и СУОТ.md",
            "Регламент — сбор NPS.md",
        )
        for source_path in source_paths:
            self.assertIn(source_path, source)
            self.assertTrue((server.ROOT.parent / "09 SOP" / source_path).is_file(), source_path)

    def test_staff_reader_shows_primary_source_instead_of_static_summary(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        reader = source.rsplit("  function reader(){", 1)[-1].split("  function tileAttachmentsEditor", 1)[0]

        self.assertIn("const conceptContent=sourcePane||noItems", reader)
        self.assertIn("const peopleContent=productPeople||noItems", reader)
        self.assertIn("const toolsContent=productTools||noItems", reader)
        self.assertNotIn("workspace.concept?`<p>", reader)
        self.assertNotIn("workspace.people.length?list", reader)
        self.assertNotIn("workspace.tools.length?list", reader)
        self.assertNotIn("workspace.tips.map", reader)

    def test_every_staff_tile_source_file_exists_and_both_roles_have_sources(self):
        project = server.ROOT.parent
        script = r'''
const fs=require('fs'), vm=require('vm');
const text=fs.readFileSync('academy-app/manager-library.js','utf8');
const end=text.indexOf('  const FULL_LIBRARY_EXTRA_SOURCES');
const code=text.slice(0,end)+'\n globalThis.__courses=COURSES;\n})();';
const context={document:{getElementById:()=>null,createElement:()=>({}),head:{appendChild(){}}},window:{},globalThis:{}};
context.globalThis=context;vm.createContext(context);vm.runInContext(code,context);
const ignored=new Set(['company','full-library','contacts','cases']);
const tiles=context.__courses.filter(course=>!ignored.has(course.id));
const missing=[];
const coverage=[];
for(const tile of tiles){
  const sources=tile.sources||[];
  const manager=sources.filter(path=>!path.startsWith('04 EXPERT/'));
  const expert=sources.filter(path=>!path.startsWith('03 SALES/'));
  for(const path of sources) if(!fs.existsSync(path)) missing.push(`${tile.id}: ${path}`);
  coverage.push({id:tile.id,roles:tile.roles||['manager','expert','leader'],manager:manager.length,expert:expert.length});
}
console.log(JSON.stringify({missing,coverage}));
'''
        result = subprocess.run(
            ["node", "-e", script], cwd=project, text=True,
            capture_output=True, check=True,
        )
        audit = json.loads(result.stdout)

        self.assertEqual(audit["missing"], [])
        self.assertTrue(audit["coverage"])
        for tile in audit["coverage"]:
            if "manager" in tile["roles"]:
                self.assertGreater(tile["manager"], 0, tile["id"])
            if "expert" in tile["roles"]:
                self.assertGreater(tile["expert"], 0, tile["id"])

    def test_trainee_spk_is_a_standalone_curriculum_lesson(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("id:'tr-spk'", source)
        self.assertIn("СПК: свидетельство", source)
        self.assertIn("const TRAINEE_COURSE_IDS=new Set", source)
        self.assertIn("[...TRAINEE_COURSES,...TRAINEE_FOUNDATION_COURSES].find", source)
        self.assertNotIn("const TRAINEE_SOURCE_COURSES", source)

    def test_trainee_keeps_the_four_day_curriculum_instead_of_staff_reference_tabs(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        program = (server.ROOT / "generated" / "trainee-program.js").read_text(encoding="utf-8")

        self.assertIn("const TRAINEE_DAYS = window.MAVIS_TRAINEE_PROGRAM?.days || [];", source)
        self.assertIn("const TRAINEE_SHEET_COURSES = window.MAVIS_TRAINEE_PROGRAM?.courses || [];", source)
        self.assertIn('"title":"День 4 · звонки и финальный тест"', program)
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
        self.assertIn("const TRAINEE_TABLE_ONLY_IDS=new Set(['tr-d1-video']);", source)
        self.assertNotIn("'tr-d1-company':'09 SOP/Учебный маршрут — Mavis Group: компания и словарь.md'", source)
        self.assertIn("const TRAINEE_DAY_ONE_SOURCE_PATHS=", source)
        self.assertIn("const TRAINEE_DAY_ONE_SOURCE_COURSES=", source)
        self.assertIn("const TRAINEE_INTERNAL_SOURCE_PATHS=", source)
        self.assertIn("TRAINEE_INTERNAL_SOURCE_PATHS[course.id]", source)
        self.assertIn("sourceCourse:TRAINEE_INTERNAL_SOURCE_COURSES[course.id]||course.sourceCourse||''", source)
        self.assertIn("if((access?.role||state.role)==='trainee')return reference?[]:all", source)

    def test_days_two_to_four_open_internal_sources_instead_of_external_links(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        expected_paths = (
            "03 SALES/Скрипты — Скрипт продаж МАВИС ГРУПП общий:.md",
            "06 BITRIX24/Регламент — работа с делами и воронкой производства.md",
            "02 PRODUCTS/Учебный маршрут — лицензия МВД.md",
            "02 PRODUCTS/Учебный маршрут — лицензия МЧС.md",
            "03 SALES/Сценарии — холодный звонок, возражения и периодика.md",
        )
        for path in expected_paths:
            self.assertIn(path, source)
            self.assertTrue((server.KNOWLEDGE_ROOT / path).is_file(), path)

        self.assertIn("'tr-d3-mvd':'licences'", source)
        self.assertIn("'tr-d3-mchs':'mchs'", source)
        self.assertTrue(server.document_access_for("trainee", "licences", "02 PRODUCTS/Учебный маршрут — лицензия МВД.md"))
        self.assertTrue(server.document_access_for("trainee", "mchs", "02 PRODUCTS/Учебный маршрут — лицензия МЧС.md"))

    def test_trainee_default_contains_only_sheet_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        program = (server.ROOT / "generated" / "trainee-program.js").read_text(encoding="utf-8")

        self.assertIn("let traineeCourses = bindTraineeSources([...TRAINEE_SHEET_COURSES]);", source)
        self.assertEqual(program.count('"importedSheet":true'), 18)
        self.assertIn('"courseIds":["tr-sheet-d1-01","tr-sheet-d1-02","tr-sheet-d1-03","tr-sheet-d1-04","tr-sheet-d1-05","tr-sheet-d1-06"]', program)
        self.assertNotIn("tr-d1-sales-structure", program)
        self.assertNotIn("let traineeCourses = bindTraineeSources([...TRAINEE_SHEET_COURSES, ...TRAINEE_FOUNDATION_COURSES", source)

    def test_trainee_course_reader_is_defined(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function readerTraineeLegacy(course)", source)
        self.assertIn("academyCompleteSource('${course.id}',0)", source)

    def test_trainee_reader_prefers_the_full_internal_source_to_a_short_preview(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        reader = source.split("function readerTraineeLegacy(course)", 1)[1].split("function contactsReader(course)", 1)[0]

        self.assertIn("path=(course.sources||[])[0]||''", reader)
        self.assertIn("id=\"course-document\"", reader)
        self.assertIn("Открываю полный материал…", reader)
        self.assertIn("Загружаю исходную таблицу и чек-лист внутрь плитки.", reader)

    def test_numbered_source_lines_render_as_one_readable_numbered_list(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        styles = (server.ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertIn('class="course-number-list"', source)
        self.assertIn("const numbered=/^(\\d+)[.)]\\s+(.+)$/.exec(line);", source)
        self.assertIn(".course-number-list", styles)

    def test_trainee_lessons_embed_materials_and_keep_submitted_work(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        program = (server.ROOT / "generated" / "trainee-program.js").read_text(encoding="utf-8")

        self.assertIn("if(course.importedSheet)return {...course,sources:[],attachments:[],sourceCourse:'',fallbackContent:''};", source)
        self.assertIn("Проверьте понимание темы", source)
        self.assertIn('"title":"Допродажи"', program)
        self.assertIn('"title":"Лицензия МВД"', program)
        self.assertNotIn("tr-d3-script-practice", program)
        final_exam = source.split("const FINAL_EXAM_BANK = [", 1)[1].split("];", 1)[0]
        self.assertEqual(final_exam.count("{q:'"), 20)

    def test_trainee_checks_use_real_multiple_choice_cases_not_study_yes_no_prompts(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const TRAINEE_QUIZ_BANK", source)
        self.assertIn("const TRAINEE_QUIZ_REQUIRED_COUNT=8", source)
        self.assertIn("return [...exact,...traineeAppliedQuestions(course)].slice(0,TRAINEE_QUIZ_REQUIRED_COUNT);", source)
        self.assertIn("function traineeQuizModal()", source)
        self.assertIn("Государственное предприятие «УКС Крупского района»", source)
        self.assertIn("tr-sheet-d1-03", source)
        self.assertNotIn("Проверка по теме «СПК»: материал плитки изучен?", source)
        final_exam = source.split("function finalExam()", 1)[1].split("const visibleTraineeName", 1)[0]
        self.assertNotIn("exam-written", final_exam)
        self.assertIn("Выберите ответ на все", source)

    def test_trainee_has_a_private_profile_and_server_side_progress_route(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        backend = (server.ROOT / "server.py").read_text(encoding="utf-8")

        self.assertIn("function traineeProfile()", source)
        self.assertIn("academyTraineeProfile", source)
        self.assertIn("/api/academy/trainee-profile", source)
        self.assertIn("/api/academy/trainee-progress", source)
        self.assertIn('"trainee_progress": "academy:trainee-progress"', backend)
        self.assertIn("def trainee_profile(self):", backend)
        self.assertIn("def save_trainee_progress(self):", backend)

    def test_trainee_progress_keeps_only_safe_completion_flags(self):
        cleaned = server.safe_trainee_progress({
            "tr-sheet-d1-03": {"done": True, "at": "2026-11-16T10:00:00Z"},
            "lesson:tr-sheet-d1-03:0": {"done": True, "at": "2026-11-16T10:00:00Z"},
            "not-a-course": {"done": True},
        })
        self.assertEqual(set(cleaned), {"tr-sheet-d1-03", "lesson:tr-sheet-d1-03:0"})

    def test_trainee_day_one_keeps_video_general_information_and_seven_products(self):
        program = (server.ROOT / "generated" / "trainee-program.js").read_text(encoding="utf-8")
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        for title in ("Видео-обучение", "Общая информация", "СПК", "Аттестат", "ISO 9001", "ISO 45001"):
            self.assertIn(title, program)
        self.assertIn('"tr-sheet-d1-01"', program)
        self.assertIn('"tr-sheet-d1-06"', program)
        self.assertIn("TRAINEE_PLAN_VERSION='trainee-sheets-2026-11-13.1'", source)
        self.assertIn("trainee-video-source", program)

    def test_day_one_video_is_embedded_in_a_large_source_tile(self):
        styles = (server.ROOT / "styles.css").read_text(encoding="utf-8")
        program = (server.ROOT / "generated" / "trainee-program.js").read_text(encoding="utf-8")

        self.assertIn(".trainee-video-source iframe", styles)
        self.assertIn('https://docs.google.com/videos/d/1i3c78SieIX4SOQVvViOQ1t5WSzKgY4UuCoqecyZ0fus/play', program)

    def test_saved_trainee_plan_allows_leader_to_hide_or_merge_tiles(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("const hasCompleteTraineePlan=data=>Boolean(", source)
        self.assertIn("data.days.length===TRAINEE_DAYS.length", source)
        self.assertIn("data.courses.every(course=>course&&typeof course.id==='string'", source)
        self.assertIn("if(hasCompleteTraineePlan(data))", source)
        self.assertIn("TRAINEE_CURRICULUM_TEMPLATE", source)
        self.assertIn("requiresSheetUpgrade", source)

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


class KnowledgeAssistantRetrievalTests(unittest.TestCase):
    def test_trainee_assistant_uses_full_corpus_without_expanding_direct_document_access(self):
        source = (server.ROOT / "server.py").read_text(encoding="utf-8")

        self.assertIn('if role not in ACCESS_ROLES:', source)
        self.assertIn('sources = select_knowledge_sources(question, knowledge_paths())', source)
        self.assertIn('Direct source opening remains protected by document_access_for.', source)

    def test_short_product_abbreviations_are_kept_in_assistant_queries(self):
        self.assertIn("си", server.normalize_terms("перечень СИ для СПК"))
        self.assertIn("спк", server.normalize_terms("как подать заявление для СПК"))

    def test_spk_queries_retrieve_relevant_passport_rows_instead_of_file_prefix(self):
        passport_path = "02 PRODUCTS/Паспорт продукта — 0101 СПК.md"
        unrelated_path = "03 SALES/Скрипт продаж.md"
        docs = {
            passport_path: "# Паспорт СПК\n| A16 | средства измерения |\n| B16 | Рулетка; линейка; нивелир; нивелирная рейка; манометр |\n| A17 | средства измерения в аренду |\n| B17 | Нивелир; теодолит |",
            unrelated_path: "# Скрипт продаж\nЗаявление о цене и встрече с клиентом.",
        }
        with patch.object(server, "knowledge_paths", return_value=list(docs)), patch.object(
            server, "fetch_knowledge_document", side_effect=lambda path, limit=None: docs[path]
        ):
            server.KNOWLEDGE_TEXT_CACHE["texts"].clear()
            sources = server.select_knowledge_sources("перечень СИ для СПК")

        self.assertEqual(sources[0]["path"], passport_path)
        self.assertIn("Рулетка; линейка; нивелир", sources[0]["text"])

    def test_real_spk_passport_tools_cell_is_retrieved_for_si_query(self):
        passport_path = "02 PRODUCTS/Паспорт продукта — 0101 СПК.md"
        server.KNOWLEDGE_TEXT_CACHE["texts"].pop(passport_path, None)
        sources = server.select_knowledge_sources("перечень СИ для СПК", [passport_path])

        self.assertEqual(sources[0]["path"], passport_path)
        self.assertIn("| A16 | средства измерения |", sources[0]["text"])
        self.assertIn("| B16 |", sources[0]["text"])
        self.assertIn("нивелир", sources[0]["text"].lower())

    def test_openrouter_web_citations_are_kept_separate_and_safe(self):
        sources = server.openrouter_external_sources({"annotations": [
            {"type": "url_citation", "url_citation": {"url": "https://pravo.by/page", "title": "Правовой портал"}},
            {"type": "url_citation", "url_citation": {"url": "https://pravo.by/page", "title": "Правовой портал"}},
            {"type": "url_citation", "url_citation": {"url": "javascript:alert(1)", "title": "Bad"}},
        ]})

        self.assertEqual(sources, [{"title": "Правовой портал", "url": "https://pravo.by/page"}])

    def test_openrouter_request_uses_bounded_web_search_and_never_exposes_key_in_body(self):
        request = server.build_openrouter_request("test-secret", "openai/gpt-6.1-terra", "system", "prompt")
        payload = json.loads(request.data)

        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
        self.assertEqual(payload["tools"][0]["type"], "openrouter:web_search")
        self.assertEqual(payload["tools"][0]["parameters"]["max_uses"], 1)
        self.assertEqual(payload["tools"][0]["parameters"]["max_results"], 3)
        self.assertNotIn("test-secret", request.data.decode("utf-8"))

    def test_openrouter_retries_transient_search_failure_without_optional_search(self):
        success = io.BytesIO('{"choices":[{"message":{"content":"Ответ из базы"}}]}'.encode("utf-8"))
        failure = server.HTTPError("https://openrouter.ai", 503, "unavailable", None, None)
        with patch.object(server, "urlopen", side_effect=[failure, success]) as open_url, patch.object(server.time, "sleep"):
            response, degraded = server.request_openrouter_answer("test-secret", "model", "system", "prompt")

        self.assertTrue(degraded)
        self.assertEqual(response["choices"][0]["message"]["content"], "Ответ из базы")
        first_payload = json.loads(open_url.call_args_list[0].args[0].data)
        retry_payload = json.loads(open_url.call_args_list[1].args[0].data)
        self.assertIn("tools", first_payload)
        self.assertNotIn("tools", retry_payload)

    def test_openrouter_does_not_retry_permanent_auth_errors(self):
        failure = server.HTTPError("https://openrouter.ai", 401, "unauthorized", None, None)
        with patch.object(server, "urlopen", side_effect=failure) as open_url:
            with self.assertRaises(server.HTTPError):
                server.request_openrouter_answer("test-secret", "model", "system", "prompt")

        open_url.assert_called_once()

    def test_internal_fallback_keeps_retrieved_excerpt_and_marks_web_search_unavailable(self):
        answer = server.internal_knowledge_fallback([{
            "path": "02 PRODUCTS/Паспорт продукта — 0101 СПК.md",
            "text": "Этап подачи заявки: направить заявку в орган по электронной почте.",
        }])

        self.assertIn("веб-поиск не выполнен", answer)
        self.assertIn("Этап подачи заявки", answer)
        self.assertIn("Паспорт продукта — 0101 СПК.md", answer)

    def test_spk_application_question_retrieves_application_step_not_document_intro(self):
        passport_path = "02 PRODUCTS/Паспорт продукта — 0101 СПК.md"
        docs = {
            passport_path: "# Паспорт СПК\n| A1 | Общая информация |\n| B1 | Длинное вводное описание документа. |\n| A3 | 2 этап: Подача заявки |\n| B3 | Заполнить заявку и направить её на электронную почту органа. Орган вышлет договор и счёт, которые направляют клиенту для оплаты. |",
        }
        with patch.object(server, "knowledge_paths", return_value=list(docs)), patch.object(
            server, "fetch_knowledge_document", side_effect=lambda path, limit=None: docs[path]
        ):
            server.KNOWLEDGE_TEXT_CACHE["texts"].clear()
            sources = server.select_knowledge_sources("как подать заявление для СПК")

        self.assertEqual(sources[0]["path"], passport_path)
        self.assertIn("направить её на электронную почту органа", sources[0]["text"])

    def test_manager_reader_uses_sales_route_not_expert_workflow_material(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")

        self.assertIn("function managerSalesWorkflow(course)", source)
        self.assertIn("Ход работы менеджера", source)
        self.assertIn("Проверить действующее СПК", source)
        self.assertIn("MANAGER_PRODUCT_SALES_ROUTES[course.id]", source)
        self.assertIn("'tr-ts':[", source)
        self.assertIn("не запрашивает СИ", source)
        self.assertNotIn("loadDocument();loadManagerDetailedWorkflow();", source)

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
    def test_registered_trainee_name_is_used_for_case_variant_results(self):
        rows, trainees = server.reconcile_trainee_reporting(
            [{"candidate_name": "анна", "attempt_type": "quiz"}, {"candidate_name": "test-run", "attempt_type": "quiz"}],
            [{"candidate_name": "Анна", "first_seen_at": "2026-11-16T08:00:00Z"}],
            [],
        )

        self.assertEqual([item["candidate_name"] for item in trainees], ["Анна"])
        self.assertEqual([item["candidate_name"] for item in rows], ["Анна"])

    def test_orphaned_attempt_does_not_create_a_trainee_card(self):
        rows, trainees = server.reconcile_trainee_reporting(
            [{"candidate_name": "Старый тест", "attempt_type": "quiz"}],
            [{"candidate_name": "Анна", "first_seen_at": "2026-11-16T08:00:00Z"}],
            [],
        )

        self.assertEqual(rows, [])
        self.assertEqual([item["candidate_name"] for item in trainees], ["Анна"])

    def test_technical_trainee_rows_are_removed_from_registry_data(self):
        kept, removed = server.remove_technical_trainees([
            {"candidate_name": "Анна"},
            {"candidate_name": "test-run"},
            {"candidate_name": "Демо 1"},
        ])

        self.assertEqual([item["candidate_name"] for item in kept], ["Анна"])
        self.assertEqual(removed, 2)

    def test_technical_trainee_results_are_removed_with_the_registry_entries(self):
        kept, removed = server.remove_technical_trainee_rows([
            {"candidate_name": "Анна", "attempt_type": "final-exam"},
            {"candidate_name": "test-run", "attempt_type": "final-exam"},
        ])

        self.assertEqual([item["candidate_name"] for item in kept], ["Анна"])
        self.assertEqual(removed, 1)

    def test_cloudflare_attempt_keeps_existing_practice_submissions(self):
        state = {
            "items": [{"candidate_name": "Анна", "title": "Кейс"}],
            "attempts": [],
        }
        saved = []
        row = {"candidate_name": "Анна", "attempt_type": "final-exam", "score": 8, "max_score": 10, "passed": True, "result": {}}

        with patch.object(server, "read_trainee_activity_state", return_value=state), patch.object(
            server, "write_auxiliary_state", side_effect=lambda *args: saved.append(args[2])
        ):
            server.save_cloudflare_attempt(row)

        self.assertEqual(saved[0]["items"], state["items"])
        self.assertEqual(saved[0]["attempts"][0]["candidate_name"], "Анна")

    def test_large_curriculum_round_trips_through_compact_state_value(self):
        curriculum = {
            "courses": [{"id": "test", "title": "Тема", "content": "Практический материал. " * 15000}],
            "days": [{"title": "День 1", "courseIds": ["test"], "reviewCourseIds": []}] * 4,
            "planVersion": "test",
        }

        packed = server.encode_persistent_value(curriculum)

        self.assertEqual(packed[server.PERSISTENT_STATE_COMPRESSION_MARKER], "zlib-json-v1")
        self.assertLess(len(json.dumps(packed)), len(json.dumps(curriculum, ensure_ascii=False)))
        self.assertEqual(server.decode_persistent_value(packed), curriculum)

    def test_named_trainee_removal_is_exact(self):
        kept, removed = server.remove_named_trainee([
            {"candidate_name": "Анна"},
            {"candidate_name": "Анна Петрова"},
        ], "анна")

        self.assertEqual([item["candidate_name"] for item in kept], ["Анна Петрова"])
        self.assertEqual(removed, 1)

    def test_leader_results_uses_cloudflare_activity_store(self):
        backend = (server.ROOT / "server.py").read_text(encoding="utf-8")

        self.assertIn('activity = read_trainee_activity_state()', backend)
        self.assertIn('payload["storage"] = "cloudflare"', backend)
        self.assertIn('"submissions": normalized_submissions[-100:]', backend)

    def test_knowledge_gap_is_saved_once_without_breaking_a_question(self):
        saved = []
        state = {"items": []}

        def save(*args):
            state.clear()
            state.update(args[2])
            saved.append(args[2])

        with patch.object(server, "read_auxiliary_state", side_effect=lambda *_: state), patch.object(
            server, "write_auxiliary_state", side_effect=save
        ):
            server.record_knowledge_gap({"name": "Анна", "role": "manager"}, "Какой документ нужен для нового редкого продукта?")
            server.record_knowledge_gap({"name": "Анна", "role": "manager"}, "Какой документ нужен для нового редкого продукта?")

        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["items"][0]["type"], "knowledge_gap")
        self.assertEqual(saved[0]["items"][0]["question"], "Какой документ нужен для нового редкого продукта?")

    def test_governance_exposes_unanswered_knowledge_questions(self):
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        backend = (server.ROOT / "server.py").read_text(encoding="utf-8")

        self.assertIn('/api/academy/governance', source)
        self.assertIn('Вопросы без ответа в базе', source)
        self.assertIn('def academy_governance(self):', backend)


    def test_governance_reads_independent_state_streams(self):
        class GovernanceHandler:
            headers = {}

            def respond_json(self, payload, code=200):
                self.payload = payload
                self.code = code
                return payload

        handler = GovernanceHandler()
        streams = {
            "material_metadata": {"items": {"02 PRODUCTS/СПК.md": {"status": "actual"}}},
            "revisions": {"items": [{"id": "rev-1", "scope": "document", "key": "02 PRODUCTS/СПК.md"}]},
            "academy_events": {"items": [{"type": "knowledge_gap", "question": "Где чек-лист?"}]},
        }
        with patch.object(server, "access_role_from_header", return_value="leader"), patch.object(
            server, "read_auxiliary_state", side_effect=lambda name, *_: streams[name]
        ) as read_state:
            payload = server.Handler.academy_governance(handler)

        self.assertEqual(read_state.call_count, 3)
        self.assertEqual(payload["metadata"]["02 PRODUCTS/СПК.md"]["status"], "actual")
        self.assertEqual(payload["revisions"][0]["id"], "rev-1")
        self.assertEqual(payload["gaps"][0]["question"], "Где чек-лист?")

    def test_inbox_is_searchable_without_a_catalog_tile(self):
        self.assertIn("99 INBOX/", server.ALLOWED_KNOWLEDGE_PREFIXES)
        paths = server.knowledge_paths()
        self.assertTrue(any(path.startswith("99 INBOX/") for path in paths))
        source = (server.ROOT / "manager-library.js").read_text(encoding="utf-8")
        self.assertNotIn("sources:products('99 INBOX'", source)

    def test_revision_log_failure_does_not_block_primary_save(self):
        with patch.object(server, "append_revision", side_effect=server.HTTPError("https://state", 400, "invalid_key", None, None)):
            self.assertIsNone(server.append_revision_best_effort("curriculum", "trainee_curriculum", {"courses": []}, "Руководитель"))

    def test_cloudflare_worker_allows_every_server_persistent_state_key(self):
        worker = (server.ROOT / "cloudflare" / "mavis-academy-state.js").read_text(encoding="utf-8")
        for key in server.PERSISTENT_STATE_KEYS.values():
            self.assertIn(f'"{key}"', worker)

    def test_cloudflare_worker_keeps_render_awake_on_schedule(self):
        worker = (server.ROOT / "cloudflare" / "mavis-academy-state.js").read_text(encoding="utf-8")
        self.assertIn("async scheduled", worker)
        self.assertIn('https://mavis-academy.onrender.com/healthz', worker)

    def test_cloudflare_is_the_only_state_backend(self):
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
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_TOKEN": "server-only-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            payload = server.persistent_state_request("GET", "academy:library-catalog")

        self.assertEqual(payload, {"value": {"custom": []}})
        self.assertEqual(captured["url"], "https://mavis-academy-state.example.workers.dev/state?key=academy%3Alibrary-catalog")
        self.assertNotIn("server-only-token", captured["url"])

    def test_cloudflare_state_config_accepts_the_worker_secret_name_on_render(self):
        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_TOKEN": "worker-secret",
        }, clear=True):
            backend, url, _, token = server.persistent_state_config()

        self.assertEqual(backend, "cloudflare")
        self.assertEqual(url, "https://mavis-academy-state.example.workers.dev")
        self.assertEqual(token, "worker-secret")

    def test_persistent_write_rejects_a_success_response_without_the_saved_value(self):
        with patch.object(server, "persistent_state_config", return_value=("cloudflare", "https://example", None, "token")), patch.object(
            server, "persistent_state_request", return_value={"saved": True}
        ):
            with self.assertRaisesRegex(OSError, "write_unconfirmed"):
                server.write_persistent_state("library_catalog", {"custom": []})

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

    def test_confirmed_cloudflare_write_does_not_call_supabase(self):
        requested_urls = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b'{"value":{"custom":[]}}'

        def fake_urlopen(request, timeout):
            requested_urls.append(request.full_url)
            return Response()

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "cloudflare-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            payload = server.persistent_state_request("POST", "academy:library-catalog", {"custom": []})

        self.assertEqual(payload, {"value": {"custom": []}})
        self.assertEqual(len(requested_urls), 1)
        self.assertIn("workers.dev/state?key=academy%3Alibrary-catalog", requested_urls[0])

    def test_persistent_write_requires_a_readback_match(self):
        with patch.object(server, "persistent_state_config", return_value=("cloudflare", "https://example", None, "token")), patch.object(
            server, "persistent_state_request", side_effect=[{"value": {"custom": []}}, {"value": {"custom": ["stale"]}}]
        ):
            with self.assertRaisesRegex(OSError, "readback_unconfirmed"):
                server.write_persistent_state("library_catalog", {"custom": []})

    def test_cloudflare_rejection_is_reported_without_a_second_store(self):
        def fake_urlopen(request, timeout):
            raise server.HTTPError(request.full_url, 401, "unauthorized", None, None)

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "rotated-cloudflare-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            with self.assertRaises(server.HTTPError):
                server.persistent_state_request("GET", "academy:trainee-submissions")

    def test_cloudflare_malformed_response_is_reported(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return b"<html>temporary gateway response</html>"

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "cloudflare-token",
        }, clear=False), patch.object(server, "urlopen", return_value=Response()):
            with self.assertRaises(json.JSONDecodeError):
                server.persistent_state_request("GET", "academy:material-metadata")

    def test_cloudflare_saves_each_editor_state_under_its_own_key(self):
        stored = {server.PERSISTENT_STATE_KEYS["curriculum"]: {"courses": [], "days": [], "planVersion": "test"}}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps({"value": stored.get(self.key)}).encode("utf-8")

        def fake_urlopen(request, timeout):
            key = parse_qs(urlparse(request.full_url).query).get("key", [""])[0]
            if request.get_method() == "PUT":
                stored[key] = json.loads(request.data.decode("utf-8"))["value"]
            response = Response()
            response.key = key
            return response

        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            values = {
                "revisions": {"items": [{"id": "revision-1"}]},
                "document_overrides": {"09 SOP/valid.md": "<p>Сохранённый текст</p>"},
                "library_catalog": {"hidden": [], "overrides": {}, "custom": [], "archived": []},
            }
            for name, value in values.items():
                server.PERSISTENT_STATE_CACHE.clear()
                self.assertTrue(server.write_persistent_state(name, value))
                server.PERSISTENT_STATE_CACHE.clear()
                self.assertEqual(server.read_persistent_state(name), value)
            self.assertEqual(stored[server.PERSISTENT_STATE_KEYS["curriculum"]]["courses"], [])
            for name, value in values.items():
                self.assertEqual(stored[server.PERSISTENT_STATE_KEYS[name]], value)
            self.assertNotIn(
                server.CLOUDFLARE_AUXILIARY_ENVELOPE_KEY,
                stored[server.PERSISTENT_STATE_KEYS["curriculum"]],
            )

    def test_cloudflare_migrates_legacy_envelope_before_replacing_curriculum(self):
        legacy_catalog = {"hidden": [], "overrides": {}, "custom": [{"id": "saved-tile"}], "archived": []}
        stored = {
            server.PERSISTENT_STATE_KEYS["curriculum"]: {
                "courses": [{"id": "old"}],
                server.CLOUDFLARE_AUXILIARY_ENVELOPE_KEY: {"library_catalog": legacy_catalog},
            }
        }

        class Response:
            def __init__(self, key):
                self.key = key

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps({"value": stored.get(self.key)}).encode("utf-8")

        def fake_urlopen(request, timeout):
            key = parse_qs(urlparse(request.full_url).query).get("key", [""])[0]
            if request.get_method() == "PUT":
                stored[key] = json.loads(request.data.decode("utf-8"))["value"]
            return Response(key)

        replacement = {"courses": [{"id": "new"}], "days": [], "planVersion": "test"}
        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(server, "urlopen", fake_urlopen):
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertTrue(server.write_persistent_state("curriculum", replacement))

        self.assertEqual(stored[server.PERSISTENT_STATE_KEYS["library_catalog"]], legacy_catalog)
        self.assertEqual(stored[server.PERSISTENT_STATE_KEYS["curriculum"]], replacement)

    def test_cloudflare_reads_a_legacy_editor_value_until_it_is_saved_to_curriculum(self):
        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(
            server, "cloudflare_curriculum_auxiliary_envelope", return_value={}
        ), patch.object(
            server, "persistent_state_request", return_value={"value": {"legacy": "editor content"}}
        ) as request:
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertEqual(server.read_persistent_state("document_overrides"), {"legacy": "editor content"})
            request.assert_called_once_with("GET", server.PERSISTENT_STATE_KEYS["document_overrides"])

    def test_cloudflare_ignores_unavailable_legacy_editor_key(self):
        with patch.dict(server.os.environ, {
            "ACADEMY_STATE_BACKEND": "cloudflare",
            "ACADEMY_STATE_URL": "https://mavis-academy-state.example.workers.dev",
            "ACADEMY_STATE_WRITE_TOKEN": "server-only-token",
        }, clear=False), patch.object(
            server, "cloudflare_curriculum_auxiliary_envelope", return_value={}
        ), patch.object(
            server, "persistent_state_request", side_effect=server.HTTPError("https://state.example", 400, "invalid_key", None, None)
        ):
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertIsNone(server.read_persistent_state("document_overrides"))

    def test_cloudflare_uses_confirmed_catalog_key_when_worker_rejects_curriculum_key(self):
        stored = {server.CLOUDFLARE_COMPATIBILITY_STATE_KEY: {"hidden": [], "overrides": {}, "custom": [], "archived": []}}
        rejection = server.HTTPError("https://state.example", 400, "invalid_key", None, None)
        rejection.academy_storage_detail = "worker_invalid_key"

        def request(method, key, value=None):
            if key == server.PERSISTENT_STATE_KEYS["curriculum"]:
                raise rejection
            if method == "POST":
                stored[key] = value
            return {"value": stored.get(key)}

        curriculum = {"courses": [{"id": "day-1"}], "days": [], "planVersion": "test"}
        with patch.object(server, "persistent_state_config", return_value=("cloudflare", "https://example", None, "token")), patch.object(
            server, "persistent_state_request", side_effect=request
        ), patch.object(server, "CLOUDFLARE_SHARED_STATE_ENABLED", False):
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertTrue(server.write_persistent_state("curriculum", curriculum))
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertEqual(server.read_persistent_state("curriculum"), curriculum)
            envelope = stored[server.CLOUDFLARE_COMPATIBILITY_STATE_KEY]
            self.assertEqual(envelope[server.CLOUDFLARE_COMPATIBILITY_STATE_FIELD], server.CLOUDFLARE_COMPATIBILITY_STATE_MARKER)
            self.assertEqual(envelope["states"]["library_catalog"]["custom"], [])

    def test_cloudflare_detects_shared_envelope_after_a_fresh_process_start(self):
        curriculum = {"courses": [{"id": "day-1"}], "days": [], "planVersion": "test"}
        stored = {
            server.CLOUDFLARE_COMPATIBILITY_STATE_KEY: {
                server.CLOUDFLARE_COMPATIBILITY_STATE_FIELD: server.CLOUDFLARE_COMPATIBILITY_STATE_MARKER,
                "states": {"curriculum": curriculum, "library_catalog": {"hidden": [], "overrides": {}, "custom": [], "archived": []}},
            }
        }

        def request(method, key, value=None):
            self.assertEqual(method, "GET")
            self.assertEqual(key, server.CLOUDFLARE_COMPATIBILITY_STATE_KEY)
            return {"value": stored[key]}

        with patch.object(server, "persistent_state_config", return_value=("cloudflare", "https://example", None, "token")), patch.object(
            server, "persistent_state_request", side_effect=request
        ), patch.object(server, "CLOUDFLARE_SHARED_STATE_ENABLED", False):
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertEqual(server.read_persistent_state("library_catalog")["custom"], [])
            server.PERSISTENT_STATE_CACHE.clear()
            self.assertEqual(server.read_persistent_state("curriculum"), curriculum)


if __name__ == "__main__":
    unittest.main()
