from django.db import models
from django.utils import timezone
from decimal import Decimal
from io import BytesIO
import qrcode
import base64
from django.core.files import File
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.dispatch import receiver



import qrcode
import json
from io import BytesIO
from django.core.files import File

# إعدادات الشركة
from django.db import models




from mptt.models import MPTTModel, TreeForeignKey  



# ===========================================
# 1. شجرة الحسابات باستخدام django-mptt
# ===========================================
ACCOUNT_TYPE_CHOICES = (
    ('asset', 'أصول'),
    ('liability', 'خصوم'),
    ('equity', 'حقوق ملكية'),
    ('income', 'إيرادات'),
    ('expense', 'مصروفات'),
)

class ChartOfAccount(MPTTModel):
    code = models.CharField(max_length=20, unique=True, verbose_name="رمز الحساب")
    name = models.CharField(max_length=100, verbose_name="اسم الحساب")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES, verbose_name="نوع الحساب")
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="الحساب الأب"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="الرصيد")

    class MPTTMeta:
        order_insertion_by = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "حساب"
        verbose_name_plural = "شجرة الحسابات"






class CompanySettings(models.Model):
    # بيانات المؤسسة

    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=" الاسم التجاري عربي"
    )

    en_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="الاسم التجاري بالإنجليزي"
    )
    # العناوين والاتصال
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="رقم الجوال"
    )
    fax = models.CharField(  
    max_length=20,  
    null=True,  
    blank=True,  
    verbose_name="رقم الفاكس"  
)
    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="العنوان (سطر 1)"
    )

    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="المدينة"
    )

    postal_code = models.CharField(
        max_length=9,
        null=True,
        blank=True,
        verbose_name="الرمز البريدي"
    )
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="المملكة العربية السعودية",
        verbose_name="الدولة"
    )

    # البيانات الضريبية والتجارية
    vat_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="الرقم الضريبي"
    )
    cr_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="رقم السجل التجاري"
    )
    vat_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=15.00,
        verbose_name="نسبة الضريبة (%)"
    )

    # الشعار
    logo = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        verbose_name="شعار المنشأة"
    )

    def __str__(self):
        return  self.name

    class Meta:
        verbose_name = "إعدادات المنشأة"
        verbose_name_plural = "إعدادات المنشآت"










class Supplier(models.Model):
    # المعلومات الأساسية للمورد
    name = models.CharField(
        max_length=255,
        verbose_name="اسم المورد"
    )
   
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="رقم الهاتف / الجوال"
    )

    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="البريد الإلكتروني"
    )

    # العنوان
    address_line = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="عنوان الشارع 1"
    )
    
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="المدينة"
    )

 
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="المملكة العربية السعودية",
        verbose_name="البلد"
    )

    # بيانات ضريبية أو تجارية
    vat_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="الرقم الضريبي (إن وجد)"
    )
    cr_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="رقم السجل التجاري (إن وجد)"
    )

    # حقل اختياري لملاحظات أو وصف إضافي
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="ملاحظات إضافية"
    )


        # ربط المورد بحساب الذمم الدائنة
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_accounts',
        verbose_name="حساب المورد"
    )
    def __str__(self):
        return self.name or "مورد"

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردون"




class Customer(models.Model):
    # المعلومات الأساسية
    name = models.CharField(
        max_length=255,
        verbose_name="اسم العميل"
    )

    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="رقم الهاتف / الجوال"
    )


    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="البريد الإلكتروني"
    )

    # العنوان
    address_line = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="عنوان الشارع 1"
    )

    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="المدينة"
    )
  
   
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        default="المملكة العربية السعودية",
        verbose_name="البلد"
    )

    # بيانات ضريبية
    vat_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="الرقم الضريبي (إن وجد)"
    )

    cr_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="رقم السجل التجاري (إن وجد)"
    )

    # ملاحظات أخرى
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="ملاحظات إضافية"
    )



    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_accounts',
        verbose_name="حساب العميل"
    )

    def __str__(self):
        return self.name or "عميل"

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "عملاء"







### ✅ وحدات القياس الأساسية
class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الوحدة الأساسية")
    abbreviation = models.CharField(max_length=20, verbose_name="التمييز")
    template = models.CharField(max_length=50, verbose_name="القالب", help_text="مثال: الوزن")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "وحدة"
        verbose_name_plural = "الوحدات"

### ✅ تحويل الوحدات
class UnitConversion(models.Model):
    base_unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="conversions", verbose_name="الوحدة الأساسية")
    larger_unit_name = models.CharField(max_length=100, verbose_name="اسم الوحدة الأكبر")
    larger_unit_abbreviation = models.CharField(max_length=20, verbose_name="التمييز")
    conversion_factor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="معامل التحويل")

    def __str__(self):
        return f"{self.base_unit.name} -> {self.larger_unit_name} ({self.conversion_factor})"

    class Meta:
        verbose_name = "تحويل وحدة"
        verbose_name_plural = "تحويلات الوحدات"


   
        
# طرق الدفع
class PaymentMethod(models.Model):
    name_ar = models.CharField(max_length=50, unique=True, verbose_name="الاسم العربي")
    name_en = models.CharField(max_length=50, unique=True, verbose_name="الاسم الإنجليزي" , null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name="الوصف")

    def __str__(self):
        return self.name_ar

    class Meta:
        verbose_name = "طريقة دفع"
        verbose_name_plural = "طرق الدفع"

# أصناف المنتجات
class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الصنف")
    description = models.TextField(null=True, blank=True, verbose_name="الوصف")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "صنف المنتج"
        verbose_name_plural = "أصناف المنتجات"



# المنتجات
class Product(models.Model):
    name_ar = models.CharField(max_length=255, verbose_name="اسم المنتج بالعربي")  

    # حقل الرقم التسلسلي  
    serial_number = models.CharField(max_length=255, unique=True, verbose_name="الرقم التسلسلي")  

    category = models.ForeignKey(
        ProductCategory, 
        on_delete=models.CASCADE, 
        related_name="products", 
        verbose_name="الصنف"
    )
    unit = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="وحدة القياس"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    description = models.TextField(null=True, blank=True, verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    stock = models.PositiveIntegerField(default=0, verbose_name="الكمية المتاحة")
    low_stock_threshold = models.PositiveIntegerField(default=10, verbose_name="حد التنبيه")


    # ربط حساب المخزون الخاص بالمنتج
    inventory_account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_products',
        verbose_name="حساب المخزون"
    )
    def __str__(self):
        return self.name_ar

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"




from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
import qrcode
from io import BytesIO
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver
import base64
from datetime import timezone as dt_timezone

from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.files import File
from io import BytesIO
import qrcode
from django.db.models.signals import post_save
from django.dispatch import receiver
import base64
from datetime import timezone as dt_timezone
from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.core.files import File
from io import BytesIO
import qrcode
from django.db.models.signals import post_save
from django.dispatch import receiver
import base64
from datetime import timezone as dt_timezone
from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.core.files import File
from io import BytesIO
import qrcode
from django.db.models.signals import post_save
from django.dispatch import receiver
import base64
from datetime import timezone as dt_timezone




def get_default_company():
    # تأكد من وجود شركة واحدة على الأقل في النظام
    return CompanySettings.objects.first()




from django.db import models
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError

from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# تأكد من استيراد النماذج المرتبطة مثل Product, Unit, UnitConversion, Invoice




class Invoice(models.Model):
    INVOICE_TYPES = [
        ('sales', 'فاتورة مبيعات'),
        ('sales_return', 'مرتجع مبيعات'),
        ('purchase', 'فاتورة مشتريات'),
        ('purchase_return', 'مرتجع مشتريات'),
    ]



    company = models.ForeignKey(
        'CompanySettings',
        on_delete=models.SET_NULL,
        null=True,
        default=get_default_company,
        verbose_name="الشركة"
    )

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="العميل"
    )

    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المورد"
    )

        # ربط فاتورة المرتجعات بالفاتورة الأصلية
    original_invoice = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        help_text="لفواتير المرتجعات",
        verbose_name="الفاتورة الأصلية"
    )

    invoice_type = models.CharField(
        max_length=20,
        choices=INVOICE_TYPES,
        verbose_name="نوع الفاتورة",
        default='sales'
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="رقم الفاتورة"
    )
    invoice_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ ووقت الفاتورة"
    )
    payment_method = models.ForeignKey(
        'PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="طريقة الدفع"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="ملاحظات"
    )


    # حقل اختياري لإدخال سبب المرتجع (إذا كانت الفاتورة مرتجع مبيعات أو مشتريات)
    return_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="سبب المرتجع",
        default='0',  # القيمة الافتراضية هي نص فارغ  

    )

    # الحقول المالية
    subtotal_before_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="الإجمالي قبل الخصم"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="نسبة الخصم %"
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="قيمة الخصم"
    )
    subtotal_before_tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="المجموع قبل الضريبة"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
        verbose_name="نسبة الضريبة"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="قيمة الضريبة"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الصافي'
    )
    qr_code = models.ImageField(
        upload_to='qr_codes/',
        null=True,
        blank=True,
        verbose_name="كود QR"
    )


   
    @property
    def is_return_invoice(self):
        """
        خاصية تسهل التحقق من كون الفاتورة مرتجع مبيعات أو مرتجع مشتريات.
        """
        return self.invoice_type in ['sales_return', 'purchase_return']

    def generate_invoice_number(self):
        """
        توليد رقم فاتورة مخصص: 
        - إذا كانت الفاتورة مرتجع، نضيف بادئة 'R' قبل الرقم التسلسلي.
        - إذا كانت فاتورة عادية، نستخدم الترقيم المعتاد (1000, 1010, ...).
        """
        last_invoice = Invoice.objects.order_by('-id').first()

        # نحدد البادئة بحسب إذا كانت فاتورة مرتجع أم لا
        prefix = "R" if self.is_return_invoice else ""

        if last_invoice and last_invoice.invoice_number:
            # حاول تحويل آخر رقم لفاتورة إلى عدد صحيح
            try:
                # إذا كانت الفاتورة السابقة أيضًا تحتوي على بادئة، نتجاهلها عند التحويل
                clean_number = last_invoice.invoice_number.replace("R", "")
                last_num = int(clean_number)
            except (ValueError, TypeError):
                last_num = 990
        else:
            last_num = 990

        new_number = last_num + 10
        return f"{prefix}{new_number}"


    def calculate_totals(self):
        """
        حساب إجمالي الفاتورة باستخدام البيانات من عناصر الفاتورة.
        يتم حساب الخصم بناءً على النسبة أو القيمة المدخلة،
        ويتم تحديث كلا الحقلين تبادليًا.
        وبعدها يتم حساب المجموع قبل الضريبة وقيمة الضريبة والإجمالي النهائي.
        """
        invoice_items = self.invoice_items.all()
        if not invoice_items.exists():
            self.subtotal_before_discount = Decimal('0.00')
            self.discount = Decimal('0.00')
            self.discount_percentage = Decimal('0.00')
            self.subtotal_before_tax = Decimal('0.00')
            self.tax_amount = Decimal('0.00')
            self.total_amount = Decimal('0.00')
        else:
            self.subtotal_before_discount = sum(item.total_before_tax for item in invoice_items)
            if self.subtotal_before_discount > Decimal('0.00'):
                # إذا تم إدخال نسبة خصم غير صفرية، احسب قيمة الخصم من النسبة.
                if self.discount_percentage and self.discount_percentage > Decimal('0.00'):
                    self.discount = (self.subtotal_before_discount * self.discount_percentage / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                # إذا لم يتم إدخال نسبة خصم ولكن تم إدخال قيمة خصم تتجاوز الصفر، احسب النسبة المكافئة.
                elif self.discount and self.discount > Decimal('0.00'):
                    self.discount_percentage = (self.discount * Decimal('100') / self.subtotal_before_discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    self.discount = Decimal('0.00')
                    self.discount_percentage = Decimal('0.00')
            else:
                self.discount = Decimal('0.00')
                self.discount_percentage = Decimal('0.00')

            self.subtotal_before_tax = self.subtotal_before_discount - self.discount
            self.tax_amount = (self.subtotal_before_tax * self.tax_rate / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.total_amount = self.subtotal_before_tax + self.tax_amount

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)



    def clean(self):
        """
        التحقق من صحة البيانات قبل الحفظ.
        - لا يمكن تحديد عميل مع فاتورة مشتريات أو مرتجع مشتريات.
        - لا يمكن تحديد مورد مع فاتورة مبيعات أو مرتجع مبيعات.
        - يجب تحديد سبب المرتجع إذا كانت الفاتورة مرتجع (اختياري حسب رغبتك).
        - التحقق من عدم كون المجموع الكلي أقل من الصفر.
        """
        if self.invoice_type in ['sales', 'sales_return']:
            if not self.customer:
                raise ValidationError("يجب اختيار عميل لفاتورة المبيعات أو المرتجع.")
            if self.supplier:
                raise ValidationError("لا يمكن تحديد مورد لفاتورة المبيعات أو المرتجع.")

        elif self.invoice_type in ['purchase', 'purchase_return']:
            if not self.supplier:
                raise ValidationError("يجب اختيار مورد لفاتورة المشتريات أو المرتجع.")
            if self.customer:
                raise ValidationError("لا يمكن تحديد عميل لفاتورة المشتريات أو المرتجع.")

        # التحقق من وجود سبب المرتجع إذا أردت جعله إلزاميًا
        if self.is_return_invoice and not self.return_reason:
            raise ValidationError("يجب إدخال سبب المرتجع عند اختيار مرتجع مبيعات أو مرتجع مشتريات.")

        if self.total_amount < 0:
            raise ValidationError("المجموع الكلي لا يمكن أن يكون أقل من صفر.")

   
    def generate_qr_code(self):
        """إنشاء رمز QR بناءً على بيانات الفاتورة"""
        if not self.company or not self.company.vat_number:
            return
        timestamp = self.invoice_date.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            1: self.company.name,
            2: self.company.vat_number,
            3: timestamp,
            4: f"{self.total_amount:.2f}",
            5: f"{self.tax_amount:.2f}"
        }
        tlv_data = bytearray()
        for tag, value in data.items():
            value_bytes = value.encode('utf-8')
            tlv_data += bytes([tag]) + bytes([len(value_bytes)]) + value_bytes
        base64_payload = base64.b64encode(tlv_data).decode('utf-8')
        # Remove explicit version to allow automatic sizing and help avoid recursion error
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2
        )
        qr.add_data(base64_payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_{self.invoice_number}.png'  
        self.qr_code.save(filename, File(buffer), save=False)

    def __str__(self):
        return f"{self.invoice_number} - {self.invoice_date}"

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['invoice_date']),
        ]



class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='invoice_items',
        verbose_name='الفاتورة',
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.PROTECT,
        verbose_name='المنتج'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='الكمية',
        default=1
    )
    # تحديد الوحدة الأساسية تلقائيًا من المنتج (غير قابلة للتعديل)
    base_unit = models.ForeignKey(
        'Unit',
        on_delete=models.CASCADE,
        verbose_name="الوحدة الأساسية",
        editable=False,
        null=True,
        blank=True,
    )
    # اختيار وحدة التحويل؛ إذا لم يتم تحديدها فهذا يعني استخدام الوحدة الأساسية
    unit = models.ForeignKey(
        'UnitConversion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="الوحدة المختارة"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="السعر لكل وحدة",
        default=0
    )
    total_before_tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name='المجموع قبل الضريبة'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
        verbose_name="نسبة الضريبة"
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False,
        verbose_name='المجموع النهائي'
    )
    # إضافة حقول لتوثيق زمن الإنشاء والتعديل
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')

    def save(self, *args, **kwargs):
        """
        عند حفظ عنصر الفاتورة:
         - يتم تعيين الوحدة الأساسية من المنتج.
         - إذا تم اختيار وحدة تحويل، يتم ضرب السعر بمعامل التحويل؛ وإلا يُستخدم السعر الأساسي.
         - يتم حساب المجموع قبل الضريبة (الكمية * السعر) ومن ثم حساب الضريبة والمجموع النهائي.
        """
        if not self.product:
            raise ValidationError('يجب اختيار منتج')

        # تعيين الوحدة الأساسية من بيانات المنتج
        self.base_unit = self.product.unit

        # السعر الأساسي للمنتج
        base_price = self.product.price

        if self.unit:
            # التأكد من وجود معامل تحويل صالح، وإلا نعتبر معامل التحويل 1
            conversion_factor = self.unit.conversion_factor if self.unit.conversion_factor else Decimal('1')
            self.unit_price = base_price * conversion_factor
        else:
            self.unit_price = base_price

        # حساب المجموع قبل الضريبة
        self.total_before_tax = self.quantity * self.unit_price

        # حساب المجموع النهائي بعد إضافة الضريبة
        tax_multiplier = Decimal('1') + (self.tax_rate / Decimal('100'))
        self.total = (self.total_before_tax * tax_multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)

    def clean(self):
        """
        التحقق من صحة البيانات:
         - التأكد من أن الكمية أكبر من الصفر.
         - التأكد من اختيار المنتج.
        """
        if self.quantity <= Decimal('0'):
            raise ValidationError('الكمية يجب أن تكون أكبر من صفر')
        if not self.product_id:
            raise ValidationError('يجب اختيار منتج')
        super().clean()

    def __str__(self):
        """
        عرض معلومات العنصر بشكل ملائم؛ يتم عرض اسم المنتج والكمية مع الوحدة (الوحدة المختارة إن وجدت أو الأساسية).
        """
        unit_display = self.unit.larger_unit_name if self.unit else self.base_unit.abbreviation
        return f"{self.product.name_ar} - {self.quantity} {unit_display}"

    class Meta:
        verbose_name = 'عنصر الفاتورة'
        verbose_name_plural = 'عناصر الفاتورة'




@receiver(post_save, sender=InvoiceItem)
def update_invoice_totals(sender, instance, **kwargs):
    invoice = instance.invoice
    if invoice and not kwargs.get('raw', False):
        invoice.calculate_totals()
        invoice.generate_qr_code()
        invoice.save(update_fields=[
            'subtotal_before_discount',
            'discount',
            'discount_percentage',
            'subtotal_before_tax',
            'tax_amount',
            'total_amount',
            'qr_code'
        ])

        