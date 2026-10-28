---
type: repository_documentation
source: GitHub
repository: mavisgroupiishki-alt/mavis-task-tracker
updated_at: 2026-10-26
secrets: excluded
---

# MAVIS Task Tracker 6.2

Проектный дашборд MAVIS GROUP с Supabase и Bitrix24 Вайбкод AI.

## Команды

```bash
npm install
npm run build
npm start
```

## Переменные окружения

```text
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
VIBECODE_API_KEY
VIBECODE_MODEL=bitrix/bitrixgpt-5.5
```

`VIBECODE_API_KEY` — только серверный секрет. Никогда не добавляйте к нему префикс `VITE_`.

## 6.2.3 — Бэклог
Добавлена отдельная вкладка Бэклог для временно неактуальных проектов и задач. Перед использованием выполнить supabase_v6_2_3_backlog.sql.

## 6.2.4 — стратегический бэклог + факт времени

Добавлена обязательная фиксация фактически потраченного времени при закрытии задачи, поддержка задач без ответственного/дедлайна и безопасный импорт 85 задач дорожной карты в Бэклог. Для миграции и импорта используйте `ОДИН_SQL_6_2_4_ВРЕМЯ_И_ИМПОРТ_85_ЗАДАЧ_В_БЭКЛОГ.sql`.

