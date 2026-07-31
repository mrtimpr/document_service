# Document Processing Service

Сервис приема и модерации пользовательских документов. Зарегистрированный пользователь загружает файл через REST API, администратор получает email-уведомление и обрабатывает документ в Django Admin. После подтверждения или отклонения пользователь получает письмо. Все уведомления выполняются через Celery.

## Возможности

- регистрация пользователей и JWT-аутентификация;
- загрузка документов через `multipart/form-data`;
- доступ пользователя только к собственным документам;
- статусы `pending`, `approved`, `rejected`;
- быстрые admin-действия подтверждения и отклонения;
- асинхронные email-уведомления через Celery и Redis;
- PostgreSQL и Django ORM без ручного SQL;
- Swagger и ReDoc;
- Docker, Docker Compose и Nginx;
- тесты с обязательным покрытием не менее 75%;
- CI-проверка Ruff, миграций и pytest;
- отдельное бизнес-обоснование в [BUSINESS_VALUE.md](BUSINESS_VALUE.md);
- отчет повторного аудита в [AUDIT_REPORT.md](AUDIT_REPORT.md).

## Стек

Python 3.12, Django 5.2, Django REST Framework, PostgreSQL, Celery, Redis, Simple JWT, drf-spectacular, Gunicorn, Nginx, Docker Compose, pytest, Ruff.

## Структура

```text
config/       настройки Django, URL, Celery
users/        пользовательская модель и регистрация
documents/    документы, API, admin, задачи, сервисы, тесты
nginx/        reverse proxy и раздача static/media
scripts/      entrypoint контейнера
.github/      CI workflow
```

## Быстрый запуск в Docker

1. Скопируйте шаблон переменных:

```bash
cp .env.template .env
```

2. Измените как минимум `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL` и SMTP-параметры.

3. Запустите проект:

```bash
docker compose up --build -d
```

4. Создайте администратора:

```bash
docker compose exec web python manage.py createsuperuser
```

5. Откройте:

- API документов: `http://localhost/api/documents/`
- Swagger: `http://localhost/api/docs/`
- ReDoc: `http://localhost/api/redoc/`
- Django Admin: `http://localhost/admin/`

## Локальный запуск без Docker

Требуются PostgreSQL и Redis.

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell
pip install -r requirements.txt
cp .env.template .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

В отдельном терминале:

```bash
celery -A config worker --loglevel=info
```

Django читает переменные окружения процесса. При локальном запуске экспортируйте их из `.env` удобным для вашей ОС способом или настройте IDE.

## API

### Регистрация

```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "student",
  "email": "student@example.com",
  "password": "StrongPass123!"
}
```

### Получение JWT

```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "student",
  "password": "StrongPass123!"
}
```

### Загрузка документа

```bash
curl -X POST http://localhost/api/documents/ \
  -H "Authorization: Bearer <access_token>" \
  -F "title=Договор" \
  -F "file=@contract.pdf"
```

### Маршруты документов

| Метод | URL | Назначение |
|---|---|---|
| GET | `/api/documents/` | список собственных документов |
| POST | `/api/documents/` | загрузить документ |
| GET | `/api/documents/{id}/` | получить собственный документ |
| DELETE | `/api/documents/{id}/` | удалить собственный документ `pending` |
| GET | `/api/documents/{id}/download/` | безопасно скачать документ |

Статус, владелец, проверяющий и даты обработки назначаются сервером и доступны только для чтения через API. Файлы не публикуются через открытый `/media/`: скачивание требует JWT или активную административную сессию.

## Модерация

1. Администратор входит в `/admin/`.
2. Открывает список документов.
3. Выбирает записи со статусом `pending`.
4. Запускает действие «Подтвердить выбранные документы» или «Отклонить выбранные документы».
5. Сервис фиксирует администратора и время решения.
6. Celery отправляет пользователю письмо.

Для индивидуальной причины отклонения предварительно заполните поле `rejection_reason` в карточке документа. Если поле пустое, массовое действие использует текст «Отклонено администратором.».

## Email

Для разработки можно использовать консольный backend:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Для реальной отправки настройте SMTP в `.env.template`. При временной ошибке задачи Celery повторяются с экспоненциальной задержкой до трех раз.

## Доверенные домены и IP

```env
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,203.0.113.10
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
```

В production используйте HTTPS и `DEBUG=False`.

## Тесты и покрытие

```bash
pytest
```

Настройки в `pytest.ini` и `.coveragerc` завершают тесты ошибкой, если покрытие прикладного кода ниже 75%. Автоматические миграции, тесты и серверные точки входа ASGI/WSGI исключены из расчета.

Отдельные проверки:

```bash
python scripts/audit_project.py
ruff check .
flake8 .
python manage.py makemigrations --check --dry-run
```


## Комментарии и стиль кода

Прикладные Python-модули содержат русские модульные docstring, описания
классов и функций, а также комментарии перед нетривиальными участками логики.
Комментарии оформлены полными предложениями, начинаются с `# ` и не дублируют
очевидные операции. Автоматически созданные миграции не редактируются вручную
и исключены из проверок форматирования. Стиль контролируют Ruff и Flake8.

## Проверка Docker Compose

```bash
docker compose config
```

Просмотр логов:

```bash
docker compose logs -f web celery
```

Остановка:

```bash
docker compose down
```

Полное удаление данных PostgreSQL, Redis и файлов:

```bash
docker compose down -v
```

## Бизнес-аспекты

Расчет экономии времени, финансового эффекта, окупаемости, KPI, рисков и сценариев приведен в `BUSINESS_VALUE.md`. Все цифры помечены как сценарные допущения и должны быть заменены фактическими данными организации при защите.

## Возможные улучшения

- S3/MinIO вместо локального media volume;
- антивирусная проверка файлов;
- журнал всех переходов статуса;
- отдельный интерфейс модератора;
- webhook и push-уведомления;
- SLA-метрики и Prometheus/Grafana;
- электронная подпись и OCR;
- повторная загрузка исправленного документа.
