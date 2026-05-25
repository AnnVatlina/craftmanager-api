# CraftManager — Техническая документация

## Содержание

1. [Обзор системы](#1-обзор-системы)
2. [Технологический стек](#2-технологический-стек)
3. [Структура проекта](#3-структура-проекта)
4. [База данных](#4-база-данных)
5. [API Reference](#5-api-reference)
6. [Аутентификация](#6-аутентификация)
7. [Фронтенд](#7-фронтенд)
8. [Деплой](#8-деплой)
9. [Локальная разработка](#9-локальная-разработка)
10. [Тестирование](#10-тестирование)

---

## 1. Обзор системы

CraftManager — веб-приложение для учёта handmade-бизнеса. Система позволяет вести учёт изделий и материалов, регистрировать продажи, отслеживать расходы и анализировать финансовые показатели.

**Архитектура:** клиент-серверная SPA.

```
[Browser SPA] ──HTTPS──> [FastAPI Backend on Railway]
                                    │
                              [PostgreSQL DB]
```

- Фронтенд: статический сайт на GitHub Pages, общается с бекендом через REST API.
- Бекенд: FastAPI-приложение на Railway, использует PostgreSQL.
- Данные строго изолированы по пользователям: каждая запись в БД содержит `user_id`.

---

## 2. Технологический стек

### Бекенд

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.11 | Рантайм |
| FastAPI | 0.104.1 | Web-фреймворк |
| SQLAlchemy | 2.0.23 | ORM (async) |
| asyncpg | 0.29.0 | Async PostgreSQL драйвер |
| psycopg2-binary | 2.9.9 | Sync драйвер для Alembic |
| Alembic | 1.13.1 | Миграции БД |
| Pydantic | 2.5.0 | Валидация данных, схемы |
| pydantic-settings | 2.1.0 | Конфигурация из env |
| python-jose | 3.3.0 | JWT токены |
| passlib + bcrypt | 1.7.4 + 3.2.2 | Хэширование паролей |
| uvicorn | 0.24.0 | ASGI-сервер |

### Фронтенд

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Vue 3 | 3.4.21 | UI-фреймворк |
| Vue Router | 4.3.0 | Клиентский роутинг |
| Vite | 5.2.0 | Сборщик |

### Инфраструктура

| Сервис | Назначение |
|--------|------------|
| Railway | Хостинг бекенда + PostgreSQL |
| GitHub Pages | Хостинг фронтенда |
| GitHub Actions | CI/CD для фронтенда |
| Docker | Контейнеризация бекенда |

---

## 3. Структура проекта

```
ann-craft/
├── backend/
│   ├── app/
│   │   ├── main.py              # Точка входа FastAPI, lifespan, CORS, роутеры
│   │   ├── config.py            # Pydantic Settings, нормализация DATABASE_URL
│   │   ├── database.py          # AsyncEngine, сессия, Base
│   │   ├── auth/
│   │   │   ├── utils.py         # bcrypt-хэширование, JWT create/decode
│   │   │   └── dependencies.py  # get_current_user dependency
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── material.py
│   │   │   ├── product_material.py
│   │   │   ├── sale.py
│   │   │   ├── sale_item.py
│   │   │   ├── sales_channel.py
│   │   │   ├── expense.py
│   │   │   └── user_setting.py
│   │   ├── schemas/             # Pydantic-схемы (In/Out) для каждой модели
│   │   ├── routers/             # FastAPI-роутеры (по одному на сущность)
│   │   └── services/
│   │       ├── product.py       # calc_product_cost_price()
│   │       └── sale.py          # calc_sale_total_amount()
│   ├── alembic/
│   │   ├── env.py               # Конфиг Alembic с _sync_url helper
│   │   └── versions/            # Файлы миграций
│   ├── tests/
│   │   ├── conftest.py          # Фикстуры: тестовая БД, клиент, пользователь, данные
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   ├── test_materials.py
│   │   ├── test_sales.py
│   │   ├── test_expenses.py
│   │   ├── test_channels.py
│   │   └── test_dashboard.py
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── main.js              # Инициализация Vue + Router
    │   ├── App.vue              # Корневой компонент
    │   ├── style.css            # Глобальные стили
    │   ├── api/
    │   │   ├── client.js        # HTTP-клиент, auto-refresh токена, обработка ошибок
    │   │   ├── auth.js
    │   │   ├── products.js
    │   │   ├── materials.js
    │   │   ├── sales.js
    │   │   ├── channels.js
    │   │   ├── expenses.js
    │   │   ├── dashboard.js
    │   │   └── settings.js
    │   ├── stores/
    │   │   ├── auth.js          # isAuthenticated, logout()
    │   │   └── settings.js      # currency, categories, загрузка из API
    │   ├── components/
    │   │   ├── AppLayout.vue    # Сайдбар, мобильная шапка, <router-view>
    │   │   └── BaseModal.vue    # Переиспользуемый модальный диалог
    │   ├── router/
    │   │   └── index.js         # Маршруты, навигационный guard
    │   └── views/
    │       ├── LoginView.vue
    │       ├── DashboardView.vue
    │       ├── ProductsView.vue
    │       ├── ProductDetailView.vue
    │       ├── MaterialsView.vue
    │       ├── SalesView.vue
    │       ├── ChannelsView.vue
    │       ├── ExpensesView.vue
    │       └── SettingsView.vue
    ├── .github/workflows/
    │   └── deploy.yml           # GitHub Actions: build → gh-pages
    └── vite.config.js           # base: '/craftmanager-ui/'
```

---

## 4. База данных

### Схема

```
users
  id UUID PK
  email VARCHAR UNIQUE NOT NULL
  hashed_password VARCHAR NOT NULL
  created_at DATETIME

products
  id UUID PK
  user_id UUID FK→users CASCADE
  name VARCHAR NOT NULL
  description TEXT
  category VARCHAR
  sale_price NUMERIC(10,2) NOT NULL
  stock_qty INTEGER DEFAULT 0
  created_at DATETIME
  [INDEX: user_id]

materials
  id UUID PK
  user_id UUID FK→users CASCADE
  name VARCHAR NOT NULL
  unit VARCHAR NOT NULL          -- г | кг | м | мл | шт
  price_per_unit NUMERIC(10,4) NOT NULL
  stock_qty NUMERIC(10,3) DEFAULT 0
  created_at DATETIME
  [INDEX: user_id]

product_materials
  id UUID PK
  user_id UUID FK→users CASCADE
  product_id UUID FK→products CASCADE
  material_id UUID FK→materials SET NULL
  quantity NUMERIC(10,3) NOT NULL
  [UNIQUE: (product_id, material_id)]

sales_channels
  id UUID PK
  user_id UUID FK→users CASCADE
  name VARCHAR NOT NULL
  type VARCHAR NOT NULL           -- ярмарка | лс | другое
  event_date DATE
  location VARCHAR
  notes TEXT
  created_at DATETIME

sales
  id UUID PK
  user_id UUID FK→users CASCADE
  channel_id UUID FK→sales_channels SET NULL
  sale_date DATE NOT NULL
  notes TEXT
  created_at DATETIME
  [INDEX: user_id, channel_id, sale_date]

sale_items
  id UUID PK
  user_id UUID FK→users CASCADE
  sale_id UUID FK→sales CASCADE
  product_id UUID FK→products SET NULL
  quantity INTEGER NOT NULL
  price NUMERIC(10,2) NOT NULL
  [INDEX: user_id, sale_id, product_id]

expenses
  id UUID PK
  user_id UUID FK→users CASCADE
  expense_date DATE NOT NULL
  amount NUMERIC(10,2) NOT NULL
  category VARCHAR
  description TEXT
  created_at DATETIME
  [INDEX: user_id, expense_date]

user_settings
  id UUID PK
  user_id UUID FK→users CASCADE UNIQUE
  currency VARCHAR DEFAULT 'Br'
  categories TEXT                 -- CSV строка категорий изделий
  expense_categories TEXT         -- CSV строка категорий расходов
  material_units TEXT             -- CSV строка единиц измерения
  low_stock_threshold INTEGER DEFAULT 5
```

### Инициализация схемы

При старте приложения в `lifespan` выполняется `Base.metadata.create_all` — таблицы создаются автоматически, если их нет. Alembic используется для инкрементальных миграций при деплое (`alembic upgrade head`).

### Изоляция данных

Все пользовательские данные фильтруются по `user_id` на уровне каждого запроса. Нет глобальных таблиц, которые делятся между пользователями.

---

## 5. API Reference

Базовый URL: `https://<railway-domain>/api/v1`

Все эндпоинты (кроме `/auth/*` и `/health`) требуют заголовка:
```
Authorization: Bearer <access_token>
```

Все ответы обёрнуты в `{"data": ...}`. Списки дополнительно содержат `{"data": [...], "meta": {...}}`.

### Auth

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация. Body: `{email, password}` |
| POST | `/auth/login` | Вход. Body: `{email, password}`. Возвращает `access_token`, `refresh_token` |
| POST | `/auth/refresh` | Обновление токена. Body: `{refresh_token}` |

### Products

| Метод | Путь | Параметры | Описание |
|-------|------|-----------|----------|
| GET | `/products` | `category`, `in_stock`, `page`, `per_page` | Список изделий с пагинацией. Meta: `total`, `pages`, `total_stock_value` |
| POST | `/products` | — | Создать изделие |
| GET | `/products/{id}` | — | Изделие + состав материалов + себестоимость |
| PUT | `/products/{id}` | — | Обновить изделие |
| DELETE | `/products/{id}` | — | Удалить изделие |
| GET | `/products/{id}/materials` | — | Состав материалов |
| POST | `/products/{id}/materials` | — | Добавить материал в состав |
| DELETE | `/products/{id}/materials/{mid}` | — | Удалить материал из состава |

### Materials

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/materials` | Список материалов |
| POST | `/materials` | Создать материал |
| GET | `/materials/{id}` | Детали материала |
| PUT | `/materials/{id}` | Обновить |
| DELETE | `/materials/{id}` | Удалить |
| POST | `/materials/{id}/restock` | Пополнить запас. Body: `{quantity, price_per_unit?}` |

### Sales

| Метод | Путь | Параметры | Описание |
|-------|------|-----------|----------|
| GET | `/sales` | `channel_id`, `date_from`, `date_to` | Список продаж |
| POST | `/sales` | — | Создать продажу (автоматически списывает `stock_qty`) |
| GET | `/sales/{id}` | — | Продажа + позиции + канал |
| PUT | `/sales/{id}` | — | Обновить заголовок продажи |
| DELETE | `/sales/{id}` | — | Удалить (восстанавливает `stock_qty`) |

### Sales Channels

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/channels` | Список каналов |
| POST | `/channels` | Создать канал |
| GET | `/channels/{id}` | Канал + связанные продажи |
| PUT | `/channels/{id}` | Обновить |
| DELETE | `/channels/{id}` | Удалить |

### Expenses

| Метод | Путь | Параметры | Описание |
|-------|------|-----------|----------|
| GET | `/expenses` | `category`, `date_from`, `date_to` | Список расходов |
| POST | `/expenses` | — | Создать расход |
| GET | `/expenses/{id}` | — | Детали |
| PUT | `/expenses/{id}` | — | Обновить |
| DELETE | `/expenses/{id}` | — | Удалить |

### Dashboard

| Метод | Путь | Параметры | Описание |
|-------|------|-----------|----------|
| GET | `/dashboard/summary` | `date_from`, `date_to` | Выручка, расходы, прибыль |
| GET | `/dashboard/top-products` | `date_from`, `date_to`, `limit` | Топ изделий по выручке |
| GET | `/dashboard/low-stock` | `threshold` | Изделия с низким остатком |

### Settings

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/settings` | Настройки пользователя (создаются при первом запросе) |
| PUT | `/settings` | Обновить настройки |

### Health

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | `{"status": "ok"}` — не требует авторизации |

---

## 6. Аутентификация

Используется схема JWT с двумя токенами:

- **access_token** — короткоживущий (30 мин), передаётся в заголовке `Authorization: Bearer`.
- **refresh_token** — долгоживущий (7 дней), используется для получения нового access_token.

Токены хранятся в `localStorage` фронтенда. HTTP-клиент (`api/client.js`) перехватывает ответ `401`, автоматически вызывает `/auth/refresh` и повторяет исходный запрос.

Пароли хэшируются через bcrypt (passlib). JWT подписываются алгоритмом HS256, секрет задаётся через `JWT_SECRET_KEY`.

---

## 7. Фронтенд

### Роутинг

Vue Router 4 с hash history (`#/`). Навигационный guard проверяет наличие `access_token` в `localStorage`. Неавторизованные пользователи перенаправляются на `/login`.

```
/login           → LoginView (публичный)
/                → DashboardView
/products        → ProductsView
/products/:id    → ProductDetailView
/materials       → MaterialsView
/sales           → SalesView
/channels        → ChannelsView
/expenses        → ExpensesView
/settings        → SettingsView
```

### Хранилища (stores)

`settingsStore` — реактивный объект, загружает настройки из API при старте (`AppLayout.vue → onMounted`). Хранит `currency`, `categories`, `expense_categories`, `material_units`, `low_stock_threshold`. Все компоненты используют его через `computed(() => settingsStore.currency)` и т.д.

`authStore` — хранит логику выхода (`logout()` очищает `localStorage` и перенаправляет на `/login`).

### Сборка и деплой

```
VITE_API_URL=https://...railway.app npm run build
```

Переменная `VITE_API_URL` подставляется в `api/client.js` во время сборки. Vite собирает приложение в `dist/`, GitHub Actions публикует в ветку `gh-pages`, GitHub Pages отдаёт файлы по адресу `https://annvatlina.github.io/craftmanager-ui/`.

Base path в `vite.config.js` установлен как `/craftmanager-ui/` — это обязательно для корректной работы на GitHub Pages в подпути.

---

## 8. Деплой

### Бекенд (Railway)

**Dockerfile** — сборка Python-образа, копирует `requirements.txt` и `app/`, устанавливает зависимости.

**railway.toml:**
```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "sh -c 'alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT'"
```

`$PORT` раскрывается через `sh -c`, т.к. Railway передаёт порт как переменную среды.

**Переменные окружения на Railway:**

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | PostgreSQL URL (Railway подставляет автоматически при подключении БД) |
| `JWT_SECRET_KEY` | Секрет для подписи JWT |
| `JWT_ALGORITHM` | Алгоритм JWT (по умолчанию `HS256`) |
| `CORS_ORIGINS` | Список разрешённых источников через запятую |

`DATABASE_URL` нормализуется в `config.py`: `postgres://` и `postgresql://` приводятся к `postgresql+asyncpg://` для asyncpg. Alembic использует `_sync_url()` хелпер для конвертации обратно в синхронный формат.

### Фронтенд (GitHub Actions → GitHub Pages)

Файл `.github/workflows/deploy.yml`:
1. Триггер: push в ветку `main`
2. `npm install` → `npm run build` (с переменной `VITE_API_URL` из GitHub Secrets)
3. Публикация `dist/` в ветку `gh-pages` через `peaceiris/actions-gh-pages@v3`

GitHub Pages настроен на ветку `gh-pages`.

---

## 9. Локальная разработка

### Требования

- Python 3.11+
- Node.js 20+
- PostgreSQL (локальный или через Docker)

### Бекенд

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Создать .env файл:
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/craftmanager
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
EOF

alembic upgrade head
uvicorn app.main:app --reload
```

API доступен на `http://localhost:8000`.  
Swagger UI: `http://localhost:8000/docs`.

### Фронтенд

```bash
cd frontend
npm install

# Создать .env.local:
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Приложение доступно на `http://localhost:5173`.

---

## 10. Тестирование

Тесты используют `pytest-asyncio` в режиме `asyncio_mode = auto` (задан в `pyproject.toml`).

### Запуск

```bash
cd backend

# Установить тестовую БД (отдельная от основной):
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/craftmanager_test

pytest -v
```

### Конфигурация фикстур (`conftest.py`)

- `db` — асинхронная сессия с `create_all` перед тестом и `drop_all` после.
- `client` — `AsyncClient` (httpx) с тестовым приложением.
- `user` + `auth_headers` — зарегистрированный пользователь и заголовок с его токеном.
- `product`, `material`, `channel`, `expense` — созданные тестовые записи.

### Покрытие

Тесты охватывают: регистрацию/вход, CRUD продуктов и материалов, пополнение запасов, создание продаж со списанием остатков, удаление продаж с восстановлением остатков, CRUD каналов, CRUD расходов, дашборд.
