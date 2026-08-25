# Модель данных

Описывает фактическую схему БД, как её создаёт `Base.metadata.create_all` из моделей в `app/models/`. Про то, как схема попадает в БД (и почему это не Alembic-миграции), см. [ARCHITECTURE.md](ARCHITECTURE.md#инициализация-схемы).

Все таблицы, кроме `users`, имеют `user_id` и фильтруются по нему на уровне каждого запроса — изоляция по пользователю сквозная, общих данных между пользователями нет.

## ER-диаграмма

```
users
  │ 1
  │
  ├──* products ──────────┬──* product_materials *──┬── materials ──* material_purchases
  │                       │                          │
  │                       └──* sale_items            │
  │                              │ *                 │
  ├──* sales_channels ──* sales ─┘                    │
  │        │ 1                                        │
  │        └──* fair_items ───────────────────────────┘ (planned_qty vs product.stock_qty)
  │
  ├──* expenses
  ├──* user_settings (1:1)
  └──* buyers (устаревшая сущность, см. ниже)
```

## Таблицы

### users
| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| email | VARCHAR UNIQUE NOT NULL | |
| hashed_password | VARCHAR NOT NULL | bcrypt |
| created_at | DATETIME | |

### products
| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| name | VARCHAR NOT NULL | |
| description | TEXT | |
| category | VARCHAR | свободная строка, набор подсказок хранится в `user_settings.categories` |
| sale_price | NUMERIC(10,2) NOT NULL | цена продажи |
| stock_qty | INTEGER DEFAULT 0 | остаток готовых изделий |
| photo | TEXT | base64 JPEG, см. [BUSINESS.md](BUSINESS.md#фото-изделия) |
| created_at | DATETIME | |

Индекс: `user_id`.

### materials
| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| name | VARCHAR NOT NULL | |
| unit | VARCHAR NOT NULL | г / кг / м / мл / шт — набор хранится в `user_settings.material_units` |
| price_per_unit | NUMERIC(10,4) NOT NULL | текущая цена за единицу (средневзвешенная, см. BUSINESS.md) |
| stock_qty | NUMERIC(10,3) DEFAULT 0 | остаток на складе |
| created_at | DATETIME | |

Индекс: `user_id`. Есть колонка `price_unit_fixed BOOLEAN`, добавленная миграцией в `main.py` — техническая метка "цена уже приведена к цене за единицу", не используется бизнес-логикой напрямую, только one-time миграцией.

### product_materials
Состав изделия — сколько какого материала уходит на одну единицу изделия.

| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| product_id | UUID FK→products CASCADE | |
| material_id | UUID FK→materials CASCADE | |
| quantity | NUMERIC(10,4) NOT NULL | расход материала на 1 ед. изделия |

Ограничение: `UNIQUE(product_id, material_id)` — материал нельзя добавить в состав дважды, только менять количество.

Удаление материала каскадно удаляет все `product_materials`, где он использован (`ON DELETE CASCADE`) — состав изделий "теряет" материал молча, без предупреждения на бэкенде. Себестоимость такого изделия при следующем запросе просто пересчитается без учёта удалённого материала.

### material_purchases
Журнал пополнений склада материалов — источник данных для дашборда (`material_expenses`) и экспорта.

| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| material_id | UUID FK→materials CASCADE | |
| purchased_at | DATE NOT NULL | |
| quantity | NUMERIC(10,3) NOT NULL | |
| price_per_unit | NUMERIC(10,4) NOT NULL | цена в момент этой закупки |
| total_cost | NUMERIC(12,2) NOT NULL | `quantity * price_per_unit`, хранится отдельно ради быстрой агрегации в дашборде |
| created_at | DATETIME | |

Запись создаётся автоматически при создании материала с `stock_qty > 0` и при каждом `POST /materials/{id}/restock` — см. [BUSINESS.md](BUSINESS.md#учёт-закупок-материалов).

### sales_channels
Канал продажи — ярмарка, личные продажи или прочее. Заменил собой сущность `buyers`.

| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| name | VARCHAR NOT NULL | |
| type | VARCHAR NOT NULL DEFAULT 'лс' | `ярмарка` \| `лс` \| `другое` — свободная строка, не enum на уровне БД |
| event_date | DATE | используется в подготовке к ярмарке |
| location | VARCHAR | |
| notes | TEXT | |
| created_at | DATETIME | |

### sales
| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| channel_id | UUID FK→sales_channels **SET NULL** | продажа может существовать без канала |
| sale_date | DATE NOT NULL | |
| notes | TEXT | |
| created_at | DATETIME | |

`total_amount` НЕ хранится в таблице — считается на лету в `calc_sale_total_amount()` как сумма `quantity * price` по позициям.

### sale_items
| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| sale_id | UUID FK→sales CASCADE | |
| product_id | UUID FK→products **SET NULL** | позиция может пережить удаление изделия |
| quantity | INTEGER NOT NULL | |
| price | NUMERIC(10,2) NOT NULL | цена продажи **на момент продажи**, копируется из `product.sale_price`, дальше живёт независимо |

### expenses
| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| category | VARCHAR NOT NULL | свободная строка, набор хранится в `user_settings.expense_categories` |
| amount | NUMERIC(10,2) NOT NULL | |
| description | TEXT | |
| expense_date | DATE NOT NULL | |
| created_at | DATETIME | |

Это **ручные** расходы (аренда, реклама, инструменты). Расходы на материалы не дублируются сюда — они считаются отдельно из `material_purchases`, см. BUSINESS.md.

### user_settings
1:1 с `users`, создаётся лениво при первом `GET /settings`.

| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE UNIQUE | |
| currency | VARCHAR DEFAULT 'Br' | |
| categories | TEXT | CSV-строка категорий изделий |
| expense_categories | TEXT | CSV-строка категорий расходов |
| material_units | TEXT | CSV-строка единиц измерения |
| low_stock_threshold | INTEGER DEFAULT 5 | |

Списки (`categories` и т.д.) хранятся как CSV-строка в одной колонке, а не отдельной таблицей — API отдаёт/принимает их как `List[str]`, конвертация происходит в роутере (`_split` / `",".join`).

### fair_items
Позиция в списке подготовки к ярмарке — сколько изделия нужно взять/доделать для конкретного канала.

| поле | тип | описание |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK→users CASCADE | |
| channel_id | UUID FK→sales_channels CASCADE | |
| product_id | UUID FK→products CASCADE | |
| planned_qty | INTEGER NOT NULL | сколько запланировано взять на ярмарку |

Ограничение: `UNIQUE(channel_id, product_id)`. `stock_qty` и `need_to_make = max(0, planned_qty - stock_qty)` не хранятся, а вычисляются в роутере при каждом запросе.

## Устаревшие/неподключённые сущности

### buyers
Таблица, модель, роутер и Pydantic-схемы существуют (`app/models/buyer.py`, `app/routers/buyers.py`, `app/schemas/buyer.py`), но:

- роутер **не подключён** в `app/main.py` — эндпоинты `/api/v1/buyers/*` не существуют в работающем API;
- `test_buyers.py` — пустой файл-заглушка с комментарием `# Buyers replaced by SalesChannels — see test_channels.py`;
- фронтенд имеет `api/buyers.js` и `views/BuyersView.vue`, но роут `/buyers` не зарегистрирован в `router/index.js` — компонент недостижим из UI.

Таблица и модель оставлены живыми только ради `export`/`import` (см. ниже) — исторические данные о покупателях, накопленные до перехода на `sales_channels`, продолжают экспортироваться и импортироваться как `buyers.csv`, но нигде не редактируются и не отображаются.

**Итог:** `Buyer` — мёртвый код в части CRUD API и UI, но не мёртвые данные — если у пользователя есть записи в этой таблице, они не теряются при экспорте/импорте.

## Экспорт/импорт

`app/routers/export.py` и `app/routers/import_data.py` реализуют полный дамп всех таблиц пользователя в ZIP с CSV-файлами и обратную загрузку. Экспортирует/импортирует все таблицы, включая `buyers` и `fair_items`. Импорт использует `INSERT ... ON CONFLICT DO NOTHING` (кроме `user_settings`, где `DO UPDATE`) — то есть повторный импорт того же файла безопасен, но **не обновляет** существующие записи, только дозаполняет отсутствующие.
