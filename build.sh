#!/usr/bin/env bash
set -e  # توقف لو حصل خطأ

echo "Installing Python dependencies…"
pip install -r requirements.txt

echo "Applying migrations…"
python manage.py migrate --no-input

echo "Collecting static files…"
python manage.py collectstatic --no-input
