from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse

from django.contrib.auth.decorators import login_required, user_passes_test

# مكتبات ReportLab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# مكتبات Django
from .models import *
from inventory.forms import *

from decimal import Decimal
import io
from datetime import datetime, timedelta
import os
from django.conf import settings



from django.http import JsonResponse




# دالة تسجيل الخطوط العربية
def register_arabic_font():
    """تسجيل الخط العربي"""
    try:
        # تحديد المسار الدقيق للخطوط
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts')
        
        regular_font = os.path.join(font_path, 'NotoSansArabic-Regular.ttf')
        bold_font = os.path.join(font_path, 'NotoSansArabic-Bold.ttf')
        
        # التحقق من وجود الخطوط
        if not os.path.exists(regular_font):
            print(f"خطأ: الخط {regular_font} غير موجود")
            return False
        
        if not os.path.exists(bold_font):
            print(f"خطأ: الخط {bold_font} غير موجود")
            return False
        
        # تسجيل الخطوط
        pdfmetrics.registerFont(TTFont('Arabic', regular_font))
        pdfmetrics.registerFont(TTFont('Arabic-Bold', bold_font))
        
        return True
    except Exception as e:
        print(f"خطأ في تسجيل الخط: {e}")
        return False


@login_required(login_url='login')
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def invoice_dashboard(request):
    # تصفية الفواتير حسب النوع
    sales_invoices = Invoice.objects.filter(invoice_type__in=['sales'])
    purchase_invoices = Invoice.objects.filter(invoice_type__in=['purchase'])
    
    sales_stats = {
        'invoice_count': sales_invoices.count(),
        'total_sales': sales_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'recent_invoices': sales_invoices.order_by('-invoice_date')[:10]
    }
    purchase_stats = {
        'invoice_count': purchase_invoices.count(),
        'total_purchases': purchase_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'recent_invoices': purchase_invoices.order_by('-invoice_date')[:10],
        'total_tax': purchase_invoices.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
    }
    
    context = {
        'sales_stats': sales_stats,
        'purchase_stats': purchase_stats,
        'title': 'لوحة تحكم الفواتير'
    }
    return render(request, 'dashboard.html', context)



from django.forms import formset_factory
from .models import Invoice, InvoiceItem, Customer, Product
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
import json

from .forms import *
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction







import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import Invoice

# تأكد من وجود دوال تسجيل الخط العربي ومعالجة النص العربي
import os  
from django.conf import settings  
from reportlab.pdfbase import pdfmetrics  
from reportlab.pdfbase.ttfonts import TTFont  

# في ملف views.py

import io
import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from .models import Invoice, InvoiceItem # تأكد من استيراد InvoiceItem
from django.urls import reverse

from num2words import num2words
from decimal import Decimal, ROUND_HALF_UP

# ==============================================================================
# 1) دالة تحويل المبلغ إلى نص عربي مفصل (تبقى كما هي)
# ==============================================================================
def convert_amount_to_arabic_words(amount):
    """
    تحويل مبلغ مالي إلى نص عربي مفصل بالريال والهللة بشكل ديناميكي.
    """
    try:
        amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError):
        return "المبلغ غير صالح"

    riyals = int(amount)
    halalas = int((amount - riyals) * 100)

    riyals_text = num2words(riyals, lang='ar').replace(" فاصلة", "").strip()
    final_text = f"{riyals_text} ريال سعودي"

    if halalas > 0:
        halalas_text = num2words(halalas, lang='ar').replace(" فاصلة", "").strip()
        final_text += f" و {halalas_text} هللة"
    else:
        final_text += " فقط لا غير"

    return final_text

# ==============================================================================
# 2) تحديث دالة عرض الفاتورة لاستخدام الدالة الجديدة وتمرير البيانات الصحيحة
# ==============================================================================
def invoice_print_view(request, invoice_id):
    """
    عرض صفحة HTML لطباعة الفاتورة مع تحويل القيم إلى نصوص مكتوبة.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # --- هذا هو الجزء الذي تم تعديله ---
    # نستخدم الدالة الجديدة لتحويل المبلغ الإجمالي فقط
    total_in_words_formatted = convert_amount_to_arabic_words(invoice.total_amount)
    
    # حساب إجمالي الكمية بالوحدة الأساسية (ياردة)
    total_base_quantity = sum(item.base_quantity_calculated for item in invoice.invoice_items.all())

    context = {
        'invoice': invoice,
        'title': f'طباعة الفاتورة {invoice.invoice_number}',
        
        # تمرير النص المنسق والجديد إلى القالب
        'total_words': total_in_words_formatted,
        
        # تمرير إجمالي الكمية بالوحدة الأساسية (ياردة)
        'total_base_quantity': total_base_quantity,
    }
    
    # تأكد من أن اسم القالب صحيح
    return render(request, 'print.html', context)











import qrcode
import base64
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Invoice
from datetime import timezone as dt_timezone

def generate_qr_code_view(request, invoice_id):
    """
    View لتوليد صورة QR Code ديناميكيًا بناءً على بيانات الفاتورة.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # التحقق من وجود البيانات اللازمة لتوليد الكود
    if not invoice.company or not invoice.company.vat_number:
        # يمكنك إرجاع صورة فارغة أو رسالة خطأ
        return HttpResponse("بيانات الشركة غير مكتملة لتوليد QR Code", status=404)

    # 1. تجميع بيانات TLV (Tag-Length-Value)
    timestamp = invoice.invoice_date.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        1: invoice.company.name or "",
        2: invoice.company.vat_number or "",
        3: timestamp,
        4: f"{invoice.total_amount:.2f}",
        5: f"{invoice.tax_amount:.2f}"
    }
    
    tlv_data = bytearray()
    for tag, value in data.items():
        value_bytes = str(value).encode('utf-8')
        tlv_data += bytes([tag]) + bytes([len(value_bytes)]) + value_bytes

    # 2. تحويل إلى Base64
    base64_payload = base64.b64encode(tlv_data).decode('utf-8')

    # 3. توليد صورة QR Code
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=2)
    qr.add_data(base64_payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # 4. حفظ الصورة في الذاكرة وإرجاعها كـ HttpResponse
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    # إرجاع الصورة مباشرة في الاستجابة
    return HttpResponse(buffer.getvalue(), content_type='image/png')







        




from django.db.models import Sum, Avg, Count
from django.shortcuts import render
from .models import Invoice

from django.shortcuts import render
from django.db.models import Sum, Avg, Count
from .models import Invoice


@login_required(login_url='login')
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def dashboard(request):
    """
    لوحة تحكم تعرض إحصائيات فواتير المبيعات والمشتريات، بما في ذلك إجمالي الضريبة.
    """
    # فواتير المبيعات
    sales_invoices = Invoice.objects.filter(invoice_type='sales')
    sales_stats = {
        'invoice_count': sales_invoices.aggregate(count=Count('id'))['count'] or 0,
        'total_sales': sales_invoices.aggregate(total=Sum('total_amount'))['total'] or 0,
        'avg_invoice': sales_invoices.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        'total_tax': sales_invoices.aggregate(tax=Sum('tax_amount'))['tax'] or 0,
        'recent_invoices': sales_invoices.order_by('-invoice_date')[:5],
    }
    
    # فواتير المشتريات
    purchase_invoices = Invoice.objects.filter(invoice_type='purchase')
    purchase_stats = {
        'invoice_count': purchase_invoices.aggregate(count=Count('id'))['count'] or 0,
        'total_purchases': purchase_invoices.aggregate(total=Sum('total_amount'))['total'] or 0,
        'avg_invoice': purchase_invoices.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        'total_tax': purchase_invoices.aggregate(tax=Sum('tax_amount'))['tax'] or 0,
        'recent_invoices': purchase_invoices.order_by('-invoice_date')[:5],
    }
    
    context = {
        'sales_stats': sales_stats,
        'purchase_stats': purchase_stats,
    }
    return render(request, 'invoices/dashboard.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages




def supplier_list(request):
    """
    دالة عرض قائمة الموردين.
    تقوم بجلب جميع سجلات الموردين من قاعدة البيانات وتمريرها إلى القالب.
    """
    suppliers = Supplier.objects.all().order_by('name')
    context = {
        'suppliers': suppliers,
        'title': 'قائمة الموردين'
    }
    return render(request, 'suppliers/supplier_list.html', context)



def create_supplier(request):

    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إضافة المورد بنجاح.")
            return redirect('supplier_list')  # تأكد من وجود URL supplier_list أو استبدله بالمسار المناسب
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = SupplierForm()
    
    context = {
        'form': form,
        'title': 'إضافة مورد جديد'
    }
    return render(request, 'suppliers/create_supplier.html', context)

def edit_supplier(request, supplier_id):
    """
    دالة لتعديل بيانات مورد قائم.
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل بيانات المورد بنجاح.")
            return redirect('supplier_list')
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = SupplierForm(instance=supplier)

    context = {
        'form': form,
        'title': 'تعديل بيانات المورد',
        'supplier': supplier
    }
    return render(request, 'suppliers/edit_supplier.html', context)


def delete_supplier(request, supplier_id):
    """
    دالة لحذف مورد محدد.
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)
    supplier.delete()
    messages.success(request, "تم حذف المورد بنجاح.")
    return redirect('supplier_list')




def supplier_detail(request, supplier_id):
    """
    دالة عرض تفاصيل مورد محدد.
    تسترجع بيانات المورد من قاعدة البيانات وتعرضها في قالب supplier_detail.html.
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)
    context = {
        'supplier': supplier,
        'title': 'تفاصيل المورد'
    }
    return render(request, 'suppliers/supplier_detail.html', context)




def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    context = {
        'customers': customers,
        'title': 'قائمة العملاء'
    }
    return render(request, 'customers/customer_list.html', context)



def create_customer(request):
    """
    دالة لإنشاء عميل جديد.
    تعرض النموذج لإدخال بيانات العميل، وتقوم بحفظها عند التحقق من صحتها.
    """
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إضافة العميل بنجاح.")
            return redirect('customer_list')  # تأكد من وجود URL customer_list أو استبدله بالمسار المناسب
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'إضافة عميل جديد'
    }
    return render(request, 'customers/create_customer.html', context)

def edit_customer(request, customer_id):
    """
    دالة لتعديل بيانات مورد قائم.
    """
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل بيانات العميل بنجاح.")
            return redirect('customer_list')
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = CustomerForm(instance=customer)

    context = {
        'form': form,
        'title': 'تعديل بيانات المورد',
        'customer': customer
    }
    return render(request, 'customers/edit_customer.html', context)


def delete_customer(request, customer_id):
    """
    دالة لحذف مورد محدد.
    """
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    messages.success(request, "تم حذف المورد بنجاح.")
    return redirect('customer_list')




def customer_detail(request, customer_id):
    """
    دالة عرض تفاصيل مورد محدد.
    تسترجع بيانات المورد من قاعدة البيانات وتعرضها في قالب supplier_detail.html.
    """
    customer = get_object_or_404(Customer, id=customer_id)
    context = {
        'customer': customer,
        'title': 'تفاصيل المورد'
    }
    return render(request, 'customers/customer_detail.html', context)











from django.views.decorators.csrf import csrf_exempt


# views.py
@csrf_exempt
def ajax_create_or_update_payment_method(request):
    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        if edit_id:
            pm = get_object_or_404(PaymentMethod, id=edit_id)
            form = PaymentMethodForm(request.POST, instance=pm)
        else:
            form = PaymentMethodForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                obj = form.save()
            return JsonResponse({
                'status': 'success',
                'id': obj.id,
                'name_ar': obj.name_ar,
                'name_en': obj.name_en or '',
                'description': obj.description or ''
            })
        else:
            errors = {field: str(err[0]) for field, err in form.errors.items()}
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)

@csrf_exempt
def ajax_delete_payment_method(request):
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        pm = get_object_or_404(PaymentMethod, id=delete_id)
        pm.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)


def manage_payment_methods(request):
    """
    صفحة واحدة تعرض قائمة طرق الدفع، مع أزرار إضافة/تعديل/حذف تعمل بـAJAX + Modal
    """
    methods = PaymentMethod.objects.all().order_by('-id')
    context = {
        'methods': methods,
        'title': 'إدارة طرق الدفع (AJAX + Modal)'
    }
    return render(request, 'payment_methods/payment_methods.html', context)
























def company_settings(request):
    # محاولة الحصول على إعدادات الشركة الحالية أو إنشاء واحدة جديدة
    company_settings, created = CompanySettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=company_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ إعدادات الشركة بنجاح')
            return redirect('company_settings')
    else:
        form = CompanySettingsForm(instance=company_settings)
    
    context = {
        'form': form,
        'title': 'إعدادات الشركة',
        'is_settings_page': True,  # لتمييز أن هذه صفحة الإعدادات
    }
    return render(request, 'company_settings.html', context)
