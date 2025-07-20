#!/usr/bin/env bash
set -e

echo "1️⃣ Installing dependencies…"
pip install -r requirements.txt

echo "2️⃣ Making migrations for your apps…"
python manage.py makemigrations --no-input

echo "3️⃣ Applying all migrations…"
python manage.py migrate --no-input

echo "4️⃣ (Optional) Seeding chart of accounts…"
python manage.py seed_accounts

echo "5️⃣ Ensuring superuser exists…"
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@example.com','1')
EOF

echo "6️⃣ Collecting static files…"
python manage.py collectstatic --no-input

echo "✅ Build script finished."
