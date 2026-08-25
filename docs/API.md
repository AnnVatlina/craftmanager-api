# API Reference

Базовый URL: `<host>/api/v1`. Полная интерактивная документация с точными схемами — на `/docs` (Swagger UI) и `/openapi.json` запущенного сервера; здесь — обзорный контракт для чтения без запуска сервера.

Все ответы обёрнуты в `{"data": ...}`. Списки дополнительно содержат `{"data": [...], "meta": {...}}`. Все эндпоинты, кроме `/auth/*` и `/health`, требуют заголовок `Authorization: Bearer <access_token>` и оперируют только данными текущего пользователя.

## Auth — `/auth`

| Метод | Путь | Body | Описание |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` | Регистрация. 400, если email занят. |
| POST | `/auth/login` | `{email, password}` | Возвращает `{access_token, refresh_token, token_type}`. 401 при неверных данных. |
| POST | `/auth/refresh` | `{refresh_token}` | Возвращает новый `access_token`, тот же `refresh_token`. |

## Products — `/products`

| Метод | Путь | Query/Body | Описание |
|---|---|---|---|
| GET | `/products` | `category?, in_stock?, search?, page=1, per_page=20` | Пагинированный список + `cost_price` на каждой записи. `search` — регистронезависимая подстрока по названию. `meta`: `total, page, per_page, pages, total_stock_value`. |
| POST | `/products` | `{name, description?, category?, sale_price, stock_qty?}` | Создание. См. [BUSINESS.md](BUSINESS.md#2-изделия-products) — начальный `stock_qty` не списывает материалы. |
| GET | `/products/{id}` | — | Изделие + состав материалов + `cost_price`. |
| PUT | `/products/{id}` | любое подмножество полей create | Увеличение `stock_qty` списывает материалы состава пропорционально разнице. |
| DELETE | `/products/{id}` | — | Каскадно удаляет `product_materials`; позиции продаж (`sale_items`) остаются, теряя ссылку. |
| GET | `/products/{id}/materials` | — | Состав изделия. |
| POST | `/products/{id}/materials` | `{material_id, quantity}` | 400, если материал уже в составе. |
| DELETE | `/products/{id}/materials/{material_id}` | — | Убрать материал из состава. |
| POST | `/products/{id}/photo` | multipart file | Ресайз до 800×800, JPEG q80, base64 в БД. |
| DELETE | `/products/{id}/photo` | — | Обнуляет фото. |

## Materials — `/materials`

| Метод | Путь | Query/Body | Описание |
|---|---|---|---|
| GET | `/materials` | — | Список материалов пользователя. |
| POST | `/materials` | `{name, unit, price_per_unit, stock_qty?}` | Если `stock_qty > 0`, создаёт запись в `material_purchases`. |
| GET | `/materials/{id}` | — | Детали. |
| PUT | `/materials/{id}` | любое подмножество полей create | Прямое редактирование, не создаёт запись закупки. |
| DELETE | `/materials/{id}` | — | Каскадно удаляет `product_materials` и `material_purchases` этого материала. |
| POST | `/materials/{id}/restock` | `{qty, price_per_unit?, purchased_at?}` | Пополнение; средневзвешенная цена, если `price_per_unit` указан. |

## Sales Channels — `/channels`

| Метод | Путь | Body | Описание |
|---|---|---|---|
| GET | `/channels` | — | Список каналов. |
| POST | `/channels` | `{name, type="лс", event_date?, location?, notes?}` | |
| GET | `/channels/{id}` | — | Канал + связанные продажи (`id, sale_date, total_amount, notes`). |
| PUT | `/channels/{id}` | подмножество полей create | |
| DELETE | `/channels/{id}` | — | Продажи, ссылающиеся на канал, не удаляются (`ON DELETE SET NULL`). |

## Fair Prep — `/fair-prep`

| Метод | Путь | Query/Body | Описание |
|---|---|---|---|
| GET | `/fair-prep/channels` | — | Каналы с `type == "ярмарка"`. |
| GET | `/fair-prep/{channel_id}` | `category?, sort_by?` (`name`\|`category`\|`price_asc`\|`price_desc`) | Список позиций с `need_to_make`, вычисленным на лету, + `summary`. |
| POST | `/fair-prep/{channel_id}/items` | `{product_id, planned_qty}` + те же query | 400, если изделие уже в списке. Возвращает обновлённый список. |
| PUT | `/fair-prep/{channel_id}/items/{item_id}` | `{planned_qty}` + те же query | |
| DELETE | `/fair-prep/{channel_id}/items/{item_id}` | те же query | |

## Sales — `/sales`

| Метод | Путь | Query/Body | Описание |
|---|---|---|---|
| GET | `/sales` | `channel_id?, date_from?, date_to?` | Список с `total_amount`, посчитанным на лету. |
| POST | `/sales` | `{channel_id?, sale_date, notes?, items: [{product_id?, quantity, price}]}` | Списывает `stock_qty` изделий по позициям. |
| GET | `/sales/{id}` | — | Продажа + позиции (с `product_name`) + `channel_name`. |
| PUT | `/sales/{id}` | `{channel_id?, sale_date?, notes?}` | Только "шапка", позиции не редактируются. |
| DELETE | `/sales/{id}` | — | Восстанавливает `stock_qty` изделий по позициям (если изделие ещё существует). |

## Expenses — `/expenses`

| Метод | Путь | Query/Body | Описание |
|---|---|---|---|
| GET | `/expenses` | `category?, date_from?, date_to?` | |
| POST | `/expenses` | `{category, amount, description?, expense_date}` | |
| GET | `/expenses/{id}` | — | |
| PUT | `/expenses/{id}` | подмножество полей create | |
| DELETE | `/expenses/{id}` | — | |

## Dashboard — `/dashboard`

| Метод | Путь | Query | Описание |
|---|---|---|---|
| GET | `/dashboard/summary` | `date_from?, date_to?` | `{total_revenue, total_expenses, manual_expenses, material_expenses, profit}`. См. [BUSINESS.md](BUSINESS.md#8-дашборд) про то, что это не COGS-прибыль. |
| GET | `/dashboard/top-products` | `date_from?, date_to?, limit=10` | `[{product_id, product_name, revenue, quantity}]`, только по существующим изделиям. |
| GET | `/dashboard/low-stock` | `threshold=5` | Изделия с `stock_qty <= threshold`, значение по умолчанию не подтягивается из `user_settings` автоматически. |

## Settings — `/settings`

| Метод | Путь | Body | Описание |
|---|---|---|---|
| GET | `/settings` | — | Создаёт запись с дефолтами при первом вызове. |
| PUT | `/settings` | `{currency?, categories?, expense_categories?, material_units?, low_stock_threshold?}` | Частичное обновление, списки передаются как JSON-массив строк. |

## Export / Import — `/export`, `/import`

| Метод | Путь | Body | Описание |
|---|---|---|---|
| GET | `/export/csv` | — | ZIP с CSV по всем таблицам пользователя, включая устаревшую `buyers.csv`. |
| POST | `/import/csv` | multipart `file` (.zip) | Импорт того же формата, `ON CONFLICT DO NOTHING` (кроме `user_settings` — `DO UPDATE`). |

## Health

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | `{"status": "ok"}`, без авторизации. |
| GET | `/` | `{"name", "version", "docs"}`, без авторизации. |

## Неподключённые эндпоинты

`app/routers/buyers.py` реализует полный CRUD для устаревшей сущности `Buyer` (`/buyers`, `/buyers/{id}`), но роутер не зарегистрирован в `app/main.py` — этих путей нет в работающем API. Подробности — [DOMAIN.md](DOMAIN.md#buyers).
