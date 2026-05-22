# CraftManager API

REST API для управления производством и продажей изделий ручной работы.

## Описание

Полнофункциональное API приложение для ремесленника, включающее:
- Управление товарами с автоматическим расчётом себестоимости
- Управление материалами и складом
- Учёт продаж и покупателей
- Отслеживание расходов
- Финансовая аналитика и дашборд

## Стек технологий

- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0
- **Auth:** JWT (python-jose)
- **Migrations:** Alembic
- **Testing:** pytest-asyncio
- **Deployment:** Docker, Railway

## Требования

- Python 3.11+
- PostgreSQL 16+
- Docker (опционально)

## Установка

### Локальная разработка

1. Клонируйте репозиторий и перейдите в папку backend:
```bash
cd backend
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Скопируйте .env.example в .env и обновите переменные:
```bash
cp .env.example .env
```

5. Запустите PostgreSQL с Docker Compose:
```bash
docker-compose up -d
```

6. Примените миграции:
```bash
alembic upgrade head
```

7. Запустите сервер:
```bash
uvicorn app.main:app --reload
```

API будет доступен по адресу `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

## Структура проекта

```
backend/
├── app/
│   ├── models/          # SQLAlchemy ORM модели
│   ├── schemas/         # Pydantic схемы для валидации
│   ├── routers/         # API маршруты
│   ├── services/        # Бизнес-логика
│   ├── auth/            # JWT и аутентификация
│   ├── main.py          # FastAPI приложение
│   ├── config.py        # Конфигурация
│   └── database.py      # Подключение БД
├── alembic/             # Миграции БД
├── tests/               # Тесты
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## API Endpoints

### Аутентификация
- `POST /api/v1/auth/register` — Регистрация
- `POST /api/v1/auth/login` — Вход
- `POST /api/v1/auth/refresh` — Обновление токена

### Товары
- `GET /api/v1/products` — Список товаров
- `POST /api/v1/products` — Создать товар
- `GET /api/v1/products/{id}` — Товар с составом
- `PUT /api/v1/products/{id}` — Обновить товар
- `DELETE /api/v1/products/{id}` — Удалить товар
- `GET /api/v1/products/{id}/materials` — Состав товара
- `POST /api/v1/products/{id}/materials` — Добавить материал
- `DELETE /api/v1/products/{id}/materials/{material_id}` — Удалить материал

### Материалы
- `GET /api/v1/materials` — Список материалов
- `POST /api/v1/materials` — Создать материал
- `GET /api/v1/materials/{id}` — Детали материала
- `PUT /api/v1/materials/{id}` — Обновить материал
- `DELETE /api/v1/materials/{id}` — Удалить материал
- `POST /api/v1/materials/{id}/restock` — Пополнить склад

### Покупатели
- `GET /api/v1/buyers` — Список покупателей
- `POST /api/v1/buyers` — Создать покупателя
- `GET /api/v1/buyers/{id}` — Детали покупателя
- `PUT /api/v1/buyers/{id}` — Обновить покупателя
- `DELETE /api/v1/buyers/{id}` — Удалить покупателя

### Продажи
- `GET /api/v1/sales` — Список продаж
- `POST /api/v1/sales` — Создать продажу
- `GET /api/v1/sales/{id}` — Детали продажи
- `PUT /api/v1/sales/{id}` — Обновить продажу
- `DELETE /api/v1/sales/{id}` — Удалить продажу

### Расходы
- `GET /api/v1/expenses` — Список расходов
- `POST /api/v1/expenses` — Создать расход
- `GET /api/v1/expenses/{id}` — Детали расхода
- `PUT /api/v1/expenses/{id}` — Обновить расход
- `DELETE /api/v1/expenses/{id}` — Удалить расход

### Дашборд
- `GET /api/v1/dashboard/summary` — Финансовая сводка
- `GET /api/v1/dashboard/top-products` — Топ товаров
- `GET /api/v1/dashboard/low-stock` — Товары с низким остатком

## Тестирование

Запустите тесты:
```bash
pytest tests/ -v
```

Покрытие включает:
- Аутентификацию и авторизацию
- CRUD операции
- Изоляцию пользователей
- Расчётные поля
- Списание и восстановление остатков

## Развёртывание

### Railway

1. Создайте проект на [Railway](https://railway.app)
2. Подключите GitHub репозиторий
3. Установите переменные окружения:
   - `DATABASE_URL` — строка подключения к PostgreSQL
   - `SECRET_KEY` — случайная строка (используйте `openssl rand -hex 32`)
   - `CORS_ORIGINS` — URL фронтенда
4. Deployment произойдёт автоматически при push в `main`

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|---------|-------------|
| `DATABASE_URL` | PostgreSQL строка подключения | postgresql+asyncpg://craft_user:craft_pass@localhost:5432/craftmanager |
| `SECRET_KEY` | Секретный ключ для JWT | test-secret-key |
| `ALGORITHM` | Алгоритм JWT | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access токена | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh токена | 30 |
| `CORS_ORIGINS` | Разрешённые origins (через запятую) | http://localhost:5173 |

## Примеры использования

### Регистрация и вход

```bash
# Регистрация
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "craftmaster@example.com",
    "password": "secure_password"
  }'

# Вход
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "craftmaster@example.com",
    "password": "secure_password"
  }'
```

### Создание товара с материалами

```bash
# Создать материал
curl -X POST http://localhost:8000/api/v1/materials \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cotton",
    "unit": "g",
    "price_per_unit": "10.50",
    "stock_qty": "5000"
  }'

# Создать товар
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Plush Bunny",
    "category": "soft",
    "sale_price": "45.00",
    "stock_qty": 20
  }'

# Добавить материал в товар
curl -X POST http://localhost:8000/api/v1/products/PRODUCT_ID/materials \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "MATERIAL_ID",
    "quantity": "100.5"
  }'
```

## Лицензия

MIT
