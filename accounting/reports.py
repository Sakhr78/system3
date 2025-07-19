from datetime import timedelta
from django.utils import timezone  
from .forms import *
from invoices.models import *
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

from decimal import Decimal
from django.db.models import Q
# reports.py أو views.py
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime  # تأكد من استيراد datetime  

from datetime import timedelta, datetime
from django.utils import timezone  
from decimal import Decimal
from django.db.models import Sum, Q
from datetime import timedelta, datetime
from django.utils import timezone  
from decimal import Decimal
from django.db.models import Sum, Q

def generate_aging_report():
    """
    تقسّم الفواتير غير المسددة (remaining_amount > 0) حسب المدة المنقضية من تاريخ الاستحقاق (due_date).
    إذا لم يوجد due_date, نفترض invoice_date + 30 يوم.
    نعيد قاموسًا بمفاتيح لا تحتوي على شرطات (للاستخدام السلس في Django template).
    """
    today = timezone.now().date()

    buckets = {
        'range_0_30': [],
        'range_31_60': [],
        'range_61_90': [],
        'range_90_plus': []
    }

    # نركز على فواتير المبيعات (sales, sales_return)
    invoices = Invoice.objects.filter(
        invoice_type__in=['sales', 'sales_return']
    ).all()

    for inv in invoices:
        remaining = inv.remaining_amount
        if remaining <= 0:
            continue

        # تحديد تاريخ الاستحقاق: إذا لم يوجد due_date نفترض invoice_date + 30 يوم
        due_date = inv.due_date if inv.due_date else inv.invoice_date.date() + timedelta(days=30)
        days_past_due = (today - due_date).days
        if days_past_due < 0:
            days_past_due = 0

        if days_past_due <= 30:
            buckets['range_0_30'].append(inv)
        elif 31 <= days_past_due <= 60:
            buckets['range_31_60'].append(inv)
        elif 61 <= days_past_due <= 90:
            buckets['range_61_90'].append(inv)
        else:
            buckets['range_90_plus'].append(inv)

    return buckets
from datetime import datetime
from decimal import Decimal
from django.utils.timezone import now

def get_customer_statement(customer):
    """
    يعرض كشف الحساب للعميل بطريقة محاسبية تشمل:
    - تاريخ العملية
    - الوصف/المرجع
    - قيمة المدين (فاتورة مبيعات أو سند رد مبلغ)
    - قيمة الدائن (سند قبض أو مرتجع مبيعات)
    - الرصيد التراكمي
    - تاريخ أول عملية (first_transaction_date)
    - تاريخ الطباعة (print_date)
    - إجمالي المدين (total_debit)
    - إجمالي الدائن (total_credit)
    - الرصيد النهائي بعد آخر عملية (final_balance)
    """

    # 1) جلب فواتير العميل (مبيعات أو مرتجع مبيعات)
    #   مع معرفة حالة الفاتورة (مدفوعة أم لا) للتمييز بين النقدية والآجلة
    invoices = Invoice.objects.filter(
        customer=customer,
        invoice_type__in=['sales', 'sales_return']
    ).values(
        'id', 'invoice_date', 'invoice_number', 'invoice_type', 'status', 'total_amount'
    )

    # 2) جلب دفعات العميل (سند قبض receipt أو سند رد مبلغ refund)
    payments = CustomerPayment.objects.filter(customer=customer).values(
        'id', 'date', 'payment_type', 'amount'
    )

    # قائمة الحركات
    transactions = []

    # إضافة الفواتير
    for inv in invoices:
        inv_date = inv['invoice_date']
        inv_number = inv['invoice_number']
        inv_type = inv['invoice_type']
        inv_status = inv['status']
        inv_amount = inv['total_amount']

        if inv_type == 'sales':
            # فاتورة مبيعات
            if inv_status == 'paid':
                # ===== الخيار الأول: تجاهل الفاتورة المدفوعة بالكامل =====
                # لأنها لا تزيد رصيد العميل مطلقًا
                # continue

                # ===== الخيار الثاني (اختياري): عرض حركة مزدوجة (فاتورة + سند قبض) =====
                # لتوضيح كل الحركات حتى لو صارت صفر
                transactions.append({
                    'date': inv_date,
                    'description': f"فاتورة مبيعات نقدية #{inv_number}",
                    'debit': inv_amount,
                    'credit': Decimal('0.00'),
                })
                transactions.append({
                    'date': inv_date,
                    'description': f"دفعة نقدية لفاتورة #{inv_number}",
                    'debit': Decimal('0.00'),
                    'credit': inv_amount,
                })

            else:
                # فاتورة مبيعات غير مدفوعة (آجلة) -> مدين
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

    # دالّة فرز للتعامل مع تاريخ date أو datetime
    def sort_key(item):
        d = item['date']
        if isinstance(d, datetime):
            return d
        # إذا كان d من نوع date فقط، نحوله إلى datetime لضمان الفرز الصحيح
        return datetime(d.year, d.month, d.day)

    # ترتيب الحركات حسب التاريخ
    transactions.sort(key=sort_key)

    # حساب الرصيد التراكمي + المجاميع
    balance = Decimal('0.00')
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    statement = []

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

    # استخراج تاريخ أول عملية
    if transactions:
        first_date = transactions[0]['date']
        if isinstance(first_date, datetime):
            first_transaction_date = first_date.date()
        else:
            first_transaction_date = first_date
    else:
        first_transaction_date = None

    return {
        'statement': statement,
        'first_transaction_date': first_transaction_date,
        'print_date': datetime.now(),  # تاريخ طباعة الكشف
        'total_debit': total_debit,
        'total_credit': total_credit,
        'final_balance': balance       # الرصيد بعد آخر عملية
    }
