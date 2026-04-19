from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable, Optional


@dataclass(frozen=True)
class DishSeed:
    name: str
    slug: str
    dish_type: str
    notes: Optional[str] = None
    recipe_url: Optional[str] = None
    last_ordered_at: Optional[str] = None


class DishRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def upsert_many(self, dishes: Iterable[DishSeed]) -> None:
        with self._connect() as connection:
            for dish in dishes:
                connection.execute(
                    """
                    INSERT INTO dishes (name, slug, dish_type, notes, recipe_url, last_ordered_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(slug) DO UPDATE SET
                        name = excluded.name,
                        dish_type = excluded.dish_type,
                        notes = excluded.notes,
                        recipe_url = excluded.recipe_url,
                        last_ordered_at = excluded.last_ordered_at,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        dish.name,
                        dish.slug,
                        dish.dish_type,
                        dish.notes,
                        dish.recipe_url,
                        dish.last_ordered_at,
                    ),
                )
            connection.commit()

