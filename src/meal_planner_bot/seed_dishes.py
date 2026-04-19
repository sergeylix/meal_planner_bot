from __future__ import annotations

from meal_planner_bot.config import load_settings
from meal_planner_bot.database import init_database
from meal_planner_bot.dish_catalog import DISH_CATALOG
from meal_planner_bot.dishes import DishRepository


def main() -> None:
    settings = load_settings()
    init_database(settings.database_path)
    repository = DishRepository(settings.database_path)
    repository.upsert_many(DISH_CATALOG)
    print(f"Imported {len(DISH_CATALOG)} dishes into {settings.database_path}")


if __name__ == "__main__":
    main()
