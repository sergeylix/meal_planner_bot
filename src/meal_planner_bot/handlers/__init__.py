from __future__ import annotations

from aiogram import Router

from meal_planner_bot.handlers.common import router as common_router


def setup_routers() -> Router:
    router = Router()
    router.include_router(common_router)
    return router
