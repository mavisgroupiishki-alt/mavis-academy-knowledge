---
type: ai_schema
status: active
last_update: 2026-08-28
---

# Mavis Knowledge — Knowledge Schema

## Основные типы заметок

| type | Что означает |
|---|---|
| project | бизнес-/AI-проект |
| system | система компании |
| integration | интеграция |
| sop | инструкция / регламент |
| decision | принятое решение |
| prompt | проверенный промпт |
| metrics | метрики |
| bitrix_field | поле Bitrix24 |
| bitrix_project | проект / рабочая группа Bitrix24 |
| architecture | архитектурная схема |
| service | внешний или внутренний сервис |
| api | API / модель / технический интерфейс |

## Базовые свойства

```yaml
type:
status:
owner:
department:
system:
created:
last_update:
priority:
source:
sensitivity:
review_status:
```

## Рекомендуемые значения status
- active
- pilot
- planned
- paused
- completed
- archived
- draft

## sensitivity
- public
- internal
- confidential
- restricted

По умолчанию корпоративные заметки считаются `internal`.
