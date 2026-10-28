---
type: ai_agent
status: pilot
environment: MacBook
provider: Bitrix24 VibeCode
model: bitrix/bitrixgpt-5.5
last_update: 2026-08-28
sensitivity: internal
---

# Mavis AI — Local Prototype Phase 4

## Статус
🟡 Локальный read-only прототип установлен.

## Где работает
`~/MavisAI`

## AI Router
Bitrix24 VibeCode.

Portal: `mavisgroup.bitrix24.by`

Model: `bitrix/bitrixgpt-5.5`

Access mode ключа: `READWRITE`

## Инструменты Phase 4
- поиск по Mavis Knowledge;
- чтение заметок;
- список проектов;
- проверка метаданных VibeCode key;
- чтение API guide;
- чтение последних сделок;
- получение сделки по ID;
- чтение списка CRM-воронок.

## Безопасность
Phase 4 не содержит инструментов записи в Bitrix24 или Obsidian.

Секрет хранится вне vault:
`~/MavisAI/.env.local`

Значение ключа никогда не должно попадать в Obsidian или GitHub.

## Следующий этап
После проверки качества ответов:
1. подключить GitHub remote;
2. добавить controlled-write workflow для Obsidian;
3. добавить больше read-only инструментов Bitrix24;
4. затем добавить действия только через human approval.
