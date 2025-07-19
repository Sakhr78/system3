from django.core.management.base import BaseCommand
from invoices.models import Product
from openpyxl import Workbook

class Command(BaseCommand):
    help = "تصدير جميع المنتجات إلى ملف Excel"

    def handle(self, *args, **options):
        # إنشاء ملف Excel جديد وورقة عمل
        wb = Workbook()
        ws = wb.active
        ws.title = "المنتجات"

        # كتابة رؤوس الأعمدة (يمكنك تعديلها لتتناسب مع نموذج Product)
        headers = [
            "name_ar",              # اسم المنتج بالعربي
            "serial_number",        # الرقم التسلسلي
            "category",             # اسم الصنف
            "unit",                 # وحدة القياس
            "price",                # السعر
            "description",          # الوصف
            "stock",                # الكمية المتاحة
            "low_stock_threshold",  # حد التنبيه
            "inventory_account"     # حساب المخزون
        ]
        ws.append(headers)

        # جلب جميع المنتجات من قاعدة البيانات
        products = Product.objects.all()
        for product in products:
            row = [
                product.name_ar,
                product.serial_number,
                product.category.name if product.category else "",
                product.unit.name if product.unit else "",
                str(product.price) if product.price else "",
                product.description or "",
                product.stock,
                product.low_stock_threshold,
                product.inventory_account.name if product.inventory_account else "",
            ]
            ws.append(row)

        # تحديد مسار حفظ الملف (في جذر المشروع، نفس مكان manage.py)
        file_path = "products.xlsx"
        wb.save(file_path)
        self.stdout.write(self.style.SUCCESS(f"تم تصدير المنتجات بنجاح إلى الملف: {file_path}"))
