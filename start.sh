#!/bin/bash

# このスクリプト内でコマンドが失敗した場合、即座に終了する
set -e

echo "Running startup script..."

# データベースのマイグレーションを適用
echo "Applying database migrations..."
flask db upgrade

# 初期データを投入 (app.py内の処理で、データがなければ投入される)
echo "Seeding initial data..."
flask seed-db

# 管理者ユーザーを作成 (app.py内の処理で、ユーザーがいなければ作成される)
echo "Creating admin user..."
flask create-admin

# Gunicornサーバーを起動する
echo "Starting Gunicorn server..."
exec gunicorn app:app