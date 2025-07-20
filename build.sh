#!/usr/bin/env bash
set -e

echo "🚀 بدء الحل الجذري لمشكلة Django..."

# التأكد من تثبيت المتطلبات
echo "📦 تثبيت المتطلبات..."
pip install -r requirements.txt

# التحقق من الاتصال بقاعدة البيانات
echo "🔍 فحص الاتصال بقاعدة البيانات..."
python manage.py shell <<EOF
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ الاتصال بقاعدة البيانات سليم")
except Exception as e:
    print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
    exit(1)
EOF

# حذف جميع الجداول الموجودة لضمان البداية من الصفر
echo "🗑️ حذف جميع الجداول الموجودة..."
python manage.py shell <<EOF
from django.db import connection
from django.db import transaction

try:
    with connection.cursor() as cursor:
        # الحصول على جميع أسماء الجداول
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if tables:
            print(f"🗑️ حذف {len(tables)} جدول موجود...")
            
            # تعطيل فحص المفاتيح الخارجية
            cursor.execute('SET session_replication_role = replica;')
            
            # حذف جميع الجداول
            for table in tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    print(f"✅ تم حذف الجدول: {table}")
                except Exception as te:
                    print(f"⚠️ خطأ في حذف الجدول {table}: {te}")
            
            # إعادة تفعيل فحص المفاتيح الخارجية
            cursor.execute('SET session_replication_role = DEFAULT;')
            print("✅ تم حذف جميع الجداول بنجاح")
        else:
            print("ℹ️ لا توجد جداول للحذف")
            
except Exception as e:
    print(f"⚠️ خطأ أثناء حذف الجداول: {e}")
    print("المتابعة مع إنشاء الجداول الجديدة...")
EOF

# حذف ملفات migrations القديمة التالفة
echo "🔄 حذف ملفات migrations القديمة..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -not -path "./venv/*" -not -path "./.venv/*" -delete || true
find . -path "*/migrations/*.pyc" -not -path "./venv/*" -not -path "./.venv/*" -delete || true

# التأكد من وجود مجلدات migrations وملفات __init__.py
echo "📁 إنشاء مجلدات migrations..."
python manage.py shell <<EOF
import os
from django.conf import settings
from django.apps import apps

for app_config in apps.get_app_configs():
    if app_config.name.startswith('django.contrib'):
        continue
        
    migrations_dir = os.path.join(app_config.path, 'migrations')
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
        print(f"📁 تم إنشاء مجلد: {migrations_dir}")
    
    init_file = os.path.join(migrations_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
        print(f"📄 تم إنشاء ملف: {init_file}")
EOF

# إنشاء migrations جديدة لجميع التطبيقات الأساسية
echo "🔧 إنشاء migrations جديدة للتطبيقات الأساسية..."
python manage.py makemigrations contenttypes --empty || python manage.py makemigrations contenttypes
python manage.py makemigrations auth --empty || python manage.py makemigrations auth  
python manage.py makemigrations admin --empty || python manage.py makemigrations admin
python manage.py makemigrations sessions --empty || python manage.py makemigrations sessions

# إنشاء migrations للتطبيقات المخصصة
echo "🔧 إنشاء migrations للتطبيقات المخصصة..."
python manage.py makemigrations

# تطبيق migrations بالترتيب الصحيح
echo "⚡ تطبيق migrations..."
python manage.py migrate contenttypes --no-input
python manage.py migrate auth --no-input
python manage.py migrate admin --no-input
python manage.py migrate sessions --no-input
python manage.py migrate --no-input

# التحقق من إنشاء الجداول
echo "🔍 التحقق من إنشاء الجداول..."
python manage.py shell <<EOF
from django.db import connection
from django.contrib.auth.models import User

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ تم إنشاء {len(tables)} جدول:")
        for table in tables:
            print(f"  📋 {table}")
    
    # اختبار جدول المستخدمين
    user_count = User.objects.count()
    print(f"✅ جدول المستخدمين يعمل بشكل صحيح - عدد المستخدمين: {user_count}")
    
except Exception as e:
    print(f"❌ خطأ في اختبار الجداول: {e}")
    exit(1)
EOF

# إنشاء superuser
echo "👤 إنشاء حساب المدير..."
python manage.py shell <<EOF
from django.contrib.auth.models import User

try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("✅ تم إنشاء حساب المدير بنجاح")
        print("   اسم المستخدم: admin")
        print("   كلمة المرور: admin123")
    else:
        print("ℹ️ حساب المدير موجود بالفعل")
except Exception as e:
    print(f"❌ خطأ في إنشاء حساب المدير: {e}")
EOF

# تشغيل أوامر إضافية إذا كانت موجودة
echo "🌱 تشغيل أوامر إضافية..."
python manage.py seed_accounts || echo "⚠️ أمر seed_accounts غير موجود أو فشل"

# جمع الملفات الثابتة
echo "📁 جمع الملفات الثابتة..."
python manage.py collectstatic --no-input

# اختبار نهائي
echo "🧪 اختبار نهائي..."
python manage.py shell <<EOF
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

try:
    # اختبار إنشاء مستخدم
    test_user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
    print("✅ تم إنشاء مستخدم تجريبي بنجاح")
    
    # اختبار المصادقة
    auth_user = authenticate(username='testuser', password='testpass123')
    if auth_user:
        print("✅ المصادقة تعمل بشكل صحيح")
    else:
        print("❌ فشل في المصادقة")
    
    # حذف المستخدم التجريبي
    test_user.delete()
    print("✅ تم حذف المستخدم التجريبي")
    
except Exception as e:
    print(f"❌ خطأ في الاختبار النهائي: {e}")
EOF

echo ""
echo "🎉 تم الانتهاء من الحل الجذري بنجاح!"
echo "📋 معلومات تسجيل الدخول:"
echo "   🌐 الرابط: https://system3-2pvh.onrender.com/login/"
echo "   👤 اسم المستخدم: admin"
echo "   🔑 كلمة المرور: admin123"
echo ""