from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum

# مكتبات لشجرة الحسابات
from mptt.models import MPTTModel, TreeForeignKey

# مكتبات لإنشاء رمز QR (اختياري)
import base64
import qrcode
from io import BytesIO
from django.core.files.base import File
from datetime import timezone as dt_timezone, datetime

User = get_user_model()

# ثابت لأنواع الحسابات
ACCOUNT_TYPE_CHOICES = (
    ('asset', 'أصول'),
    ('liability', 'خصوم'),
    ('equity', 'حقوق ملكية'),
    ('income', 'إيرادات'),
    ('expense', 'مصروفات'),
)

# ==============================================================================
# 1) إعدادات المنشأة
# ==============================================================================
class CompanySettings(models.Model):
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="الاسم التجاري عربي"
    )
    en_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="الاسم التجاري بالإنجليزي"
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="البريد الإلكتروني"
    )
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
    logo = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        verbose_name="شعار المنشأة"
    )

    def __str__(self):
        return self.name or "إعدادات المنشأة"

    class Meta:
        verbose_name = "إعدادات المنشأة"
        verbose_name_plural = "إعدادات المنشآت"


# ==============================================================================
# 2) شجرة الحسابات (ChartOfAccount) مع MPTT
# ==============================================================================
class ChartOfAccount(MPTTModel):
    code = models.CharField(max_length=20, unique=True, verbose_name="رمز الحساب")
    name = models.CharField(max_length=100, verbose_name="اسم الحساب")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES, verbose_name="نوع الحساب")
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                            related_name='children', verbose_name="الحساب الأب")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="الرصيد")

    class MPTTMeta:
        order_insertion_by = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "حساب"
        verbose_name_plural = "شجرة الحسابات"


# ==============================================================================
# 3) القيود المحاسبية (JournalEntry) وتفاصيلها
# ==============================================================================
class JournalEntry(models.Model):
    date = models.DateField("تاريخ القيد", default=timezone.now)
    description = models.TextField("وصف القيد")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="تم الإنشاء بواسطة")

    def __str__(self):
        return f"قيد محاسبي بتاريخ {self.date}"


class JournalEntryDetail(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="details")
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, verbose_name="الحساب")
    debit = models.DecimalField("مدين", max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit = models.DecimalField("دائن", max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.account.name} - مدين: {self.debit} | دائن: {self.credit}"


@receiver(post_save, sender=JournalEntryDetail)
def update_account_balance(sender, instance, created, **kwargs):
    """
    تحدّث رصيد الحساب بشكل تلقائي عند إنشاء سطر قيد جديد.
    """
    if created:
        account = instance.account
        account.balance += (instance.debit - instance.credit)
        account.save()


# ==============================================================================
# 4) العملاء والموردين
# ==============================================================================
class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم المورد")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم الهاتف")
    email = models.EmailField(null=True, blank=True, verbose_name="البريد الإلكتروني")
    address_line = models.CharField(max_length=255, null=True, blank=True, verbose_name="عنوان الشارع")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="المدينة")
    country = models.CharField(max_length=100, null=True, blank=True, default="المملكة العربية السعودية", verbose_name="البلد")
    vat_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="الرقم الضريبي (إن وجد)")
    cr_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم السجل التجاري (إن وجد)")
    notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات إضافية")

    def __str__(self):
        return self.name or "مورد"

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردون"


class Customer(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم العميل")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم الهاتف")
    email = models.EmailField(null=True, blank=True, verbose_name="البريد الإلكتروني")
    address_line = models.CharField(max_length=255, null=True, blank=True, verbose_name="عنوان الشارع")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="المدينة")
    country = models.CharField(max_length=100, null=True, blank=True, default="المملكة العربية السعودية", verbose_name="البلد")
    vat_number = models.CharField(max_length=15, null=True, blank=True, verbose_name="الرقم الضريبي (إن وجد)")
    cr_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="رقم السجل التجاري (إن وجد)")
    notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات إضافية")
    credit_limit = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="حد الائتمان")

    def __str__(self):
        return self.name or "عميل"

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "عملاء"


# ==============================================================================
# 5) دفتر مساعد للعملاء والموردين (CustomerLedger, SupplierLedger)
# ==============================================================================
class CustomerLedger(models.Model):
    """
    دفتر مساعد (Sub-Ledger) للعملاء. يُسجل كل فاتورة أو دفعة تخص العميل.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="العميل")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    description = models.CharField(max_length=255, verbose_name="الوصف")
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="مدين")
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="دائن")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="الرصيد بعد الحركة")

    payment = models.ForeignKey('CustomerPayment', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='ledger_entries')

    def __str__(self):
        return f"حركة في دفتر العميل {self.customer.name} بتاريخ {self.date}"

    class Meta:
        verbose_name = "حركة دفتر العميل"
        verbose_name_plural = "دفتر مساعد العملاء"


class SupplierLedger(models.Model):
    """
    دفتر مساعد للموردين. يُسجل كل فاتورة أو دفعة تخص المورد.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="المورد")
    date = models.DateField(default=timezone.now, verbose_name="التاريخ")
    description = models.CharField(max_length=255, verbose_name="الوصف")
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="مدين")
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="دائن")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="الرصيد بعد الحركة")

    def __str__(self):
        return f"حركة في دفتر المورد {self.supplier.name} بتاريخ {self.date}"

    class Meta:
        verbose_name = "حركة دفتر المورد"
        verbose_name_plural = "دفتر مساعد الموردين"


def get_default_company():
    # افتراضًا: إعادة أول CompanySettings كافتراضي
    return CompanySettings.objects.first()


# ==============================================================================
# 5) طرق الدفع
# ==============================================================================
class PaymentMethod(models.Model):
    name_ar = models.CharField(max_length=50, unique=True, verbose_name="الاسم العربي")
    name_en = models.CharField(max_length=50, unique=True, verbose_name="الاسم الإنجليزي", null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name="الوصف")

    def __str__(self):
        return self.name_ar

    class Meta:
        verbose_name = "طريقة دفع"
        verbose_name_plural = "طرق الدفع"


# ==============================================================================
# 6) نموذج الفاتورة (Invoice) وعناصرها (InvoiceItem)
# ==============================================================================
class Invoice(models.Model):
    INVOICE_TYPES = [
        ('sales', 'فاتورة مبيعات'),
        ('sales_return', 'مرتجع مبيعات'),
        ('purchase', 'فاتورة مشتريات'),
        ('purchase_return', 'مرتجع مشتريات'),
    ]

    INVOICE_STATUS_CHOICES = [
        ('unpaid', 'غير مدفوعة'),
        ('paid', 'مدفوعة'),
        ('cancelled', 'ملغاة'),
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
        blank=True,
        verbose_name="العميل"
    )
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المورد"
    )
    original_invoice = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        help_text="لفواتير المرتجعات",
        verbose_name="الفاتورة الأصلية"
    )
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='sales', verbose_name="نوع الفاتورة")
    invoice_number = models.CharField(max_length=50, blank=True, verbose_name="رقم الفاتورة")
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='unpaid', verbose_name="حالة الفاتورة",)
    invoice_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ ووقت الفاتورة")
    payment_method = models.ForeignKey(
        'PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="طريقة الدفع"
    )
    notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات")
    return_reason = models.TextField(null=True, blank=True, default='0', verbose_name="سبب المرتجع")

    # الحقول المالية
    subtotal_before_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="الإجمالي قبل الخصم")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="نسبة الخصم %")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="قيمة الخصم")
    subtotal_before_tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="المجموع قبل الضريبة")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'), verbose_name="نسبة الضريبة")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="قيمة الضريبة")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="الصافي")
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True, verbose_name="كود QR")
    due_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    is_posted = models.BooleanField(default=False, verbose_name="تم إنشاء القيد؟")

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        unique_together = ('invoice_type', 'invoice_number')

    def __str__(self):
        return f"{self.invoice_number} - {self.invoice_date}"

    @property
    def is_return_invoice(self):
        return self.invoice_type in ['sales_return', 'purchase_return']

    @property
    def paid_amount(self):
        # في حال عدم ربط الدفعات بالفاتورة مباشرة
        return Decimal('0.00')

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    def generate_invoice_number(self):
        """
        توليد رقم الفاتورة بتسلسل خاص حسب نوع الفاتورة.
        """
        last_invoice = Invoice.objects.filter(invoice_type=self.invoice_type).order_by('-id').first()
        if last_invoice and last_invoice.invoice_number:
            try:
                base_part = last_invoice.invoice_number.split('-')[0]
                base_num = int(base_part)
            except (ValueError, TypeError):
                base_num = 1000
        else:
            base_num = 1000

        candidate = f"{base_num + 10}"
        suffix = 1
        base_candidate = candidate

        while Invoice.objects.filter(invoice_type=self.invoice_type, invoice_number=candidate).exists():
            candidate = f"{base_candidate}-{suffix}"
            suffix += 1

        return candidate

    def save(self, *args, **kwargs):
        # توليد رقم الفاتورة عند عدم وجوده
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        super().save(*args, **kwargs)
        self.calculate_totals()

        # إنشاء القيد المحاسبي لأول مرة إذا لم يكن الفاتورة ملغاة
        if not self.is_posted and self.status != 'cancelled':
            self.create_journal_entry()
            self.is_posted = True
            super().save(update_fields=['is_posted'])

        # إذا كانت مدفوعة وفاتورة مشتريات => إنشاء سند صرف
        if self.status == 'paid' and self.invoice_type in ['purchase', 'purchase_return'] and self.supplier:
            from .models import SupplierPayment
            if not SupplierPayment.objects.filter(notes=f"دفع نقدي لفاتورة #{self.invoice_number}").exists():
                SupplierPayment.objects.create(
                    supplier=self.supplier,
                    payment_type='payment',
                    amount=self.total_amount,
                    date=self.invoice_date.date(),
                    notes=f"دفع نقدي لفاتورة #{self.invoice_number}"
                )

    def calculate_totals(self):
        items = self.invoice_items.all()
        if not items.exists():
            self.subtotal_before_discount = Decimal('0.00')
            self.discount = Decimal('0.00')
            self.discount_percentage = Decimal('0.00')
            self.subtotal_before_tax = Decimal('0.00')
            self.tax_amount = Decimal('0.00')
            self.total_amount = Decimal('0.00')
        else:
            self.subtotal_before_discount = sum(i.total_before_tax for i in items)
            if self.subtotal_before_discount > 0:
                if self.discount_percentage > 0:
                    self.discount = (
                        self.subtotal_before_discount * self.discount_percentage / Decimal('100')
                    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                elif self.discount > 0:
                    self.discount_percentage = (
                        self.discount * 100 / self.subtotal_before_discount
                    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                self.discount = Decimal('0.00')
                self.discount_percentage = Decimal('0.00')

            self.subtotal_before_tax = self.subtotal_before_discount - self.discount
            self.tax_amount = (
                self.subtotal_before_tax * self.tax_rate / Decimal('100')
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.total_amount = self.subtotal_before_tax + self.tax_amount

        super().save(update_fields=[
            'subtotal_before_discount',
            'discount',
            'discount_percentage',
            'subtotal_before_tax',
            'tax_amount',
            'total_amount'
        ])

    def create_journal_entry(self):
        """
        إنشاء القيد المحاسبي الأساسي للفاتورة.
        """
        from .models import JournalEntry, JournalEntryDetail, CustomerLedger, SupplierLedger, ChartOfAccount

        if self.status == 'cancelled':
            return

        accounts = {
            'ar': ChartOfAccount.objects.get(code='1100'),   # الذمم المدينة
            'ap': ChartOfAccount.objects.get(code='2100'),   # الذمم الدائنة
            'revenue': ChartOfAccount.objects.get(code='4000'),
            'purchase': ChartOfAccount.objects.get(code='5000'),
            'tax': ChartOfAccount.objects.get(code='2200'),
            'discount': ChartOfAccount.objects.get(code='4100'),
            'cash': ChartOfAccount.objects.get(code='1000'), # النقدية
        }

        entry = JournalEntry.objects.create(
            date=self.invoice_date.date(),
            description=f"فاتورة {self.invoice_number} - {self.get_invoice_type_display()}"
        )

        # ===================== مبيعات =====================
        if self.invoice_type == 'sales':
            if self.status == 'paid':
                # فاتورة مبيعات مدفوعة
                JournalEntryDetail.objects.create(entry=entry, account=accounts['revenue'], credit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], credit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], debit=self.discount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['cash'], debit=self.total_amount)

                if self.customer:
                    self._update_customer_ledger(
                        debit_val=Decimal('0.00'),
                        credit_val=self.total_amount,
                        description=f"دفعة نقدية لفاتورة مبيعات #{self.invoice_number}"
                    )
            else:
                # فاتورة مبيعات غير مدفوعة
                JournalEntryDetail.objects.create(entry=entry, account=accounts['revenue'], credit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], credit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], debit=self.discount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['ar'], debit=self.total_amount)

                if self.customer:
                    self._update_customer_ledger(
                        debit_val=self.total_amount,
                        credit_val=Decimal('0.00'),
                        description=f"فاتورة مبيعات #{self.invoice_number}"
                    )

        # ===================== مشتريات =====================
        elif self.invoice_type == 'purchase':
            if self.status == 'paid':
                # فاتورة مشتريات مدفوعة
                JournalEntryDetail.objects.create(entry=entry, account=accounts['purchase'], debit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], debit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], credit=self.discount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['cash'], credit=self.total_amount)

                if self.supplier:
                    self._update_supplier_ledger(
                        debit_val=Decimal('0.00'),
                        credit_val=self.total_amount,
                        description=f"دفعة نقدية لفاتورة مشتريات #{self.invoice_number}"
                    )
            else:
                # فاتورة مشتريات غير مدفوعة
                JournalEntryDetail.objects.create(entry=entry, account=accounts['purchase'], debit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], debit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], credit=self.discount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['ap'], credit=self.total_amount)

                if self.supplier:
                    self._update_supplier_ledger(
                        debit_val=Decimal('0.00'),
                        credit_val=self.total_amount,
                        description=f"فاتورة مشتريات #{self.invoice_number}"
                    )

        # ===================== مرتجع مبيعات =====================
        elif self.invoice_type == 'sales_return':
            entry.description += " (مرتجع مبيعات)"
            entry.save()
            if self.status == 'paid':
                JournalEntryDetail.objects.create(entry=entry, account=accounts['revenue'], debit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], debit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], credit=self.discount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['cash'], credit=self.total_amount)

                if self.customer:
                    self._update_customer_ledger(
                        debit_val=self.total_amount,
                        credit_val=Decimal('0.00'),
                        description=f"دفعة نقدية لمرتجع مبيعات #{self.invoice_number}"
                    )
            else:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['revenue'], debit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], debit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], credit=self.discount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['ar'], credit=self.total_amount)

                if self.customer:
                    self._update_customer_ledger(
                        debit_val=Decimal('0.00'),
                        credit_val=self.total_amount,
                        description=f"مرتجع مبيعات #{self.invoice_number}"
                    )

        # ===================== مرتجع مشتريات =====================
        elif self.invoice_type == 'purchase_return':
            entry.description += " (مرتجع مشتريات)"
            entry.save()
            if self.status == 'paid':
                JournalEntryDetail.objects.create(entry=entry, account=accounts['ap'], debit=self.total_amount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['purchase'], credit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], credit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], debit=self.discount)

                if self.supplier:
                    self._update_supplier_ledger(
                        debit_val=self.total_amount,
                        credit_val=Decimal('0.00'),
                        description=f"دفعة نقدية لمرتجع مشتريات #{self.invoice_number}"
                    )
            else:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['ap'], debit=self.total_amount)
                JournalEntryDetail.objects.create(entry=entry, account=accounts['purchase'], credit=self.subtotal_before_tax)
                if self.tax_amount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], credit=self.tax_amount)
                if self.discount > 0:
                    JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], debit=self.discount)

                if self.supplier:
                    self._update_supplier_ledger(
                        debit_val=self.total_amount,
                        credit_val=Decimal('0.00'),
                        description=f"مرتجع مشتريات #{self.invoice_number}"
                    )

    def _update_customer_ledger(self, debit_val, credit_val, description):
        from .models import CustomerLedger
        last_entry = CustomerLedger.objects.filter(customer=self.customer).order_by('-id').first()
        old_balance = last_entry.balance_after if last_entry else Decimal('0.00')
        new_balance = old_balance + debit_val - credit_val

        CustomerLedger.objects.create(
            customer=self.customer,
            date=self.invoice_date,
            description=description,
            debit=debit_val,
            credit=credit_val,
            balance_after=new_balance
        )

    def _update_supplier_ledger(self, debit_val, credit_val, description):
        from .models import SupplierLedger
        last_entry = SupplierLedger.objects.filter(supplier=self.supplier).order_by('-id').first()
        old_balance = last_entry.balance_after if last_entry else Decimal('0.00')
        new_balance = old_balance + debit_val - credit_val

        SupplierLedger.objects.create(
            supplier=self.supplier,
            date=self.invoice_date,
            description=description,
            debit=debit_val,
            credit=credit_val,
            balance_after=new_balance
        )

    def generate_qr_code(self):
        """
        اختياري: إنشاء QR Code بناءً على بيانات الفاتورة.
        """
        if not self.company or not self.company.vat_number:
            return
        timestamp = self.invoice_date.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            1: self.company.name or "",
            2: self.company.vat_number or "",
            3: timestamp,
            4: f"{self.total_amount:.2f}",
            5: f"{self.tax_amount:.2f}"
        }
        tlv_data = bytearray()
        for tag, value in data.items():
            value_bytes = value.encode('utf-8')
            tlv_data += bytes([tag]) + bytes([len(value_bytes)]) + value_bytes

        base64_payload = base64.b64encode(tlv_data).decode('utf-8')
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=2)
        qr.add_data(base64_payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_{self.invoice_number}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def clean(self):
        super().clean()
        # تحقق من اختيار العميل/المورد الصحيح
        if self.invoice_type in ['sales', 'sales_return']:
            if not self.customer:
                raise ValidationError("يجب اختيار عميل لفاتورة المبيعات أو المرتجع.")
            if self.supplier:
                raise ValidationError("لا يمكن اختيار مورد لفاتورة المبيعات أو المرتجع.")
        elif self.invoice_type in ['purchase', 'purchase_return']:
            if not self.supplier:
                raise ValidationError("يجب اختيار مورد لفاتورة المشتريات أو المرتجع.")
            if self.customer:
                raise ValidationError("لا يمكن اختيار عميل لفاتورة المشتريات أو المرتجع.")

        # تحقق من سبب المرتجع
        if self.is_return_invoice and not self.return_reason:
            raise ValidationError("يجب إدخال سبب المرتجع.")

        # لا يمكن أن يكون المجموع سالبًا
        if self.total_amount < 0:
            raise ValidationError("المجموع الكلي لا يمكن أن يكون أقل من صفر.")


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
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
    base_unit = models.ForeignKey(
        'Unit',
        on_delete=models.CASCADE,
        verbose_name="الوحدة الأساسية",
        editable=False,
        null=True,
        blank=True,
    )
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')

    def save(self, *args, **kwargs):
        if not self.product:
            raise ValidationError('يجب اختيار منتج')

        from decimal import Decimal
        self.base_unit = self.product.unit
        conversion_factor = Decimal('1')
        if self.unit and self.unit.conversion_factor:
            conversion_factor = self.unit.conversion_factor

        if not self.unit_price:
            self.unit_price = self.product.price * conversion_factor

        new_base_price = self.unit_price / conversion_factor
        if self.product.price != new_base_price:
            self.product.price = new_base_price
            self.product.save()

        self.total_before_tax = self.quantity * self.unit_price
        self.total = self.total_before_tax
        super().save(*args, **kwargs)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError('الكمية يجب أن تكون أكبر من صفر')
        if not self.product_id:
            raise ValidationError('يجب اختيار منتج')
        super().clean()

    def __str__(self):
        unit_display = ""
        if self.unit:
            unit_display = self.unit.larger_unit_name
        elif self.base_unit:
            unit_display = self.base_unit.abbreviation
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


# ==============================================================================
# 8) نموذج الدفعة للعميل (CustomerPayment) والمورد (SupplierPayment)
# ==============================================================================
class CustomerPayment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('receipt', 'سند قبض من العميل'),
        ('refund', 'سند رد مبلغ للعميل'),
    ]

    voucher_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="رقم السند"
    )
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="العميل"
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='receipt',
        verbose_name="نوع الدفعة"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="مبلغ الدفعة"
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="تاريخ الدفعة"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="ملاحظات"
    )
    payment_method = models.ForeignKey(
        'PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="طريقة الدفع",
        related_name="customer_payments"
    )
    is_posted = models.BooleanField(
        default=False,
        verbose_name="تم إنشاء القيد؟"
    )

    class Meta:
        verbose_name = "دفعة عميل"
        verbose_name_plural = "دفعات العملاء"

    def __str__(self):
        return f"{self.get_payment_type_display()} #{self.voucher_number} - {self.customer.name} - {self.amount}"

    def clean(self):
        super().clean()
        if self.amount <= 0:
            raise ValidationError("المبلغ يجب أن يكون أكبر من صفر.")

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            self.voucher_number = self.generate_voucher_number()

        super().save(*args, **kwargs)

        if not self.is_posted:
            self.create_journal_entry()
            self.is_posted = True
            super().save(update_fields=['is_posted'])

    def generate_voucher_number(self):
        last_voucher = CustomerPayment.objects.order_by('-id').first()
        if last_voucher and last_voucher.voucher_number:
            try:
                last_num = int(last_voucher.voucher_number.split('-')[0])
            except (ValueError, TypeError):
                last_num = 149
        else:
            last_num = 149

        potential_number = f"{last_num + 1}"

        suffix = 1
        base_number = potential_number
        while CustomerPayment.objects.filter(voucher_number=potential_number).exists():
            potential_number = f"{base_number}-{suffix}"
            suffix += 1

        return potential_number

    def create_journal_entry(self):
        from .models import JournalEntry, JournalEntryDetail, CustomerLedger, ChartOfAccount

        entry = JournalEntry.objects.create(
            date=self.date,
            description=f"{self.get_payment_type_display()} #{self.voucher_number} - {self.customer.name}"
        )

        ar_account = ChartOfAccount.objects.get(code='1100')   # الذمم المدينة
        cash_account = ChartOfAccount.objects.get(code='1000') # النقدية

        if self.payment_type == 'receipt':
            # سند قبض
            JournalEntryDetail.objects.create(entry=entry, account=cash_account, debit=self.amount)
            JournalEntryDetail.objects.create(entry=entry, account=ar_account, credit=self.amount)
            self._update_customer_ledger(
                debit_val=Decimal('0.00'),
                credit_val=self.amount,
                description=f"سند قبض #{self.voucher_number}"
            )
        else:
            # سند رد مبلغ
            JournalEntryDetail.objects.create(entry=entry, account=ar_account, debit=self.amount)
            JournalEntryDetail.objects.create(entry=entry, account=cash_account, credit=self.amount)
            self._update_customer_ledger(
                debit_val=self.amount,
                credit_val=Decimal('0.00'),
                description=f"سند رد مبلغ #{self.voucher_number}"
            )

    def _update_customer_ledger(self, debit_val, credit_val, description):
        from .models import CustomerLedger
        last_entry = CustomerLedger.objects.filter(customer=self.customer).order_by('-id').first()
        old_balance = last_entry.balance_after if last_entry else Decimal('0.00')
        new_balance = old_balance + debit_val - credit_val

        CustomerLedger.objects.create(
            customer=self.customer,
            payment=self,
            date=self.date,
            description=description,
            debit=debit_val,
            credit=credit_val,
            balance_after=new_balance
        )


class SupplierPayment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('payment', 'سند صرف للمورد'),
        ('refund', 'المورد يرد مبلغ'),
    ]

    voucher_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name="رقم السند")
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="المورد"
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='payment',
        verbose_name="نوع الدفعة"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="مبلغ الدفعة"
    )
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الدفعة")
    notes = models.TextField(null=True, blank=True, verbose_name="ملاحظات")
    payment_method = models.ForeignKey(
        'PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="طريقة الدفع",
        related_name="supplier_payments"
    )
    is_posted = models.BooleanField(default=False, verbose_name="تم إنشاء القيد؟")

    class Meta:
        verbose_name = "دفعة مورد"
        verbose_name_plural = "دفعات الموردين"

    def __str__(self):
        return f"{self.get_payment_type_display()} #{self.voucher_number} - {self.supplier.name} - {self.amount}"

    def clean(self):
        super().clean()
        if self.amount <= 0:
            raise ValidationError("المبلغ يجب أن يكون أكبر من صفر.")

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            self.voucher_number = self.generate_voucher_number()

        super().save(*args, **kwargs)

        if not self.is_posted:
            self.create_journal_entry()
            self.is_posted = True
            super().save(update_fields=['is_posted'])

    def generate_voucher_number(self):
        last_voucher = SupplierPayment.objects.order_by('-id').first()
        if last_voucher and last_voucher.voucher_number:
            try:
                base_num = int(last_voucher.voucher_number.split('-')[0])
            except (ValueError, TypeError):
                base_num = 149
        else:
            base_num = 149

        candidate = str(base_num + 1)
        suffix = 1
        base_candidate = candidate
        while SupplierPayment.objects.filter(voucher_number=candidate).exists():
            candidate = f"{base_candidate}-{suffix}"
            suffix += 1

        return candidate

    def create_journal_entry(self):
        from .models import JournalEntry, JournalEntryDetail, SupplierLedger, ChartOfAccount

        entry = JournalEntry.objects.create(
            date=self.date,
            description=f"{self.get_payment_type_display()} #{self.voucher_number} - {self.supplier.name}"
        )

        ap_account = ChartOfAccount.objects.get(code='2100')   # الذمم الدائنة (الموردين)
        cash_account = ChartOfAccount.objects.get(code='1000') # النقدية

        if self.payment_type == 'payment':
            # سند صرف
            JournalEntryDetail.objects.create(entry=entry, account=ap_account, debit=self.amount)
            JournalEntryDetail.objects.create(entry=entry, account=cash_account, credit=self.amount)
            self._update_supplier_ledger(
                debit_val=self.amount,
                credit_val=Decimal('0.00'),
                description=f"سند صرف #{self.voucher_number}"
            )
        else:
            # سند رد مبلغ
            JournalEntryDetail.objects.create(entry=entry, account=cash_account, debit=self.amount)
            JournalEntryDetail.objects.create(entry=entry, account=ap_account, credit=self.amount)
            self._update_supplier_ledger(
                debit_val=Decimal('0.00'),
                credit_val=self.amount,
                description=f"سند رد مبلغ #{self.voucher_number}"
            )

    def _update_supplier_ledger(self, debit_val, credit_val, description):
        from .models import SupplierLedger
        last_entry = SupplierLedger.objects.filter(supplier=self.supplier).order_by('-id').first()
        old_balance = last_entry.balance_after if last_entry else Decimal('0.00')
        new_balance = old_balance + debit_val - credit_val

        SupplierLedger.objects.create(
            supplier=self.supplier,
            date=self.date,
            description=description,
            debit=debit_val,
            credit=credit_val,
            balance_after=new_balance
        )


# ==============================================================================
# 9) وظائف التقارير المالية (ميزان مراجعة، كشف حساب عميل/مورد)
# ==============================================================================

def generate_trial_balance():
    """
    ميزان مراجعة بسيط: لكل حساب نجمع المدين والدائن ونحسب الرصيد.
    """
    accounts = ChartOfAccount.objects.all()
    balance_data = []
    for account in accounts:
        debit_sum = JournalEntryDetail.objects.filter(account=account).aggregate(Sum('debit'))['debit__sum'] or Decimal('0.00')
        credit_sum = JournalEntryDetail.objects.filter(account=account).aggregate(Sum('credit'))['credit__sum'] or Decimal('0.00')
        balance = debit_sum - credit_sum
        balance_data.append({
            'account_code': account.code,
            'account_name': account.name,
            'debit': debit_sum,
            'credit': credit_sum,
            'balance': balance
        })
    return balance_data


def get_customer_statement_ledger(customer):
    """
    أفضل ممارسة: عرض كشف الحساب للعميل بالاعتماد على دفتر الأستاذ المساعد (CustomerLedger).
    """
    ledger_entries = CustomerLedger.objects.filter(customer=customer).order_by('date', 'id')

    balance = Decimal('0.00')
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    statement = []

    for entry in ledger_entries:
        balance += (entry.debit - entry.credit)
        total_debit += entry.debit
        total_credit += entry.credit
        statement.append({
            'date': entry.date,
            'description': entry.description,
            'debit': entry.debit,
            'credit': entry.credit,
            'balance': balance
        })

    first_transaction_date = ledger_entries.first().date if ledger_entries.exists() else None

    return {
        'statement': statement,
        'first_transaction_date': first_transaction_date,
        'print_date': timezone.now(),
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': balance
    }


def get_customer_statement_no_ledger(customer):
    """
    يعرض كشف الحساب للعميل عن طريق دمج:
    - الفواتير (sales, sales_return)
    - الدفعات (سند قبض receipt، سند رد مبلغ refund)

    **مع استبعاد الفواتير المدفوعة** حتى لا تظهر كدين للعميل.
    """
    from .models import Invoice, CustomerPayment

    # 1) جلب الفواتير (sales أو sales_return) مع استبعاد الفواتير المدفوعة (status='paid')
    invoices = Invoice.objects.filter(
        customer=customer,
        invoice_type__in=['sales', 'sales_return']
    ).exclude(status='paid').values(
        'id', 'invoice_date', 'invoice_number', 'invoice_type', 'total_amount', 'status'
    )

    # 2) جلب الدفعات (سند قبض أو سند رد مبلغ)
    payments = CustomerPayment.objects.filter(customer=customer).values(
        'id', 'date', 'payment_type', 'amount'
    )

    transactions = []

    # إضافة الفواتير
    for inv in invoices:
        inv_date = inv['invoice_date']
        inv_number = inv['invoice_number']
        inv_type = inv['invoice_type']
        inv_amount = inv['total_amount']

        if inv_type == 'sales':
            # فاتورة مبيعات غير مدفوعة -> مدين
            transactions.append({
                'date': inv_date,
                'description': f"فاتورة مبيعات #{inv_number}",
                'debit': inv_amount,
                'credit': Decimal('0.00'),
            })
        else:
            # مرتجع مبيعات -> دائن
            transactions.append({
                'date': inv_date,
                'description': f"مرتجع مبيعات #{inv_number}",
                'debit': Decimal('0.00'),
                'credit': inv_amount,
            })

    # إضافة الدفعات
    for pay in payments:
        pay_id = pay['id']
        pay_date = pay['date']
        pay_type = pay['payment_type']
        pay_amount = pay['amount']

        if pay_type == 'receipt':
            # سند قبض -> دائن
            transactions.append({
                'date': pay_date,
                'description': f"سند قبض #{pay_id}",
                'debit': Decimal('0.00'),
                'credit': pay_amount
            })
        else:
            # سند رد مبلغ -> مدين
            transactions.append({
                'date': pay_date,
                'description': f"سند رد مبلغ #{pay_id}",
                'debit': pay_amount,
                'credit': Decimal('0.00')
            })

    # فرز الحركات حسب التاريخ
    def sort_key(item):
        d = item['date']
        if isinstance(d, datetime):
            return d
        return datetime(d.year, d.month, d.day)

    transactions.sort(key=sort_key)

    # حساب الرصيد التراكمي
    balance = Decimal('0.00')
    statement = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    for t in transactions:
        total_debit += t['debit']
        total_credit += t['credit']
        balance += (t['debit'] - t['credit'])

        statement.append({
            'date': t['date'],
            'description': t['description'],
            'debit': t['debit'],
            'credit': t['credit'],
            'balance': balance
        })

    return {
        'statement': statement,
        'first_transaction_date': statement[0]['date'] if statement else None,
        'print_date': timezone.now(),
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': balance
    }


def get_supplier_statement(supplier):
    """
    كشف حساب المورد بالاعتماد على دفتر الأستاذ المساعد (SupplierLedger).
    """
    ledger_entries = SupplierLedger.objects.filter(supplier=supplier).order_by('date', 'id')
    return ledger_entries


# ==============================================================================
# 10) نماذج إدارة الوحدات والمنتجات
# ==============================================================================
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


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الصنف")
    description = models.TextField(null=True, blank=True, verbose_name="الوصف")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "صنف المنتج"
        verbose_name_plural = "أصناف المنتجات"


class Product(models.Model):
    name_ar = models.CharField(max_length=255, verbose_name="اسم المنتج بالعربي")
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
    stock = models.PositiveIntegerField(default=999999999, verbose_name="الكمية المتاحة", blank=True)
    low_stock_threshold = models.PositiveIntegerField(default=10, verbose_name="حد التنبيه", null=True, blank=True)
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
