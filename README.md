# CraftManager API

REST API для учёта handmade-производства: изделия и их себестоимость, склад материалов, продажи по каналам (в т.ч. ярмарки), расходы, финансовый дашборд.

Бэкенд для [craftmanager-ui](https://github.com/AnnVatlina/craftmanager-ui). Вся бизнес-логика и данные живут здесь — фронтенд тонкий.

## Документация

Подробная документация — в [`docs/`](docs/):

- [`docs/BUSINESS.md`](docs/BUSINESS.md) — реализованные бизнес-правила и сценарии, включая то, что осознанно не сделано
- [`docs/DOMAIN.md`](docs/DOMAIN.md) — модель данных: таблицы, поля, связи
- [`docs/API.md`](docs/API.md) — контракт эндпоинтов (точные схемы — на `/docs` запущенного сервера)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — стек, структура, деплой, известные несоответствия

## Стек технологий

- **Backend:** FastAPI (Python 3.11), SQLAlchemy 2.0 (async)
- **Database:** PostgreSQL 16
- **Auth:** JWT (python-jose)
- **Testing:** pytest-asyncio
- **Deployment:** Docker, Railway (backend) + GitHub Pages (frontend)

## Локальная разработка

```bash
git clone https://github.com/AnnVatlina/craftmanager-api.git
cd craftmanager-api

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
docker-compose up -d            # Postgres на 5432, тестовый на 5433

uvicorn app.main:app --reload   # схема БД создаётся автоматически при старте
```

API — `http://localhost:8000`, Swagger UI — `http://localhost:8000/docs`.

> Схема БД создаётся через `Base.metadata.create_all` при старте приложения, а не через `alembic upgrade head` — Alembic сконфигурирован, но версий миграций в репозитории нет. Подробности — [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#инициализация-схемы).

## Структура проекта

```
craftmanager-api/
├── app/
│   ├── models/          # SQLAlchemy ORM модели
│   ├── schemas/         # Pydantic схемы для валидации
│   ├── routers/         # API маршруты
│   ├── services/        # Бизнес-логика (себестоимость, суммы продаж)
│   ├── auth/            # JWT и аутентификация
│   ├── main.py          # FastAPI приложение, lifespan
│   ├── config.py        # Конфигурация
│   └── database.py      # Подключение БД
├── alembic/              # Настроен, миграций пока нет
├── tests/                # pytest
├── docs/                 # Документация (см. выше)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Тестирование

```bash
pytest -v
```

Покрывает: регистрацию/вход, изоляцию пользователей, CRUD по всем сущностям, расчётные поля (себестоимость, суммы), списание/восстановление остатков при продаже, подготовку к ярмарке.

## Развёртывание

### Railway (backend)

1. Создайте проект на [Railway](https://railway.app), подключите репозиторий и Postgres-плагин.
2. Переменные окружения: `DATABASE_URL` (Railway подставит сам при подключении БД), `SECRET_KEY` (`openssl rand -hex 32`), `CORS_ORIGINS` — URL фронтенда.
3. Деплой — автоматически при push в `main` (`railway.toml`).

### Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | PostgreSQL, `postgres://`/`postgresql://` нормализуются в `postgresql+asyncpg://` | `postgresql+asyncpg://craft_user:craft_pass@localhost:5432/craftmanager` |
| `SECRET_KEY` | Секрет для подписи JWT | `test-secret-key` — обязательно сменить в проде |
| `ALGORITHM` | Алгоритм JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access-токена | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh-токена | `30` |
| `CORS_ORIGINS` | Разрешённые origins через запятую | `http://localhost:5173` |

## Лицензия

MIT
