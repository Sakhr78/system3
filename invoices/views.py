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

# مكتبات دعم العربية
import arabic_reshaper
from bidi.algorithm import get_display

# مكتبات Django
from .models import *
from decimal import Decimal
import io
from datetime import datetime, timedelta
import os
from django.conf import settings



from django.http import JsonResponse


# دالة معالجة النص العربي
def process_arabic_text(text):
    """معالجة النص العربي للطباعة"""
    if not text:
        return ''
    
    # إعادة ترتيب الحروف العربية
    reshaped_text = arabic_reshaper.reshape(text)
    
    # عكس اتجاه النص
    bidi_text = get_display(reshaped_text)
    
    return bidi_text

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

def register_arabic_font():  
    """  
    مثال لتسجيل الخط العربي باستخدام ReportLab.  
    يجب توفير مسار الخط المناسب.  
    """  
    try:  
        # مسارات الخطوط باستخدام STATIC/FONT  
        arabic_font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'NotoNaskhArabic-Regular.ttf')  
        arabic_bold_font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'NotoNaskhArabic-Bold.ttf')  

        # تسجيل الخطوط  
        pdfmetrics.registerFont(TTFont('Arabic', arabic_font_path))  
        pdfmetrics.registerFont(TTFont('Arabic-Bold', arabic_bold_font_path))  
    except Exception as e:  
        # التعامل مع حالة الخطأ  
        print(f"Error registering font: {e}")


import arabic_reshaper
from bidi.algorithm import get_display

def process_arabic_text(text):
    """
    تعيد الدالة النص العربي بعد إعادة تشكيله وتصحيحه ليظهر بشكل مناسب.
    - تستخدم مكتبة arabic_reshaper لإعادة تشكيل الحروف العربية.
    - تستخدم مكتبة python-bidi لضبط اتجاه النص بحيث يُعرض من اليمين إلى اليسار.
    """
    try:
        # إعادة تشكيل النص العربي
        reshaped_text = arabic_reshaper.reshape(text)
        # تعديل اتجاه النص ليصبح من اليمين إلى اليسار
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        # في حال حدوث خطأ يمكن طباعة رسالة وإرجاع النص الأصلي
        print(f"Error processing Arabic text: {e}")
        return text


import io
import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from .models import Invoice
from django.urls import reverse




from .utils import convert_number_to_words

def invoice_print_view(request, invoice_id):
    """
    عرض صفحة HTML لطباعة الفاتورة مع تحويل القيم إلى نصوص مكتوبة
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)

    context = {
        'invoice': invoice,
        'title': f'طباعة الفاتورة {invoice.invoice_number}',
        'subtotal_words': convert_number_to_words(invoice.subtotal_before_discount),
        'discount_words': convert_number_to_words(invoice.discount),
        'subtotal_after_discount_words': convert_number_to_words(invoice.subtotal_before_tax),
        'tax_words': convert_number_to_words(invoice.tax_amount),
        'total_words': convert_number_to_words(invoice.total_amount),
    }
    return render(request, 'print.html', context)



def print_invoice(request, invoice_id):
    register_arabic_font()
    
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice_items = invoice.invoice_items.all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)
    
    # إعداد أنماط النصوص باستخدام الخطوط العربية
    title_style = ParagraphStyle(
        'TitleStyle',
        fontName='Arabic-Bold',
        fontSize=18,
        alignment=1,  # توسيط
        textColor=colors.black,
        spaceAfter=10
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        fontName='Arabic',
        fontSize=12,
        alignment=1,
        textColor=colors.black,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        fontName='Arabic',
        fontSize=10,
        alignment=2,  # محاذاة لليمين
        textColor=colors.black,
        spaceAfter=6
    )
    
    elements = []
    
    # رأس الفاتورة: شعار الشركة (إذا وُجد) مع اسم ومعلومات الشركة
  # """ if invoice.company and invoice.company.logo:
   #     try:
   #         logo_path = invoice.company.logo.path
    #        logo = Image(logo_path, width=100, height=100)
    #        logo.hAlign = 'CENTER'
    ##        elements.append(logo)
      #  except Exception as e:
     #       print(f"Error loading logo: {e}")
    
    if invoice.company:
        company_name = process_arabic_text(invoice.company.name)
        company_details = []
        if invoice.company.address:
            company_details.append(process_arabic_text(invoice.company.address))
        if invoice.company.phone:
            company_details.append(process_arabic_text(invoice.company.phone))
        company_info = " | ".join(company_details)
    else:
        company_name = process_arabic_text("الشركة غير محددة")
        company_info = ""
    
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph(company_info, header_style))
    elements.append(Spacer(1, 12))
    
    # معلومات الفاتورة
    invoice_info_data = [
        [process_arabic_text('رقم الفاتورة:'), invoice.invoice_number],
        [process_arabic_text('تاريخ الفاتورة:'), invoice.invoice_date.strftime('%Y-%m-%d')],
        [process_arabic_text('اسم العميل:'), process_arabic_text(invoice.customer.name if invoice.customer else 'غير محدد')]
    ]
    invoice_info_table = Table(invoice_info_data, colWidths=[120, 300])
    invoice_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (0,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    elements.append(invoice_info_table)
    elements.append(Spacer(1, 12))
    
    # جدول العناصر
    items_data = [
        [
            process_arabic_text('المنتج'),
            process_arabic_text('الوحدة'),
            process_arabic_text('الكمية'),
            process_arabic_text('السعر الوحدوي'),
            process_arabic_text('المجموع')
        ]
    ]
    for item in invoice_items:
        if item.unit and hasattr(item.unit, 'larger_unit_name') and item.unit.larger_unit_name:
            unit_display = process_arabic_text(item.unit.larger_unit_name)
        else:
            unit_display = process_arabic_text(item.base_unit.abbreviation)
        items_data.append([
            process_arabic_text(item.product.name_ar),
            unit_display,
            str(item.quantity),
            f'{item.unit_price:.2f} ر.س',
            f'{item.total:.2f} ر.س'
        ])
    items_table = Table(items_data, colWidths=[180, 80, 80, 80, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 12))
    
    # ملخص الحسابات
    financial_data = [
        [process_arabic_text('المجموع الفرعي:'), f'{invoice.subtotal_before_discount:.2f} ر.س'],
        [process_arabic_text('قيمة الخصم:'), f'{invoice.discount:.2f} ر.س'],
        [process_arabic_text('المجموع قبل الضريبة:'), f'{invoice.subtotal_before_tax:.2f} ر.س'],
        [process_arabic_text('مبلغ الضريبة:'), f'{invoice.tax_amount:.2f} ر.س'],
        [process_arabic_text('المجموع النهائي:'), f'{invoice.total_amount:.2f} ر.س']
    ]
    financial_table = Table(financial_data, colWidths=[200, 100])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (0,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Arabic'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 20))
    
    # توقيع وختم الفاتورة
    elements.append(Paragraph(process_arabic_text("توقيع المحاسب: ____________________   ختم الشركة: ____________________"), normal_style))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{invoice.invoice_number}.pdf'
    return response


import json
from django.shortcuts import render, get_object_or_404
from .models import Invoice, Product, UnitConversion
# يُفترض أن تكون نماذج Invoice و Product و UnitConversion معرفة في models.py



        




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
            return redirect('supplier_detail', supplier_id=supplier.id)
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
            return redirect('customer_detail', customer_id=customer.id)
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










from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .forms import ProductForm
from .models import Product

# قائمة المنتجات
def product_list(request):
    products = Product.objects.all().order_by('-id')
    context = {
        'products': products,
        'title': 'قائمة المنتجات'
    }
    return render(request, 'products/product_list.html', context)

# إنشاء منتج جديد
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "تم إضافة المنتج بنجاح")
            return redirect('product_list')
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = ProductForm()
    context = {
        'form': form,
        'title': 'إضافة منتج جديد'
    }
    return render(request, 'products/product_form.html', context)

# تعديل منتج
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل المنتج بنجاح")
            return redirect('product_list')
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        form = ProductForm(instance=product)
    context = {
        'form': form,
        'title': f'تعديل المنتج: {product.name_ar}'
    }
    return render(request, 'products/product_form.html', context)

# حذف منتج
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "تم حذف المنتج بنجاح.")
        return redirect('product_list')



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







from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Product
from .forms import ProductForm

@csrf_exempt
def ajax_create_or_update_product(request):
    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        if edit_id:
            product = get_object_or_404(Product, id=edit_id)
            form = ProductForm(request.POST, instance=product)
        else:
            form = ProductForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                obj = form.save()
            return JsonResponse({
                'status': 'success',
                'id': obj.id,
                'name_ar': obj.name_ar,
                'serial_number': obj.serial_number or '',
                'category': obj.category.id,  # أو obj.category.name إذا كنت تريد الاسم
                'unit': obj.unit.id,          # أو obj.unit.name إذا كنت تريد الاسم
                'price': str(obj.price),       # تحويل Decimal إلى String
                'description': obj.description or '',
                'stock': obj.stock,
                'low_stock_threshold': obj.low_stock_threshold
            })
        else:
            errors = {field: str(err[0]) for field, err in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            })
    return JsonResponse({'status': 'invalid request'}, status=400)

@csrf_exempt
def ajax_delete_product(request):
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        product = get_object_or_404(Product, id=delete_id)
        product.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)

def manage_products(request):
    products = Product.objects.all().order_by('-id')
    form = ProductForm()  # إنشاء النموذج لتضمينه في القالب
    context = {
        'products': products,
        'title': 'إدارة المنتجات (AJAX + Modal)',
        'form': form,  # تمرير النموذج إلى القالب
    }
    return render(request, 'inventory/products.html', context)
    




















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
