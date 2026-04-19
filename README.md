# meal_planner_bot

Telegram-бот для хранения списка блюд и помощи в выборе, что заказать или приготовить.

## Стек

- Python 3.9+
- aiogram 3
- python-dotenv

## Быстрый старт

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости:

```bash
pip install aiogram python-dotenv
```

3. Создайте `.env` по примеру и укажите токен бота:

```bash
cp .env.example .env
```

4. Запустите бота:

```bash
env PYTHONPATH=src .venv/bin/python3 -m meal_planner_bot
```

## Доступ

Бот работает по заявкам:

- пользователь отправляет запрос на доступ
- администратор получает уведомление в Telegram
- после одобрения пользователь может пользоваться ботом

Для этого в `.env` нужно указать Telegram `user_id` администраторов:

```env
ADMIN_USER_IDS=123456789,987654321
```

## Возможности

Сейчас бот уже поддерживает:

- доступ по заявкам с подтверждением администратором
- справочник блюд в SQLite
- приоритеты блюд и счетчик заказов
- дату последнего заказа и дату паузы рекомендаций
- рекомендации набора из `супа`, `второго` и `салата`
- автооценку заказанных блюд из последнего заказа

## Справочник блюд

В SQLite добавлен отдельный справочник блюд `dishes` с полями:

- `name`
- `slug`
- `dish_type`
- `notes`
- `recipe_url`
- `priority`
- `order_count`
- `last_ordered_at`
- `do_not_recommend_until`

Шкала `priority`:

- `0` - совсем не нравится, не готовим больше
- `1` - не нравится, но можно приготовить
- `2` - нравится
- `3` - очень нравится

Импорт справочника можно повторить командой:

```bash
env PYTHONPATH=src .venv/bin/python3 -m meal_planner_bot.seed_dishes
```

Форматы команд:

```text
/start
/help
/request_access
/whoami
/dishes
/dish <id|slug|название>
/suggest
/add_dish <тип> | <название> | [ссылка] | [комментарий]
/update_last_ordered <id|slug|название> | [YYYY-MM-DD]
/set_dishes_review_schedule <день_недели> <HH:MM>
```

Команды в меню Telegram:

- `/start`
- `/help`
- `/request_access`
- `/dishes`
- `/dish`
- `/suggest`

Скрытые, но рабочие команды:

- `/whoami`
- `/add_dish`
- `/update_last_ordered`
- `/set_dishes_review_schedule`

Сейчас `/add_dish`, `/update_last_ordered` и `/set_dishes_review_schedule` доступны только администратору.

`/update_last_ordered` не только обновляет дату последнего заказа и увеличивает счетчик заказов блюда, но и ставит дату паузы рекомендаций на 14 дней вперед.

`/suggest` подбирает 3 блюда: одно `суп`, одно `второе`, одно `салат`.
Алгоритм:

- исключает замороженные блюда
- исключает блюда с приоритетом `0`
- считает вес по давности последнего заказа
- считает вес по приоритету
- складывает веса
- берет `top 3` по каждому типу и случайно выбирает одно блюдо

После `/suggest` бот показывает кнопки:

- `Выбрать`
- `Изменить`

При `Выбрать` весь набор считается заказанным и у всех 3 блюд обновляются:

- `last_ordered_at`
- `order_count`
- `do_not_recommend_until`

При `Изменить` появляются кнопки:

- `Заменить суп`
- `Заменить второе`
- `Заменить салат`
- `Отмена`

После замены пересчитывается только выбранный тип блюда, а текущее выбранное блюдо этого типа исключается из кандидатов, чтобы оно не выпало снова.

## Автооценка Заказанных Блюд

Бот сам присылает администраторам блюда из последнего заказа и просит выбрать приоритет кнопками `0`, `1`, `2`, `3` или `Отмена`.

По умолчанию расписание такое:

- каждая пятница в `14:00 UTC`

Изменить расписание можно скрытой админ-командой:

```text
/set_dishes_review_schedule пятница 14:00
```

## VPS Deploy

Ниже базовый вариант для Ubuntu VPS с `systemd`.

### 1. Установить системные пакеты

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

### 2. Подготовить пользователя и окружение

Скрипт для первичной подготовки:

```bash
chmod +x scripts/bootstrap_vps.sh
./scripts/bootstrap_vps.sh
```

По умолчанию он готовит:

- пользователя `mealplanner`
- директорию `/opt/meal_planner_bot`
- виртуальное окружение `/opt/meal_planner_bot/.venv`

### 3. Клонировать проект на сервер

```bash
sudo -u mealplanner git clone git@github.com:sergeylix/meal_planner_bot.git /opt/meal_planner_bot
```

Если репозиторий уже клонирован, просто обнови его.

### 4. Создать `.env` на сервере

Пример:

```env
BOT_TOKEN=your_token
ADMIN_USER_IDS=123456789
DATABASE_PATH=data/meal_planner_bot.db
```

### 5. Установить `systemd` unit

Скопируй шаблон:

```bash
sudo cp deploy/systemd/meal_planner_bot.service /etc/systemd/system/meal_planner_bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now meal_planner_bot
```

### 6. Проверить статус и логи

```bash
sudo systemctl status meal_planner_bot
sudo journalctl -u meal_planner_bot -f
```

### 7. Обновление приложения

Для последующих обновлений можно использовать:

```bash
chmod +x scripts/deploy_update.sh
APP_DIR=/opt/meal_planner_bot ./scripts/deploy_update.sh
```
