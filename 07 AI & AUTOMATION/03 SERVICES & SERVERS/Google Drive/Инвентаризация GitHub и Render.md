---
type: infrastructure_inventory
scope: GitHub + Render
updated_at: 2026-10-26
secrets: excluded
---

# AI-процессы Mavis: GitHub и Render

Этот документ описывает обнаруженные сервисы Render и их исходные репозитории. Секреты, API-ключи и значения переменных окружения намеренно не включены.

## Как пользоваться

1. Код хранится в GitHub-репозитории.
2. Render собирает выбранную ветку и запускает сервис.
3. При auto-deploy=Yes новый commit обычно запускает новый deploy автоматически.
4. Перед изменениями проверяйте health-check и последние события Render.
5. Секреты меняются только в Environment Variables Render, не в GitHub и не в Obsidian.

### mavis-vibecode-relay
- Render service: srv-db701fuk1f9s73bp4nkg
- Тип: web_service; runtime: node; план: starter; регион: oregon
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-bitrix-expert-assistant
- Ветка: main; auto-deploy: no
- URL: https://mavis-vibecode-relay.onrender.com
- Корень проекта: .
- Сборка: npm install
- Запуск: node relay.js
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### transcribat
- Render service: srv-db6uk4rrjlhs739b33o0
- Тип: web_service; runtime: docker; план: free; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/transcribat
- Ветка: main; auto-deploy: yes
- URL: https://transcribat.onrender.com
- Корень проекта: .
- Сборка: ./Dockerfile
- Запуск: по Dockerfile/настройкам Render
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### iso-smk-kristina
- Render service: srv-db2eq1nlot8c73eucdrg
- Тип: web_service; runtime: docker; план: 0.5c-512mb; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/iso-smk
- Ветка: main; auto-deploy: yes
- URL: https://iso-smk-kristina.onrender.com
- Корень проекта: .
- Сборка: ./Dockerfile
- Запуск: по Dockerfile/настройкам Render
- Диск: /data, 1 GB
- Health-check: не задан
- Статус suspend: not_suspended

### iso-smk-rar
- Render service: srv-dah4sr2jnfac738agg60
- Тип: web_service; runtime: docker; план: 0.5c-512mb; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/iso-smk
- Ветка: main; auto-deploy: yes
- URL: https://iso-smk-rar.onrender.com
- Корень проекта: .
- Сборка: ./Dockerfile
- Запуск: по Dockerfile/настройкам Render
- Диск: /data, 1 GB
- Health-check: не задан
- Статус suspend: not_suspended

### mavis-operational-dashboard
- Render service: srv-dadak42jnfac73f58f7g
- Тип: web_service; runtime: docker; план: 0.5c-512mb; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-operational-dashboard
- Ветка: main; auto-deploy: yes
- URL: https://mavis-operational-dashboard.onrender.com
- Корень проекта: .
- Сборка: ./Dockerfile
- Запуск: по Dockerfile/настройкам Render
- Диск: /var/data, 1 GB
- Health-check: /health
- Статус suspend: not_suspended

### mavis-registry
- Render service: srv-da2l7c67bikc73b945q0
- Тип: web_service; runtime: python; план: 0.5c-512mb; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-kp-generator
- Ветка: main; auto-deploy: yes
- URL: https://mavis-registry.onrender.com
- Корень проекта: registry-server-app
- Сборка: pip install -r requirements.txt
- Запуск: gunicorn app:app --workers 2 --threads 4 --timeout 120
- Диск: нет в метаданных
- Health-check: /health
- Статус suspend: not_suspended

### mavis-payment-schedule
- Render service: srv-d9q939h42hec73a2c1eg
- Тип: web_service; runtime: python; план: 0.5c-512mb; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-payment-schedule
- Ветка: main; auto-deploy: yes
- URL: https://mavis-payment-schedule.onrender.com
- Корень проекта: .
- Сборка: pip install -r requirements.txt
- Запуск: gunicorn app:app
- Диск: нет в метаданных
- Health-check: /health
- Статус suspend: not_suspended

### mavis-task-tracker true
- Render service: srv-d9perum1egvs73fa12k0
- Тип: web_service; runtime: node; план: 0.5c-512mb; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-task-tracker
- Ветка: main; auto-deploy: yes
- URL: https://mavis-task-tracker-true.onrender.com
- Корень проекта: .
- Сборка: npm install && npm run build
- Запуск: npm start
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### marketing
- Render service: srv-d9f0ni6rnols73f5qf50
- Тип: web_service; runtime: python; план: free; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/marketing
- Ветка: main; auto-deploy: yes
- URL: https://marketing-86n1.onrender.com
- Корень проекта: .
- Сборка: pip install -r requirements.txt
- Запуск: gunicorn app:app
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### iso-smk-1
- Render service: srv-d8se8lb7uimc7389bbi0
- Тип: web_service; runtime: docker; план: starter; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/iso-smk
- Ветка: main; auto-deploy: yes
- URL: https://iso-smk-1.onrender.com
- Корень проекта: .
- Сборка: ./Dockerfile
- Запуск: по Dockerfile/настройкам Render
- Диск: /data, 1 GB
- Health-check: не задан
- Статус suspend: not_suspended

### sales-analytics
- Render service: srv-d8nv6f3sq97s73bs5ddg
- Тип: web_service; runtime: python; план: starter; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/sales-analytics
- Ветка: main; auto-deploy: yes
- URL: https://sales-analytics-qyf6.onrender.com
- Корень проекта: .
- Сборка: pip install -r requirements-web.txt
- Запуск: sh deploy/render-start.sh
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### mavis-bitrix-expert-assistant
- Render service: srv-d8jbqlnlk1mc7391cosg
- Тип: web_service; runtime: node; план: starter; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-bitrix-expert-assistant
- Ветка: main; auto-deploy: no
- URL: https://mavis-bitrix-expert-assistant.onrender.com
- Корень проекта: .
- Сборка: npm install
- Запуск: node bootstrap-v133.js
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### mavis-task-tracker
- Render service: srv-d8elrbfavr4c738sv270
- Тип: static_site; runtime: unknown; план: unknown; регион: unknown
- Репозиторий: https://github.com/mavisgroupiishki-alt/mavis-task-tracker
- Ветка: main; auto-deploy: yes
- URL: https://mavis-task-tracker.onrender.com
- Корень проекта: .
- Сборка: по Dockerfile/настройкам Render
- Запуск: по Dockerfile/настройкам Render
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### VAKANSII-1
- Render service: srv-d87ejamk1jcs73dqavdg
- Тип: web_service; runtime: docker; план: free; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/VAKANSII
- Ветка: main; auto-deploy: yes
- URL: https://vakansii-1.onrender.com
- Корень проекта: .
- Сборка: ./Dockerfile
- Запуск: по Dockerfile/настройкам Render
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### mavis-task-bot
- Render service: srv-d7urhetckfvc73bhp9kg
- Тип: web_service; runtime: python; план: free; регион: frankfurt
- Репозиторий: https://github.com/mavisgroupiishki-alt/CentrWorkflow
- Ветка: main; auto-deploy: yes
- URL: https://mavis-task-bot.onrender.com
- Корень проекта: .
- Сборка: pip install -r requirements.txt
- Запуск: python bot.py
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: not_suspended

### iso-smk
- Render service: srv-d715q5a4d50c73bf7hb0
- Тип: web_service; runtime: python; план: free; регион: oregon
- Репозиторий: https://github.com/mavisgroupiishki-alt/iso-smk
- Ветка: main; auto-deploy: yes
- URL: https://iso-smk.onrender.com
- Корень проекта: .
- Сборка: pip install -r requirements.txt
- Запуск: python server.py
- Диск: нет в метаданных
- Health-check: не задан
- Статус suspend: suspended

## Безопасный порядок изменения

- Сначала открыть репозиторий и проверить README, Dockerfile/requirements/package.json.
- Сделать отдельную ветку и Pull Request.
- После проверки запустить deploy в Render.
- Проверить URL и health endpoint.
- При ошибке смотреть Build/Deploy logs и откатить последний commit через GitHub.

## Найденные подключения

GitHub-коннектор API в текущем сеансе вернул 0 репозиториев, хотя в пользовательском GitHub-интерфейсе видны репозитории организации `mavisgroupiishki-alt`. Поэтому в Obsidian добавлены доступные README для Bitrix Expert Assistant, Operational Dashboard, Sales Analytics, Mavis HR Bot и Mavis Task Tracker; остальные репозитории пока отмечены по метаданным Render до восстановления полного API-доступа.

