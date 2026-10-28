---
type: ai_agent
status: pilot
environment: MacBook
provider: Bitrix24 VibeCode
last_update: 2026-08-28
sensitivity: internal
---

# Mavis AI — Phase 5 Controlled Write

## Что изменилось
Mavis AI получил возможность готовить предложения изменений для Obsidian.

## Безопасная схема
AI → Proposal → Diff → Human approval → Apply → Backup → Changelog

## Важно
**Phase 5 использует обязательное подтверждение человеком для любых изменений.**
AI не может сам применить proposal.

Для применения человек должен:
1. открыть proposal;
2. посмотреть diff;
3. вручную ввести `APPLY <proposal-id>`.

## Bitrix24
Остаётся READ-ONLY.

## Локальные файлы
- Agent: `~/MavisAI/mavis_ai.py`
- Proposals: `~/MavisAI/proposals`
- Backups: `~/MavisAI/backups`
- Secret: `~/MavisAI/.env.local`

## Команды
`/proposals`
`/review P-...`
`/apply P-...`
`/reject P-...`
