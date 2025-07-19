from django.db import models, IntegrityError
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum

# لمكتبات إنشاء QR code (اختياري)
import base64
import qrcode
from io import BytesIO
from django.core.files.base import File
from datetime import timezone as dt_timezone

from mptt.models import MPTTModel, TreeForeignKey  # إذا كنت تستخدم شجرة الحسابات
from django.contrib.auth import get_user_model

User = get_user_model()

# بعض النماذج التي لديك مسبقًا:
# - CompanySettings
# - Customer
# - Supplier
# - PaymentMethod
# - ChartOfAccount
# - JournalEntry, JournalEntryDetail
# - CustomerLedger, SupplierLedger
# - ...الخ

# ---------------------------------------------------------------------------
# مثال: دالة لإرجاع الشركة الافتراضية
def get_default_company():
    return CompanySettings.objects.first()

# ---------------------------------------------------------------------------
# نموذج سند الصرف للمورد (مثال)؛ تأكد من وجوده في نفس ملف النماذج
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
        # توليد رقم السند عند الحاجة
        if not self.voucher_number:
            self.voucher_number = self.generate_voucher_number()

        super().save(*args, **kwargs)

        # إنشاء القيد المحاسبي إن لم يكن منشأً بعد
        if not self.is_posted:
            self.create_journal_entry()
            self.is_posted = True
            super().save(update_fields=['is_posted'])

    def generate_voucher_number(self):
        """
        توليد رقم سند صرف بتسلسل تلقائي، مع معالجة اللاحقة إذا حدث تعارض.
        """
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
        # لو وجد نفس الرقم تمامًا نضيف لاحقة
        while SupplierPayment.objects.filter(voucher_number=candidate).exists():
            candidate = f"{base_candidate}-{suffix}"
            suffix += 1

        return candidate

    def create_journal_entry(self):
        """
        إنشاء قيد اليومية وتفاصيله، وتحديث دفتر المورد.
        """
        from .models import JournalEntry, JournalEntryDetail, SupplierLedger, ChartOfAccount

        entry = JournalEntry.objects.create(
            date=self.date,
            description=f"{self.get_payment_type_display()} #{self.voucher_number} - {self.supplier.name}"
        )

        ap_account = ChartOfAccount.objects.get(code='2100')  # الذمم الدائنة (الموردين)
        cash_account = ChartOfAccount.objects.get(code='1000')  # النقدية

        if self.payment_type == 'payment':
            # Dr AP, Cr Cash
            JournalEntryDetail.objects.create(entry=entry, account=ap_account, debit=self.amount)
            JournalEntryDetail.objects.create(entry=entry, account=cash_account, credit=self.amount)
            self._update_supplier_ledger(
                debit_val=self.amount,
                credit_val=Decimal('0.00'),
                description=f"سند صرف #{self.voucher_number}"
            )
        else:
            # رد مبلغ => Dr Cash, Cr AP
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


# ---------------------------------------------------------------------------
# نموذج الفاتورة (مع منع تكرار إنشاء سند صرف أكثر من مرة)
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
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='unpaid', verbose_name="حالة الفاتورة")
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

    # يمكننا إضافة قيد uniqueness حسب نوع الفاتورة + رقمها
    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        unique_together = ('invoice_type', 'invoice_number')  # يضمن عدم تكرار رقم الفاتورة لنفس النوع

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
        # نبحث فقط عن آخر فاتورة من نفس النوع
        last_invoice = Invoice.objects.filter(invoice_type=self.invoice_type).order_by('-id').first()
        if last_invoice and last_invoice.invoice_number:
            try:
                # نفترض أن الجزء الأساسي من الرقم هو قبل أي '-' إن وجد
                base_part = last_invoice.invoice_number.split('-')[0]
                base_num = int(base_part)
            except (ValueError, TypeError):
                base_num = 1000
        else:
            base_num = 1000

        candidate = f"{base_num + 10}"
        suffix = 1
        base_candidate = candidate

        # لو وجد رقم فاتورة مطابق تمامًا، نضيف لاحقة
        while Invoice.objects.filter(invoice_type=self.invoice_type, invoice_number=candidate).exists():
            candidate = f"{base_candidate}-{suffix}"
            suffix += 1

        return candidate

    def save(self, *args, **kwargs):
        # توليد رقم الفاتورة عند عدم وجوده
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        # حفظ أولي
        super().save(*args, **kwargs)

        # حساب المجاميع
        self.calculate_totals()

        # إذا لم تُنشأ القيد بعد، والفاتورة ليست ملغاة => ننشئ القيد
        if not self.is_posted and self.status != 'cancelled':
            self.create_journal_entry()
            self.is_posted = True
            super().save(update_fields=['is_posted'])

        # إذا كانت مدفوعة وفاتورة مشتريات => إنشاء سند صرف مرة واحدة فقط
        # نتحقق مثلًا من عدم وجود سند بنفس الملاحظات (أو طريقة أخرى)
        if self.status == 'paid' and self.invoice_type in ['purchase', 'purchase_return'] and self.supplier:
            from .models import SupplierPayment
            # نتحقق هل يوجد سند صرف تم إنشاؤه "تلقائيًا" لنفس الفاتورة
            if not SupplierPayment.objects.filter(notes=f"دفع تلقائي لفاتورة #{self.invoice_number}").exists():
                # إنشاء سند صرف
                SupplierPayment.objects.create(
                    supplier=self.supplier,
                    payment_type='payment',
                    amount=self.total_amount,
                    date=self.invoice_date.date(),
                    notes=f"دفع تلقائي لفاتورة #{self.invoice_number}"
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
                    self.discount = (self.subtotal_before_discount
                                     * self.discount_percentage / Decimal('100')
                                    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                elif self.discount > 0:
                    self.discount_percentage = (self.discount * 100
                                                / self.subtotal_before_discount
                                               ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                self.discount = Decimal('0.00')
                self.discount_percentage = Decimal('0.00')

            self.subtotal_before_tax = self.subtotal_before_discount - self.discount
            self.tax_amount = (self.subtotal_before_tax
                               * self.tax_rate / Decimal('100')
                              ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.total_amount = self.subtotal_before_tax + self.tax_amount

        # لا تنس حفظ
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

        # الحسابات الأساسية
        accounts = {
            'ar': ChartOfAccount.objects.get(code='1100'),       # الذمم المدينة
            'ap': ChartOfAccount.objects.get(code='2100'),       # الذمم الدائنة
            'revenue': ChartOfAccount.objects.get(code='4000'),  # الإيرادات
            'purchase': ChartOfAccount.objects.get(code='5000'), # المشتريات
            'tax': ChartOfAccount.objects.get(code='2200'),      # الضريبة
            'discount': ChartOfAccount.objects.get(code='4100'), # الخصم
        }

        entry = JournalEntry.objects.create(
            date=self.invoice_date.date(),
            description=f"فاتورة {self.invoice_number} - {self.get_invoice_type_display()}"
        )

        # حسب نوع الفاتورة
        if self.invoice_type == 'sales':
            # Dr AR, Cr Revenue (+tax, +discount)
            JournalEntryDetail.objects.create(entry=entry, account=accounts['revenue'], credit=self.subtotal_before_tax)
            if self.tax_amount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], credit=self.tax_amount)
            if self.discount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], debit=self.discount)
            JournalEntryDetail.objects.create(entry=entry, account=accounts['ar'], debit=self.total_amount)

            # تحديث دفتر العميل
            if self.customer:
                self._update_customer_ledger(
                    debit_val=self.total_amount,
                    credit_val=Decimal('0.00'),
                    description=f"فاتورة مبيعات #{self.invoice_number}"
                )

        elif self.invoice_type == 'purchase':
            # Dr Purchase, Cr AP
            JournalEntryDetail.objects.create(entry=entry, account=accounts['purchase'], debit=self.subtotal_before_tax)
            if self.tax_amount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], debit=self.tax_amount)
            if self.discount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], credit=self.discount)
            JournalEntryDetail.objects.create(entry=entry, account=accounts['ap'], credit=self.total_amount)

            # تحديث دفتر المورد
            if self.supplier:
                self._update_supplier_ledger(
                    debit_val=Decimal('0.00'),
                    credit_val=self.total_amount,
                    description=f"فاتورة مشتريات #{self.invoice_number}"
                )

        elif self.invoice_type == 'sales_return':
            entry.description += " (مرتجع مبيعات)"
            entry.save()
            # Dr Revenue, Cr AR
            JournalEntryDetail.objects.create(entry=entry, account=accounts['revenue'], debit=self.subtotal_before_tax)
            if self.tax_amount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], debit=self.tax_amount)
            if self.discount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], credit=self.discount)
            JournalEntryDetail.objects.create(entry=entry, account=accounts['ar'], credit=self.total_amount)

            # تحديث دفتر العميل
            if self.customer:
                self._update_customer_ledger(
                    debit_val=Decimal('0.00'),
                    credit_val=self.total_amount,
                    description=f"مرتجع مبيعات #{self.invoice_number}"
                )

        elif self.invoice_type == 'purchase_return':
            entry.description += " (مرتجع مشتريات)"
            entry.save()
            # Dr AP, Cr Purchase
            JournalEntryDetail.objects.create(entry=entry, account=accounts['ap'], debit=self.total_amount)
            JournalEntryDetail.objects.create(entry=entry, account=accounts['purchase'], credit=self.subtotal_before_tax)
            if self.tax_amount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['tax'], credit=self.tax_amount)
            if self.discount > 0:
                JournalEntryDetail.objects.create(entry=entry, account=accounts['discount'], debit=self.discount)

            # تحديث دفتر المورد
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
        """
        التحقق من صحة البيانات قبل الحفظ.
        """
        super().clean()
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

        if self.is_return_invoice and not self.return_reason:
            raise ValidationError("يجب إدخال سبب المرتجع.")

        if self.total_amount < 0:
            raise ValidationError("المجموع الكلي لا يمكن أن يكون أقل من صفر.")





# ---------------------------------------------------------------------------
# عناصر الفاتورة
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
        default=1,
        verbose_name='الكمية'
    )
    base_unit = models.ForeignKey(
        'Unit',
        on_delete=models.CASCADE,
        editable=False,
        null=True,
        blank=True,
        verbose_name="الوحدة الأساسية"
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
        default=0,
        verbose_name="السعر لكل وحدة"
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

    def __str__(self):
        return f"{self.product.name_ar} - {self.quantity}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("الكمية يجب أن تكون أكبر من صفر.")
        if not self.product_id:
            raise ValidationError("يجب اختيار منتج.")
        super().clean()

    def save(self, *args, **kwargs):
        if not self.product:
            raise ValidationError("يجب اختيار منتج.")
        # ضبط الوحدة الأساسية
        self.base_unit = self.product.unit

        # حساب معامل التحويل
        conversion_factor = Decimal('1')
        if self.unit and self.unit.conversion_factor:
            conversion_factor = self.unit.conversion_factor

        # إذا لم يحدد سعر، نعتمده من المنتج * معامل التحويل
        if not self.unit_price:
            self.unit_price = self.product.price * conversion_factor

        # إذا أردنا تحديث سعر المنتج الأساسي
        new_base_price = self.unit_price / conversion_factor
        if self.product.price != new_base_price:
            self.product.price = new_base_price
            self.product.save()

        # حساب الإجمالي قبل الضريبة
        self.total_before_tax = self.quantity * self.unit_price
        # مبدئياً نضع total = قبل الضريبة
        self.total = self.total_before_tax
        super().save(*args, **kwargs)


@receiver(post_save, sender=InvoiceItem)
def update_invoice_totals(sender, instance, **kwargs):
    """
    بعد حفظ عنصر فاتورة، نعيد حساب إجماليات الفاتورة + توليد QR code.
    """
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
