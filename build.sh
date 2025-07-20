#!/usr/bin/env bash
set -e

echo "🚀 Starting fresh database setup..."

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗑️ Clearing any problematic migrations..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -not -path "./venv/*" -not -path "./.venv/*" -delete || true
find . -path "*/migrations/*.pyc" -not -path "./venv/*" -not -path "./.venv/*" -delete || true

echo "🔄 Creating fresh migration files..."
python manage.py makemigrations contenttypes
python manage.py makemigrations auth
python manage.py makemigrations sessions
python manage.py makemigrations admin

echo "🔄 Creating app-specific migrations..."
python manage.py makemigrations

echo "🗃️ Dropping and recreating all tables..."
python manage.py shell <<EOF
from django.db import connection
from django.core.management.color import no_style
from django.db import transaction

try:
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if tables:
                print(f"Dropping {len(tables)} existing tables...")
                # Disable foreign key checks
                cursor.execute('SET session_replication_role = replica;')
                
                # Drop all tables
                for table in tables:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    print(f"Dropped table: {table}")
                
                # Re-enable foreign key checks
                cursor.execute('SET session_replication_role = DEFAULT;')
                print("✅ All tables dropped successfully")
            else:
                print("ℹ️ No existing tables to drop")
                
except Exception as e:
    print(f"⚠️ Error during table cleanup: {e}")
    print("Continuing with migration...")
EOF

echo "⚡ Running fresh migrations..."
python manage.py migrate --no-input

echo "👤 Creating superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='1'
        )
        print("✅ Admin user created successfully")
    else:
        print("ℹ️ Admin user already exists")
except Exception as e:
    print(f"❌ Error creating superuser: {e}")
EOF

echo "🌱 Seeding accounts..."
python manage.py seed_accounts || echo "⚠️ Seeding failed, continuing..."

echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

echo "✅ Fresh database setup completed!"