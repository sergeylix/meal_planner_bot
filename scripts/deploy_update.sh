#!/usr/bin/env bash

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/meal_planner_bot}"
BRANCH="${BRANCH:-main}"

cd "$APP_DIR"

git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

.venv/bin/pip install --upgrade pip
.venv/bin/pip install aiogram python-dotenv

sudo systemctl restart meal_planner_bot
sudo systemctl status meal_planner_bot --no-pager
