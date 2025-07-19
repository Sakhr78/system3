# accounting_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from decimal import Decimal
from django.contrib import messages  
from .forms import *
from invoices.models import *





# views.py
def aging_report_view(request):
    from .reports import generate_aging_report
    buckets = generate_aging_report()
    return render(request, 'accounting_app/aging_report.html', {'buckets': buckets})


# views.py
from django.shortcuts import render, get_object_or_404
from .reports import get_customer_statement


def customer_statement_view(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    statement_data = get_customer_statement(customer)

    # إذا لم توجد حركات في statement
    if not statement_data['statement']:
        # يمكنك عرض صفحة خاصة مثل 'empty_statement.html' أو رسالة
        return render(request, 'accounting_app/empty_statement.html', {
            'customer': customer
        })

    context = {
        'customer': customer,
        'statement': statement_data['statement'],
        'first_transaction_date': statement_data['first_transaction_date'],
        'print_date': statement_data['print_date'],
        'total_debit': statement_data['total_debit'],
        'total_credit': statement_data['total_credit'],
        'final_balance': statement_data['final_balance'],
        'company':  CompanySettings.objects.first(),

    }
    return render(request, 'accounting_app/customer_statement.html', context)


from django.shortcuts import render, get_object_or_404
#from .models import PaymentVoucher

#def print_voucher(request, voucher_id):
#    voucher = get_object_or_404(PaymentVoucher, pk=voucher_id)
 #   return render(request, 'voucher_print.html', {'voucher': voucher})



# في ملف views.py
from decimal import Decimal
from django.shortcuts import render, get_object_or_404



from decimal import Decimal
from invoices.models import Invoice

from django.shortcuts import render, get_object_or_404






from decimal import Decimal
from django.shortcuts import render, get_object_or_404

from decimal import Decimal
from django.shortcuts import render, get_object_or_404

from decimal import Decimal
from django.utils.timezone import now
from django.shortcuts import render, get_object_or_404

def print_customer_payment(request, pk):
    """
    دالة لعرض صفحة طباعة سند واحد خاص بالعميل:
      - إذا سند قبض (receipt) => يعامل كدائن (credit)
      - إذا سند رد مبلغ (refund) => يعامل كمدين (debit)
    منطق مطابق لـ get_customer_statement في التعامل مع المبالغ.
    """
    # نجلب السند المطلوب
    payment = get_object_or_404(CustomerPayment, pk=pk)

    # ننشئ قائمة معاملات (transactions) فيها معاملة واحدة
    transactions = []
    if payment.payment_type == 'receipt':
        # سند قبض => دائن
        transactions.append({
            'date': payment.date,
            'description': f"سند قبض #{payment.voucher_number}",
            'debit': Decimal('0.00'),
            'credit': payment.amount
        })
    else:
        # payment_type == 'refund' => مدين
        transactions.append({
            'date': payment.date,
            'description': f"سند رد مبلغ #{payment.voucher_number}",
            'debit': payment.amount,
            'credit': Decimal('0.00')
        })

    # حساب إجمالي المدين والدائن
    total_debit = sum(item['debit'] for item in transactions)
    total_credit = sum(item['credit'] for item in transactions)

    # إذا أردت حساب الرصيد (التراكمي) لكل صف، يمكنك إضافته
    balance = Decimal('0.00')
    statement = []
    for item in transactions:
        balance += item['debit'] - item['credit']
        statement.append({
            'date': item['date'],
            'description': item['description'],
            'debit': item['debit'],
            'credit': item['credit'],
            'balance': balance  # في حال أردت عرضه في القالب
        })

    context = {
        'payment': payment,
        'company':  CompanySettings.objects.first(),

        'statement': statement,        # قائمة بمعاملة واحدة
        'total_debit': total_debit,    # إجمالي المدين
        'total_credit': total_credit,  # إجمالي الدائن
    }
    return render(request, 'payment_print.html', context)






from decimal import Decimal
from django.shortcuts import get_object_or_404, render

def print_supplier_payment(request, pk):
    """
    دالة لعرض صفحة طباعة سند واحد خاص بالمورد:
      - إذا سند صرف (payment) => يعامل كدائن (credit)
      - إذا سند رد مبلغ (refund) => يعامل كمدين (debit)
    """

    # نجلب السند المطلوب
    payment = get_object_or_404(SupplierPayment, pk=pk)

    # ننشئ قائمة معاملات (transactions) فيها معاملة واحدة
    transactions = []
    if payment.payment_type == 'payment':
        # سند صرف => دائن
        transactions.append({
            'date': payment.date,
            'description': f"سند صرف #{payment.voucher_number}",
            'debit': Decimal('0.00'),
            'credit': payment.amount
        })
    else:
        # payment_type == 'refund' => مدين
        transactions.append({
            'date': payment.date,
            'description': f"سند رد مبلغ #{payment.voucher_number}",
            'debit': payment.amount,
            'credit': Decimal('0.00')
        })

    # حساب إجمالي المدين والدائن
    total_debit = sum(item['debit'] for item in transactions)
    total_credit = sum(item['credit'] for item in transactions)

    # إذا أردت حساب الرصيد (التراكمي) لكل صف، يمكنك إضافته
    balance = Decimal('0.00')
    statement = []
    for item in transactions:
        balance += item['debit'] - item['credit']
        statement.append({
            'date': item['date'],
            'description': item['description'],
            'debit': item['debit'],
            'credit': item['credit'],
            'balance': balance  # في حال أردت عرضه في القالب
        })

    context = {
        'payment': payment,
        'company': CompanySettings.objects.first(),

        'statement': statement,        # قائمة بمعاملة واحدة
        'total_debit': total_debit,    # إجمالي المدين
        'total_credit': total_credit,  # إجمالي الدائن
    }
    return render(request, 'payment_print_supplier.html', context)









from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from invoices.models import *

def customer_payment_list(request):
    """
    عرض قائمة مدفوعات العملاء مع إمكانية البحث والتصفية.
    """
    # جلب جميع المدفوعات مرتبة تنازليًا حسب تاريخ الدفعة (الأحدث أولاً)
    payments = CustomerPayment.objects.all().order_by('-date')

    context = {
        'payments': payments,
        'title': 'قائمة سندات القبض من العملاء'
    }
    return render(request, 'payments/customer_payments_list.html', context)


def ajax_search_customer_payments(request):
    """
    تُرجع نتائج البحث في سندات القبض (CustomerPayment) بصيغة JSON
    بناءً على رقم السند، اسم العميل، وتاريخ الدفعة (من/إلى).
    """
    voucher_number = request.GET.get('voucher_number', '').strip()
    customer_name = request.GET.get('customer_name', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # فلترة جميع المدفوعات
    qs = CustomerPayment.objects.all()

    # البحث برقم السند
    if voucher_number:
        qs = qs.filter(voucher_number__icontains=voucher_number)

    # البحث باسم العميل
    if customer_name:
        qs = qs.filter(customer__name__icontains=customer_name)

    # البحث بتاريخ الدفعة (من تاريخ)
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d').date()
            qs = qs.filter(date__gte=date_from_dt)
        except ValueError:
            pass  # إذا كانت صيغة التاريخ غير صالحة، نتجاهل الفلترة

    # البحث بتاريخ الدفعة (إلى تاريخ)
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            qs = qs.filter(date__lte=date_to_dt)
        except ValueError:
            pass

    # ترتيب تنازلي (الأحدث أولاً)
    qs = qs.order_by('-id')

    # تجهيز البيانات للإرجاع بصيغة JSON
    data = []
    for payment in qs:
        data.append({
            'id': payment.id,
            'voucher_number': payment.voucher_number,
            'date': payment.date.strftime('%Y-%m-%d'),  # أو أي تنسيق
            'customer_name': payment.customer.name if payment.customer else '—',
            'payment_type_display': payment.get_payment_type_display(),
            'amount': str(payment.amount),
        })

    return JsonResponse({'results': data})





def delete_customer_payment(request, payment_id):
    """
    دالة لحذف سند قبض للعميل.
    """
    payment = get_object_or_404(CustomerPayment, id=payment_id)

    if request.method == 'POST':
        payment.delete()
        messages.success(request, f"تم حذف سند القبض رقم {payment.voucher_number} بنجاح.")
        return redirect('customer_payment_list')  # عد إلى قائمة السندات

    # إذا GET, يمكن تجاهله لأننا نعرض الـModal في نفس الصفحة
    # لكن يمكنك اختيار عرض رسالة أو redirect
    return redirect('customer_payment_list')





def create_customer_payment(request):
    """
    إنشاء سند قبض جديد للعميل.
    """
    if request.method == 'POST':
        form = CustomerPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            # يمكنك ضبط المنطق الإضافي قبل الحفظ
            payment.save()
            messages.success(request, f"تم إنشاء سند قبض رقم {payment.voucher_number} بنجاح.")
            return redirect('customer_payment_list')  # أو أي صفحة أخرى
    else:
        form = CustomerPaymentForm()

    context = {
        'form': form,
        'title': 'إضافة سند قبض للعميل'
    }
    return render(request, 'payments/create_customer_payment.html', context)



def update_customer_payment(request, payment_id):  
    """  
    تعديل سند قبض موجود للعميل.  
    """  
    payment = get_object_or_404(CustomerPayment, id=payment_id)  

    if request.method == 'POST':  
        form = CustomerPaymentForm(request.POST, instance=payment)  
        if form.is_valid():  
            updated_payment = form.save()  
            messages.success(request, f"تم تحديث سند قبض رقم {updated_payment.voucher_number} بنجاح.")  
            return redirect('customer_payment_list')  # أو أي صفحة أخرى بعد التحديث  
    else:  
        form = CustomerPaymentForm(instance=payment)  

    context = {  
        'form': form,  
        'title': 'تعديل سند قبض للعميل',  
        'payment': payment  # يمكنك تمرير السند لعرض تفاصيله إذا كنت بحاجة لذلك  
    }  
    return render(request, 'payments/create_customer_payment.html', context)  



def create_supplier_payment(request):  
    """  
    إنشاء سند قبض جديد للمورد.  
    """  
    if request.method == 'POST':  
        form = SupplierPaymentForm(request.POST)  
        if form.is_valid():  
            payment = form.save(commit=False)  
            # يمكنك ضبط المنطق الإضافي قبل الحفظ  
            payment.save()  
            messages.success(request, f"تم إنشاء سند قبض للمورد {payment.supplier.name} بنجاح.")  
            return redirect('supplier_payment_list')  # أو أي صفحة أخرى  
    else:  
        form = SupplierPaymentForm()  

    context = {  
        'form': form,  
        'title': 'إضافة سند قبض للمورد'  
    }  
    return render(request, 'payments/create_supplier_payment.html', context)  



def update_supplier_payment(request, payment_id):  
    """  
    تعديل سند قبض موجود للعميل.  
    """  
    payment = get_object_or_404(SupplierPayment, id=payment_id)  

    if request.method == 'POST':  
        form = SupplierPaymentForm(request.POST, instance=payment)  
        if form.is_valid():  
            updated_payment = form.save()  
            messages.success(request, f"تم تحديث سند قبض  رقم {updated_payment.voucher_number} بنجاح.")  
            return redirect('supplier_payment_list')  # أو أي صفحة أخرى بعد التحديث  
    else:  
        form = SupplierPaymentForm(instance=payment)  

    context = {  
        'form': form,  
        'title': 'تعديل سند قبض للعميل',  
        'payment': payment  # يمكنك تمرير السند لعرض تفاصيله إذا كنت بحاجة لذلك  
    }  
    return render(request, 'payments/create_supplier_payment.html', context)  



def supplier_payment_list(request):
    """
    عرض قائمة مدفوعات العملاء مع إمكانية البحث والتصفية.
    """
    # جلب جميع المدفوعات مرتبة تنازليًا حسب تاريخ الدفعة (الأحدث أولاً)
    payments = SupplierPayment.objects.all().order_by('-date')

    context = {
        'payments': payments,
        'title': 'قائمة سندات القبض من الموردين '
    }
    return render(request, 'payments/supplier_payments_list.html', context)


def ajax_search_supplier_payments(request):
    """
    تُرجع نتائج البحث في سندات القبض (CustomerPayment) بصيغة JSON
    بناءً على رقم السند، اسم العميل، وتاريخ الدفعة (من/إلى).
    """
    voucher_number = request.GET.get('voucher_number', '').strip()
    supplier_name = request.GET.get('supplier_name', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # فلترة جميع المدفوعات
    qs = SupplierPayment.objects.all()

    # البحث برقم السند
    if voucher_number:
        qs = qs.filter(voucher_number__icontains=voucher_number)

    # البحث باسم العميل
    if supplier_name:
        qs = qs.filter(supplier__name__icontains=supplier_name)

    # البحث بتاريخ الدفعة (من تاريخ)
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d').date()
            qs = qs.filter(date__gte=date_from_dt)
        except ValueError:
            pass  # إذا كانت صيغة التاريخ غير صالحة، نتجاهل الفلترة

    # البحث بتاريخ الدفعة (إلى تاريخ)
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            qs = qs.filter(date__lte=date_to_dt)
        except ValueError:
            pass

    # ترتيب تنازلي (الأحدث أولاً)
    qs = qs.order_by('-id')

    # تجهيز البيانات للإرجاع بصيغة JSON
    data = []
    for payment in qs:
        data.append({
            'id': payment.id,
            'voucher_number': payment.voucher_number,
            'date': payment.date.strftime('%Y-%m-%d'),  # أو أي تنسيق
            'supplier_name': payment.supplier.name if payment.supplier else '—',
            'payment_type_display': payment.get_payment_type_display(),
            'amount': str(payment.amount),
        })

    return JsonResponse({'results': data})





def delete_supplier_payment(request, payment_id):
    """
    دالة لحذف سند قبض للعميل.
    """
    payment = get_object_or_404(SupplierPayment, id=payment_id)

    if request.method == 'POST':
        payment.delete()
        messages.success(request, f"تم حذف سند القبض رقم {payment.voucher_number} بنجاح.")
        return redirect('supplier_payment_list')  # عد إلى قائمة السندات

    # إذا GET, يمكن تجاهله لأننا نعرض الـModal في نفس الصفحة
    # لكن يمكنك اختيار عرض رسالة أو redirect
    return redirect('supplier_payment_list')
