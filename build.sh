#!/usr/bin/env bash
set -e

echo "Installing dependencies…"
pip install -r requirements.txt

echo "Applying migrations…"
python manage.py migrate --no-input

echo "Seeding accounts…"
python manage.py seed_accounts

echo "Creating superuser if missing…"
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@example.com','1')
EOF

echo "Collecting static files…"
python manage.py collectstatic --no-input

echo "Done."
