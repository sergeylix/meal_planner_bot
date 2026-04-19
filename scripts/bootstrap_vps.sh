#!/usr/bin/env bash

set -euo pipefail

APP_USER="${APP_USER:-mealplanner}"
APP_DIR="${APP_DIR:-/opt/meal_planner_bot}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "Creating system user if needed..."
if ! id -u "$APP_USER" >/dev/null 2>&1; then
  sudo useradd --system --create-home --shell /bin/bash "$APP_USER"
fi

echo "Preparing application directory..."
sudo mkdir -p "$APP_DIR"
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "Installing Python venv..."
sudo -u "$APP_USER" "$PYTHON_BIN" -m venv "$APP_DIR/.venv"

echo "Installing dependencies..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install aiogram python-dotenv

echo "Bootstrap complete."
echo "Next steps:"
echo "1. Clone the repo into $APP_DIR"
echo "2. Create $APP_DIR/.env"
echo "3. Copy deploy/systemd/meal_planner_bot.service to /etc/systemd/system/"
echo "4. Run: sudo systemctl daemon-reload"
echo "5. Run: sudo systemctl enable --now meal_planner_bot"
