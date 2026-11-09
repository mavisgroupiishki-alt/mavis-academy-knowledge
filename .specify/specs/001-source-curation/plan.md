# Технический план: Полная редакторская переработка источников

Источники Google Drive, Bitrix24 и вложения сверяются с локальной базой. Доступные материалы превращаются в Markdown-уроки, подключаются в `academy-app/manager-library.js` к нужной роли и индексируются существующим полнотекстовым поиском. Секреты, пароли и персональные данные клиентов исключаются.

| Блок | Профиль | Скилл |
| --- | --- | --- |
| Извлечение документов и таблиц | fast/low | google-drive, google-docs, google-sheets |
| Редакторская переработка | balanced/medium | brainstorming |
| Интеграция Academy | balanced/medium | speckit |
| Проверка и публикация | balanced/medium | verification-before-completion, render-deploy |
