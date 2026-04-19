from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import random
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
    order_count: int = 0
    do_not_recommend_until: Optional[str] = None
    priority: int = 2


@dataclass(frozen=True)
class Dish:
    id: int
    name: str
    slug: str
    dish_type: str
    notes: Optional[str]
    recipe_url: Optional[str]
    last_ordered_at: Optional[str]
    order_count: int
    do_not_recommend_until: Optional[str]
    priority: int
    is_active: int


class DishRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def validate_priority(priority: int) -> int:
        if priority not in {0, 1, 2, 3}:
            raise ValueError("Priority must be one of: 0, 1, 2, 3.")
        return priority

    def upsert_many(self, dishes: Iterable[DishSeed]) -> None:
        with self._connect() as connection:
            for dish in dishes:
                connection.execute(
                    """
                    INSERT INTO dishes (
                        name, slug, dish_type, notes, recipe_url, last_ordered_at, order_count,
                        do_not_recommend_until, priority
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(slug) DO UPDATE SET
                        name = excluded.name,
                        dish_type = excluded.dish_type,
                        notes = excluded.notes,
                        recipe_url = excluded.recipe_url,
                        last_ordered_at = excluded.last_ordered_at,
                        order_count = excluded.order_count,
                        do_not_recommend_until = excluded.do_not_recommend_until,
                        priority = excluded.priority,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        dish.name,
                        dish.slug,
                        dish.dish_type,
                        dish.notes,
                        dish.recipe_url,
                        dish.last_ordered_at,
                        dish.order_count,
                        dish.do_not_recommend_until,
                        self.validate_priority(dish.priority),
                    ),
                )
            connection.commit()

    def list_active(self) -> list[Dish]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id, name, slug, dish_type, notes, recipe_url, last_ordered_at, order_count,
                    do_not_recommend_until, priority, is_active
                FROM dishes
                WHERE is_active = 1
                ORDER BY dish_type, name
                """
            ).fetchall()
        return [Dish(**dict(row)) for row in rows]

    def get_by_id(self, dish_id: int) -> Optional[Dish]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id, name, slug, dish_type, notes, recipe_url, last_ordered_at, order_count,
                    do_not_recommend_until, priority, is_active
                FROM dishes
                WHERE id = ?
                """,
                (dish_id,),
            ).fetchone()
        return Dish(**dict(row)) if row else None

    def find_one(self, query: str) -> Optional[Dish]:
        normalized_query = query.strip()
        if not normalized_query:
            return None

        if normalized_query.isdigit():
            dish = self.get_by_id(int(normalized_query))
            if dish is not None:
                return dish

        query_lower = normalized_query.lower()
        dishes = self.list_active()

        for dish in dishes:
            if dish.slug.lower() == query_lower:
                return dish

        for dish in dishes:
            if dish.name.lower() == query_lower:
                return dish

        for dish in dishes:
            if query_lower in dish.name.lower():
                return dish

        return None

    def create(self, dish: DishSeed) -> Dish:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO dishes (
                    name, slug, dish_type, notes, recipe_url, last_ordered_at, order_count,
                    do_not_recommend_until, priority
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dish.name,
                    dish.slug,
                    dish.dish_type,
                    dish.notes,
                    dish.recipe_url,
                    dish.last_ordered_at,
                    dish.order_count,
                    dish.do_not_recommend_until,
                    self.validate_priority(dish.priority),
                ),
            )
            connection.commit()
            dish_id = cursor.lastrowid

        created_dish = self.get_by_id(int(dish_id))
        if created_dish is None:
            raise ValueError("Failed to create dish.")
        return created_dish

    def get_latest_ordered_dishes(self) -> list[Dish]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id, name, slug, dish_type, notes, recipe_url, last_ordered_at, order_count,
                    do_not_recommend_until, priority, is_active
                FROM dishes
                WHERE is_active = 1
                  AND last_ordered_at IS NOT NULL
                  AND last_ordered_at = (
                    SELECT MAX(last_ordered_at)
                    FROM dishes
                    WHERE is_active = 1
                      AND last_ordered_at IS NOT NULL
                  )
                ORDER BY name
                """
            ).fetchall()
        return [Dish(**dict(row)) for row in rows]

    def update_last_ordered(self, dish_id: int, ordered_at: str) -> Optional[Dish]:
        ordered_date = datetime.strptime(ordered_at, "%Y-%m-%d").date()
        do_not_recommend_until = (ordered_date + timedelta(days=14)).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE dishes
                SET last_ordered_at = ?,
                    order_count = order_count + 1,
                    do_not_recommend_until = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (ordered_at, do_not_recommend_until, dish_id),
            )
            connection.commit()
        return self.get_by_id(dish_id)

    def update_priority(self, dish_id: int, priority: int) -> Optional[Dish]:
        validated_priority = self.validate_priority(priority)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE dishes
                SET priority = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (validated_priority, dish_id),
            )
            connection.commit()
        return self.get_by_id(dish_id)

    @staticmethod
    def _date_weight(last_ordered_at: Optional[str], today: date) -> int:
        if not last_ordered_at:
            return 3

        ordered_date = datetime.strptime(last_ordered_at, "%Y-%m-%d").date()
        days_since_order = (today - ordered_date).days

        if days_since_order < 21:
            return 1
        if days_since_order < 35:
            return 2
        return 3

    @staticmethod
    def _priority_weight(priority: Optional[int]) -> int:
        if priority in (2, 3):
            return 2
        return 1

    def get_suggestions(self, today: Optional[date] = None) -> dict[str, Optional[Dish]]:
        current_date = today or date.today()
        dishes = self.list_active()

        filtered_dishes = []
        for dish in dishes:
            if dish.priority == 0:
                continue
            if dish.do_not_recommend_until:
                freeze_until = datetime.strptime(dish.do_not_recommend_until, "%Y-%m-%d").date()
                if freeze_until >= current_date:
                    continue
            filtered_dishes.append(dish)

        suggestions: dict[str, Optional[Dish]] = {}
        for dish_type in ("суп", "второе", "салат"):
            suggestions[dish_type] = self.get_suggestion_for_type(
                dish_type=dish_type,
                today=current_date,
                excluded_ids=None,
            )

        return suggestions

    def get_suggestion_for_type(
        self,
        dish_type: str,
        today: Optional[date] = None,
        excluded_ids: Optional[set[int]] = None,
    ) -> Optional[Dish]:
        current_date = today or date.today()
        excluded = excluded_ids or set()
        scored = []

        for dish in self.list_active():
            if dish.dish_type != dish_type or dish.id in excluded:
                continue
            if dish.priority == 0:
                continue
            if dish.do_not_recommend_until:
                freeze_until = datetime.strptime(dish.do_not_recommend_until, "%Y-%m-%d").date()
                if freeze_until >= current_date:
                    continue

            score = self._date_weight(dish.last_ordered_at, current_date) + self._priority_weight(
                dish.priority
            )
            scored.append((score, dish))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        top_dishes = [dish for _, dish in scored[:3]]
        return random.choice(top_dishes) if top_dishes else None
