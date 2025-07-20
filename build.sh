#!/usr/bin/env bash
set -e  # إيقاف السكربت لو حصل خطأ

echo "1️⃣ تثبيت التبعيات…
"
pip install -r requirements.txt

echo "2️⃣ إنشاء الميجريشنز تلقائيًا…
"
python manage.py makemigrations --no-input

echo "3️⃣ تطبيق الميجريشنات…
"
python manage.py migrate --no-input

echo "4️⃣ تعبئة الحسابات الأساسية…
"
python manage.py seed_accounts

echo "5️⃣ إنشاء أو التأكد من وجود superuser…
"
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@example.com','1')
    print("✅ Superuser ‘admin’ created")
else:
    print("⚠️ Superuser ‘admin’ already exists")
EOF

echo "6️⃣ جمع ملفات الثابتة…
"
python manage.py collectstatic --no-input

echo "✅ انتهى بناء المشروع."
