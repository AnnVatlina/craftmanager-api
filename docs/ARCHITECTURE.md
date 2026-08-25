# Архитектура

## Обзор

CraftManager — учётная система для мастера handmade-товаров: изделия и их себестоимость, склад материалов, продажи по каналам, расходы, финансовый дашборд.

```
[Vue 3 SPA, craftmanager-ui] ──HTTPS/JSON──> [FastAPI, craftmanager-api] ──> [PostgreSQL]
```

Два отдельных репозитория, не монорепо:
- **craftmanager-api** — бэкенд, источник истины по бизнес-логике и данным.
- **craftmanager-ui** — тонкий SPA-клиент, вся логика (себестоимость, списание остатков, изоляция по пользователю) — на бэкенде.

Данные изолированы по пользователю: каждая таблица, кроме `users`, содержит `user_id`, фильтрация — на уровне каждого запроса в роутерах.

## Технологический стек

### Бэкенд (этот репозиторий)

| Компонент | Версия | Назначение |
|---|---|---|
| Python | 3.11 | |
| FastAPI | 0.104.1 | |
| SQLAlchemy | 2.0.23 | ORM, async |
| asyncpg | 0.29.0 | async-драйвер Postgres |
| psycopg2-binary | 2.9.9 | sync-драйвер для Alembic (см. ниже — фактически не используется) |
| Alembic | 1.13.1 | сконфигурирован, но без версий миграций — см. [Инициализация схемы](#инициализация-схемы) |
| Pydantic / pydantic-settings | 2.5.0 / 2.1.0 | схемы, конфиг из env |
| python-jose | 3.3.0 | JWT |
| passlib + bcrypt | хэширование паролей |
| Pillow | 10.1.0 | ресайз/сжатие фото изделий |
| pytest + pytest-asyncio + httpx | тесты |

### Фронтенд (craftmanager-ui)

| Компонент | Версия |
|---|---|
| Vue | 3.4.21 |
| Vue Router | 4.3.0 (hash history) |
| Vite | 5.2.0 |

Без стейт-менеджера (Pinia/Vuex) — состояние в двух reactive-объектах (`authStore`, `settingsStore`), без внешней библиотеки компонентов.

### Инфраструктура

| Сервис | Назначение |
|---|---|
| Railway | Хостинг бэкенда + managed PostgreSQL |
| GitHub Pages | Хостинг статики фронтенда |
| GitHub Actions | CI обоих репозиториев, деплой фронтенда на Pages |
| Docker | Контейнеризация бэкенда (`Dockerfile`, `docker-compose.yml` для локальной БД) |

## Структура репозитория (craftmanager-api)

```
craftmanager-api/
├── app/
│   ├── main.py              # FastAPI app, lifespan (создание схемы + ad hoc миграции), CORS, роутеры
│   ├── config.py             # Settings (pydantic-settings), нормализация DATABASE_URL
│   ├── database.py           # AsyncEngine, session factory, Base
│   ├── auth/
│   │   ├── utils.py           # bcrypt, JWT create/decode
│   │   └── dependencies.py    # get_current_user
│   ├── models/                # SQLAlchemy ORM — см. docs/DOMAIN.md
│   ├── schemas/                # Pydantic In/Out схемы, по одной на сущность
│   ├── routers/                 # по роутеру на сущность, см. docs/API.md
│   └── services/
│       ├── product.py            # calc_product_cost_price()
│       └── sale.py               # calc_sale_total_amount()
├── alembic/
│   ├── env.py                # настроен, конвертирует async URL в sync
│   └── versions/              # пусто — миграций нет, см. ниже
├── tests/                     # pytest, по файлу на роутер (buyers — пустая заглушка)
├── docs/                      # эта документация
├── Dockerfile
├── docker-compose.yml          # локальный Postgres + тестовый Postgres на 5433
├── railway.toml
└── requirements.txt
```

Фронтенд (`craftmanager-ui`) — отдельный репозиторий, структура описана в его собственном README.

## База данных

Полная схема — [DOMAIN.md](DOMAIN.md).

### Инициализация схемы

Здесь реализация **расходится** с тем, что заявляет `requirements.txt` и `railway.toml`. По факту:

1. При старте приложения (`lifespan` в `app/main.py`) выполняется `Base.metadata.create_all` — создаёт все таблицы, если их ещё нет, исходя из текущего состояния моделей.
2. Дополнительно там же выполняются несколько `ALTER TABLE` / `DO $$ ... END $$` блоков сырого SQL — ручные one-time миграции для изменений, которые `create_all` не покрывает (добавление колонки в существующую таблицу, перенос данных из `buyer_id` в `channel_id`, исправление сохранённых цен материалов). Каждая обёрнута в проверку `IF NOT EXISTS`, так что безопасно выполняется на каждом старте.
3. `alembic/versions/` — **пустая директория**. Alembic сконфигурирован (`env.py` настроен и корректен), но не содержит ни одной ревизии. `railway.toml` запускает `alembic upgrade head` перед стартом сервера — команда завершается успешно, но ничего не делает, потому что применять нечего.

**На практике:** миграции схемы этого проекта — это `Base.metadata.create_all` (для нового) + ad hoc SQL в `main.py` (для изменений существующей БД). Alembic присутствует в стеке, но не является рабочим механизмом миграций. Если это осознанный выбор — стоит либо убрать Alembic из зависимостей и `railway.toml`, либо начать действительно вести миграции через него; смешанное состояние — источник путаницы для любого, кто прочитает `README.md`/`requirements.txt` и ожидает найти историю миграций в `alembic/versions/`.

## Аутентификация

JWT, два токена: `access_token` (30 мин, `Authorization: Bearer`) и `refresh_token` (30 дней, обмен через `/auth/refresh`). Оба — stateless, не хранятся и не отзываются на сервере; логаут — только удаление токенов на клиенте. Пароли — bcrypt через passlib. Секрет и алгоритм — `SECRET_KEY` / `ALGORITHM` в `app/config.py`.

⚠️ Несоответствие имени переменной: `TECHNICAL.md` (устаревший, см. ниже) и часть внешней документации ссылались на `JWT_SECRET_KEY` — актуальное имя переменной окружения `SECRET_KEY` (см. `app/config.py`, `.env.example`).

## Деплой

### Бэкенд (Railway)

`railway.toml`:
```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "sh -c 'alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT'"
```

Переменные окружения на Railway: `DATABASE_URL` (подставляется автоматически при подключении Postgres-плагина), `SECRET_KEY`, `CORS_ORIGINS`. `DATABASE_URL` нормализуется в `config.py` (`postgres://`/`postgresql://` → `postgresql+asyncpg://`).

### Фронтенд (GitHub Pages)

Собирается Vite (`base: '/craftmanager-ui/'` обязателен для GitHub Pages в подпути) с `VITE_API_URL`, публикуется в ветку `gh-pages` через GitHub Actions.

## Локальная разработка

```bash
git clone https://github.com/AnnVatlina/craftmanager-api.git
cd craftmanager-api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker-compose up -d          # Postgres на 5432, тестовый на 5433
uvicorn app.main:app --reload # схема создаётся автоматически при старте
```

`http://localhost:8000/docs` — Swagger UI.

Фронтенд — см. README в `craftmanager-ui`.

## Тестирование

```bash
pytest -v
```

`tests/conftest.py` поднимает таблицы на тестовой БД (`craftmanager_test`, порт 5433 из `docker-compose.yml`) через `create_all`/`drop_all` вокруг каждого теста, создаёт пользователя и токен. По файлу теста на роутер: `test_auth`, `test_products`, `test_materials`, `test_sales`, `test_expenses`, `test_channels`, `test_fair_prep`. `test_buyers.py` — пустая заглушка (сущность устарела). Нет отдельных тестов на `dashboard`, `material_purchases`, `export`/`import`.

## Известные несоответствия документации ↔ код (на момент написания)

- Прежний `README.md` описывал структуру `cd backend` и `docker-compose.prod.yml` — ни того, ни другого нет в этом репозитории (плоская структура, один `docker-compose.yml`). Исправлено в актуальном README.
- Прежний `TECHNICAL.md` описывал монорепо с папками `backend/`/`frontend/` — на деле это два отдельных репозитория. `TECHNICAL.md` также не упоминает `sales_channels`, `fair_prep`, `material_purchase`, экспорт/импорт, загрузку фото — написан до этих фич и требует замены на этот файл + [DOMAIN.md](DOMAIN.md) + [BUSINESS.md](BUSINESS.md) + [API.md](API.md).
