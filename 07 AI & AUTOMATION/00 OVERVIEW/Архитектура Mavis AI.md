---
type: architecture
status: target
last_update: 2026-08-28
---

# Архитектура Mavis AI

```mermaid
flowchart TD
    U[Сотрудник] --> A[Mavis AI]
    A --> K[Obsidian / Mavis Knowledge]
    A --> B[Bitrix24]
    A --> G[GitHub]
    A --> D[Drive / Sheets]
    A --> S[Сервисы и API]
    K --> A
    B --> A
    G --> A
    D --> A
    S --> A
```

## Принцип
Obsidian — память и документация.  
Mavis AI — интеллект и оркестрация.  
Bitrix24 — операционная правда по CRM.  
GitHub — правда по коду.  
Drive/Sheets — документы и табличные данные.

## Правило безопасности
Критичные изменения:
- production-код;
- настройки Bitrix;
- удаление данных;
- изменение регламентов

должны проходить через подтверждение человека.
