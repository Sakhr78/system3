from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from invoices.models import *
from invoices.forms import *

import json

from django.db.models import Q
from django.http import JsonResponse

import json  # لتحويل البيانات إلى تنسيق JSON  



def sales_invoice_list(request):
    """
    عرض قائمة فواتير المبيعات مع إمكانية البحث والتصفية حسب اسم العميل وتاريخ الفاتورة.
    """
    # جلب فواتير المبيعات وترتيبها تنازليًا بحسب تاريخ الفاتورة (الأحدث أولاً)
    invoices = Invoice.objects.filter(invoice_type='sales').order_by('-invoice_date')
    
    # خيارات البحث من GET
    customer = request.GET.get('customer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if customer:
        invoices = invoices.filter(customer__name__icontains=customer)
    if start_date:
        invoices = invoices.filter(invoice_date__gte=start_date)
    if end_date:
        invoices = invoices.filter(invoice_date__lte=end_date)
    
    context = {
        'invoices': invoices,
        'title': 'قائمة فواتير المبيعات'
    }
    return render(request, 'sales/invoice_list.html', context)


def create_sales_invoice(request):
    if request.method == 'POST':
        form = SalesInvoiceForm(request.POST, request.FILES)
        formset = InvoiceItemFormSet(request.POST, prefix='items')
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # احفظ الفاتورة مع ربطها بالعميل
                    invoice = form.save(commit=False)
                    invoice.customer = form.cleaned_data['customer']
                    invoice.save()
                    
                    formset.instance = invoice
                    formset.save()
                    
                    # منطق تحديث المخزون (يبقى كما هو)
                    for item_form in formset:
                        if not item_form.cleaned_data.get('DELETE', False):
                            item = item_form.save(commit=False)
                            product = item.product
                            base_quantity = item.quantity
                            
                            if product.stock < base_quantity:
                                raise Exception(f"لا توجد كمية كافية للمنتج {product.name_ar}")
                            product.stock -= int(base_quantity)
                            product.save()

                messages.success(request, 'تم إنشاء فاتورة المبيعات بنجاح.')
                return redirect('sales_invoice_detail', invoice_id=invoice.id)
            except Exception as e:
                messages.error(request, f'حدث خطأ: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        form = SalesInvoiceForm()
        formset = InvoiceItemFormSet(prefix='items')
    
    # الباقي يبقى كما هو
    products = Product.objects.all()
    product_prices = {str(product.id): str(product.price) for product in products}
    product_units = {str(product.id): product.unit.abbreviation for product in products}
    conversion_units = {
        str(conv.id): {
            "abbr": conv.larger_unit_name if hasattr(conv, 'larger_unit_name') else conv.conversion_unit,
            "factor": str(conv.conversion_factor)
        }
        for conv in UnitConversion.objects.all()
    }
    context = {
        'form': form,
        'formset': formset,
        'title': 'إنشاء فاتورة مبيعات - النظام المحاسبي',
        'product_prices': json.dumps(product_prices),
        'product_units': json.dumps(product_units),
        'conversion_units': json.dumps(conversion_units),
    }
    return render(request, 'sales/create_invoice.html', context)


def update_sales_invoice(request, invoice_id):
    """
    دالة عرض لتحديث فاتورة مبيعات موجودة.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        form = SalesInvoiceForm(request.POST, request.FILES, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix='items')
   #     print("request.POST content:", request.POST.dict())

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.save(commit=False)
                    invoice.customer = form.cleaned_data['customer']
                    invoice.save()

                    # تخزين العناصر القديمة لمقارنة التعديلات
                    old_items = {item.id: item for item in invoice.invoice_items.all()}
                    formset.instance = invoice
                    formset_items = formset.save(commit=False)

                    for item in formset_items:
                        if item.id:
                            old_item = old_items.pop(item.id, None)
                        else:
                            old_item = None

                        product = item.product
                        base_quantity = item.quantity

                        if old_item:
                            # حساب الفرق بين الكمية الجديدة والقديمة
                            quantity_difference = base_quantity - old_item.quantity
                            product.stock -= int(quantity_difference)
                        else:
                            if product.stock < base_quantity:
                                raise Exception(f"لا توجد كمية كافية للمنتج {product.name_ar}")
                            product.stock -= int(base_quantity)

                        if product.stock < 0:
                            raise Exception(f"الكمية في المخزون للمنتج {product.name_ar} أصبحت أقل من صفر.")

                        item.save()
                        product.save()

                    # استعادة المخزون للعناصر التي تم حذفها
                 #   for old_item in old_items.values():
                 #       product = old_item.product
                 #       product.stock += int(old_item.quantity)
                 #       product.save()
                  #      old_item.delete()

                    invoice.calculate_totals()
                    invoice.save()

                    messages.success(request, 'تم تحديث فاتورة المبيعات بنجاح.')
                    return redirect('sales_invoice_detail', invoice_id=invoice.id)

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء تحديث الفاتورة: {str(e)}')
        else:
            print("Formset Errors:", formset.errors)
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
    else:
        form = SalesInvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice, prefix='items')

    products = Product.objects.all()
    product_prices = {str(product.id): str(product.price) for product in products}
    product_units = {str(product.id): product.unit.abbreviation for product in products}
    conversion_units = {
        str(conv.id): {
            "abbr": conv.larger_unit_name if hasattr(conv, 'larger_unit_name') else conv.conversion_unit,
            "factor": str(conv.conversion_factor)
        }
        for conv in UnitConversion.objects.all()
    }
    context = {
        'form': form,
        'formset': formset,
        'title': 'تحديث فاتورة مبيعات - النظام المحاسبي',
        'invoice_id': invoice_id,
        'product_prices': json.dumps(product_prices),
        'product_units': json.dumps(product_units),
        'conversion_units': json.dumps(conversion_units),
    }
    return render(request, 'sales/edit_invoice.html', context)





def delete_sales_invoice(request, invoice_id):
    """
    دالة لحذف فاتورة مبيعات.
    يتم التأكد من أن الفاتورة من نوع 'sales'.
    عند تأكيد الحذف (POST)، يتم حذف الفاتورة وإعادة التوجيه إلى صفحة قائمة فواتير المبيعات.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, invoice_type='sales')
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, "تم حذف فاتورة المبيعات بنجاح.")
        return redirect('sales_invoice_list')  # تأكد من وجود مسار URL مناسب لقائمة فواتير المبيعات






def sales_invoice_detail(request, invoice_id):

    invoice = get_object_or_404(Invoice, id=invoice_id, invoice_type='sales')
    context = {
        'invoice': invoice,
        'invoice_items': invoice.invoice_items.all(),  # أو الاستعلام المناسب
        'title': f'تفاصيل فاتورة المبيعات {invoice.invoice_number}'
    }
    return render(request, 'sales/invoice_detail.html', context)














def list_sales_returns(request):
  
    context = {
        'title': 'قائمة مرتجعات المبيعات (بحث ديناميكي)',
    }
    return render(request, 'sales_returns/list.html', context)




def ajax_search_sales_returns(request):
    invoice_number = request.GET.get('invoice_number', '').strip()
    customer_name = request.GET.get('customer_name', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # فلترة فواتير المرتجع فقط
    qs = Invoice.objects.filter(invoice_type='sales_return')

    if invoice_number:
        qs = qs.filter(invoice_number__icontains=invoice_number)

    if customer_name:
        qs = qs.filter(customer__name__icontains=customer_name)

    if date_from:
        qs = qs.filter(invoice_date__date__gte=date_from)

    if date_to:
        qs = qs.filter(invoice_date__date__lte=date_to)

    # ترتيب تنازلي (الأحدث أولاً)
    qs = qs.order_by('-id')

    data = []
    for invoice in qs:
        data.append({
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d %H:%M'),
            'customer_name': invoice.customer.name if invoice.customer else '—',
            'return_reason': invoice.return_reason if invoice.return_reason else '—',
            'total_amount': str(invoice.total_amount),
        })

    return JsonResponse({'results': data})



def create_sales_return_invoice(request):
    """
    دالة لإنشاء فاتورة مرتجع مبيعات (Sales Return) جديدة.
    """

        # نموذج Formset لعناصر الفاتورة
    InvoiceItemFormSet = inlineformset_factory(
        Invoice, InvoiceItem,
        form=InvoiceItemForm,
        extra=1,
        can_delete=True,
        # أي إعدادات إضافية تحتاجها
    )
    if request.method == 'POST':
        form = SalesReturnForm(request.POST, request.FILES)
        formset = InvoiceItemFormSet(request.POST, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # 1) إنشاء الفاتورة (نوعها sales_return)
                    invoice = form.save(commit=False)
                    # تأكد من وجود عميل
                    invoice.customer = form.cleaned_data['customer']
                    invoice.save()

                    # 2) حفظ عناصر الفاتورة وربطها بها
                    formset.instance = invoice
                    items = formset.save(commit=False)

                    # 3) منطق تحديث المخزون للمرتجع
                    #    بما أن هذه فاتورة مرتجع مبيعات، سنزيد مخزون المنتجات
                    for item_form in formset:
                        if not item_form.cleaned_data.get('DELETE', False):
                            item = item_form.save(commit=False)
                            product = item.product
                            base_quantity = item.quantity

                            # نضيف الكمية إلى المخزون (عكس فاتورة المبيعات)
                            product.stock += int(base_quantity)
                            product.save()

                    # 4) احذف العناصر التي عليها علامة DELETE في الـFormset
                    for deleted_form in formset.deleted_forms:
                        if deleted_form.instance.pk:
                            deleted_item = deleted_form.instance
                            # في حالة حُذفت عنصر تم إضافته بالخطأ
                            # نعيد المخزون الذي أضفناه؟
                            # إذا أردت التعامل مع ذلك، يمكنك عكس العملية
                            deleted_item.delete()

                    # 5) استدعِ formset.save() لحفظ باقي الحقول في InvoiceItem
                    formset.save()

                    # 6) الرسائل والتوجيه
                    messages.success(request, 'تم إنشاء فاتورة مرتجع المبيعات بنجاح.')
                    return redirect('sales_return_invoice_detail', invoice_id=invoice.id)

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء فاتورة المرتجع: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
    else:
        # الطلب GET: عرض نموذج فارغ
        form = SalesReturnForm()
        formset = InvoiceItemFormSet(prefix='items')

    # جلب بيانات المنتجات للـJavaScript
    products = Product.objects.all()
    product_prices = {str(product.id): str(product.price) for product in products}
    product_units = {str(product.id): product.unit.abbreviation for product in products}
    conversion_units = {
        str(conv.id): {
            "abbr": conv.larger_unit_name if hasattr(conv, 'larger_unit_name') else conv.conversion_unit,
            "factor": str(conv.conversion_factor)
        }
        for conv in UnitConversion.objects.all()
    }

    context = {
        'form': form,
        'formset': formset,
        'title': 'إنشاء مرتجع مبيعات - النظام المحاسبي',
        'product_prices': json.dumps(product_prices),
        'product_units': json.dumps(product_units),
        'conversion_units': json.dumps(conversion_units),
    }
    return render(request, 'sales_returns/create_sales_return.html', context)







def update_sales_return_invoice(request, invoice_id):
    """
    دالة لتعديل فاتورة مرتجع المبيعات الموجودة مسبقًا.
    - تعرض نموذج الفاتورة (SalesReturnForm) + عناصر الفاتورة (InvoiceItemFormSet)
    - تعالج منطق المخزون بحيث يتم إضافة الكمية إلى المخزون (بما أنه مرتجع).
    - إذا غيّر المستخدم الكمية أو حذف العنصر، يتم ضبط المخزون accordingly.
    """
    # جلب الفاتورة والتأكد من أنها فاتورة مرتجع مبيعات
    invoice = get_object_or_404(Invoice, id=invoice_id, invoice_type='sales_return')

    if request.method == 'POST':
        form = SalesReturnForm(request.POST, request.FILES, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # حفظ بيانات الفاتورة الرئيسية
                    invoice = form.save(commit=False)
                    # مثلاً لو أردت التأكد من أن invoice_type ما زال 'sales_return'
                    invoice.invoice_type = 'sales_return'
                    invoice.save()

                    # جلب العناصر القديمة من قاعدة البيانات قبل التعديل
                    old_items = {item.id: item for item in invoice.invoice_items.all()}

                    # اربط الـFormset بالفاتورة واحصل على العناصر المحدثة
                    formset.instance = invoice
                    formset_items = formset.save(commit=False)

                    # 1) معالجة العناصر الموجودة في formset
                    for item_form in formset:
                        # إذا المستخدم اختار حذف العنصر
                        if item_form.cleaned_data.get('DELETE', False):
                            # إذا العنصر قديم (له id)
                            if item_form.instance.id:
                                old_item = old_items.pop(item_form.instance.id, None)
                                if old_item:
                                    product = old_item.product
                                    # الكمية التي كانت مضافة للمخزون يجب إزالتها
                                    product.stock -= int(old_item.quantity)
                                    product.save()
                                # احذف العنصر من قاعدة البيانات
                                item_form.instance.delete()
                        else:
                            # عنصر موجود أو جديد
                            item = item_form.save(commit=False)
                            if item.id:
                                # عنصر قديم تم تحديثه
                                old_item = old_items.pop(item.id, None)
                                if old_item:
                                    product = item.product
                                    # احسب فرق الكمية (الجديدة - القديمة)
                                    diff = item.quantity - old_item.quantity
                                    # إذا diff موجب => نضيف diff للمخزون
                                    # إذا diff سالب => ننقص المخزون
                                    product.stock += int(diff)
                                    product.save()
                            else:
                                # عنصر جديد بالكامل
                                product = item.product
                                product.stock += int(item.quantity)
                                product.save()

                            item.save()

                    # 2) العناصر التي لم تعد موجودة في formset (لم تظهر في POST)
                    #    لكنها كانت موجودة في قاعدة البيانات
                    #    عادةً هذه الحالة تعني أن المستخدم حذفها فعليًا
                    #    ولكن إذا قمت بمعالجة الحذف أعلاه، قد لا تصل لهذه المرحلة.
                    for old_item in old_items.values():
                        product = old_item.product
                        product.stock -= int(old_item.quantity)
                        product.save()
                        old_item.delete()

                    # 3) تحديث إجماليات الفاتورة
                    invoice.calculate_totals()
                    invoice.save()

                    messages.success(request, 'تم تحديث فاتورة مرتجع المبيعات بنجاح.')
                    return redirect('sales_return_invoice_detail', invoice_id=invoice.id)

            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء تحديث فاتورة المرتجع: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج.')
    else:
        # الطلب GET: عرض البيانات الحالية في النموذج
        form = SalesReturnForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice, prefix='items')

    # يمكنك جلب بيانات المنتجات للجافاسكريبت (للحسابات الديناميكية)
    products = Product.objects.all()
    product_prices = {str(p.id): str(p.price) for p in products}
    product_units = {str(p.id): p.unit.abbreviation for p in products}
    # إذا لديك وحدات تحويل
    from .models import UnitConversion
    conversion_units = {
        str(conv.id): {
            "abbr": conv.larger_unit_name if hasattr(conv, 'larger_unit_name') else conv.conversion_unit,
            "factor": str(conv.conversion_factor)
        }
        for conv in UnitConversion.objects.all()
    }

    context = {
        'form': form,
        'formset': formset,
        'title': 'تعديل فاتورة مرتجع المبيعات',
        'invoice_id': invoice_id,
        'product_prices': json.dumps(product_prices),
        'product_units': json.dumps(product_units),
        'conversion_units': json.dumps(conversion_units),
    }
    return render(request, 'sales_returns/edit_sales_return.html', context)



def delete_sales_return_invoice(request, invoice_id):
    """
    دالة لحذف فاتورة مبيعات.
    يتم التأكد من أن الفاتورة من نوع 'sales'.
    عند تأكيد الحذف (POST)، يتم حذف الفاتورة وإعادة التوجيه إلى صفحة قائمة فواتير المبيعات.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, invoice_type='sales_return')
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, "تم حذف فاتورة المبيعات بنجاح.")
        return redirect('list_sales_returns')  # تأكد من وجود مسار URL مناسب لقائمة فواتير المبيعات



def sales_return_invoice_detail(request, invoice_id):

    invoice = get_object_or_404(Invoice, id=invoice_id, invoice_type='sales_return')
    context = {
        'invoice': invoice,
        'invoice_items': invoice.invoice_items.all(),  # أو الاستعلام المناسب
        'title': f'تفاصيل فاتورة المبيعات {invoice.invoice_number}'
    }
    return render(request, 'sales/invoice_detail.html', context)











import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def get_invoice_data(request):
    """
    يعيد بيانات الفاتورة الأصلية (من نوع sales) بصيغة JSON،
    يشمل ذلك: العميل، طريقة الدفع، الملاحظات، البنود (قائمة المنتجات والكميات).
    """
    invoice_id = request.GET.get('invoice_id')
    invoice = get_object_or_404(Invoice, pk=invoice_id, invoice_type='sales')
    
    # تجهيز البيانات الأساسية
    data = {
        'customer_id': invoice.customer.id if invoice.customer else None,
        'payment_method_id': invoice.payment_method.id if invoice.payment_method else None,
        'notes': invoice.notes or '',
        'items': []
    }
    
    # إضافة بنود الفاتورة
    for item in invoice.invoice_items.all():
        data['items'].append({
            'product_id': item.product.id,
            'product_name': str(item.product),
            'quantity': str(item.quantity),
            'unit_price': str(item.unit_price),
            'tax_rate': str(item.tax_rate),
        })
    
    return JsonResponse(data, safe=False)




from .forms import *

def get_invoice_details(request):
    invoice_id = request.GET.get('invoice_id')
    invoice = get_object_or_404(Invoice, id=invoice_id, invoice_type='sales')
    items = [
        {
            'product_id': item.product.id,
            'product_name': str(item.product),
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'tax_rate': float(item.tax_rate)
        } for item in invoice.invoice_items.all()
    ]
    data = {
        'customer_id': invoice.customer.id,
        'invoice_items': items,
        'invoice_number': invoice.invoice_number,
        'discount_percentage': invoice.discount_percentage if hasattr(invoice, 'discount_percentage') else None,
    }
    return JsonResponse(data)

def get_invoices_by_customer(request):
    customer_id = request.GET.get('customer_id')
    if customer_id:
        invoices = Invoice.objects.filter(customer_id=customer_id, invoice_type='sales')
        data = [{
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
        } for invoice in invoices]
        return JsonResponse({'invoices': data})
    return JsonResponse({'error': 'طلب غير صالح'}, status=400)

def create_sales_return_invoice(request):
    original_id = request.GET.get('original_id')
    if request.method == 'POST':
        form = SalesReturnInvoiceForm(request.POST, request.FILES)
        formset = SalesReturnInvoiceItemInlineFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.invoice_type = 'sales_return'
            invoice.calculate_totals()  # إذا كان لديك دالة لحساب الإجماليات
            invoice.save()
            formset.instance = invoice
            formset.save()
            return redirect(reverse('invoice_detail', kwargs={'invoice_id': invoice.id}))
        return render(request, 'sales_return_invoice_form.html', {'form': form, 'formset': formset})
    
    invoice = Invoice(invoice_type='sales_return')
    if original_id:
        original_inv = get_object_or_404(Invoice, pk=original_id, invoice_type='sales')
        invoice.original_invoice = original_inv
        invoice.customer = original_inv.customer
        invoice.payment_method = original_inv.payment_method
        invoice.notes = f"نسخة عن فاتورة {original_inv.invoice_number}"
        if hasattr(original_inv, 'discount_percentage'):
            invoice.discount_percentage = original_inv.discount_percentage

    form = SalesReturnInvoiceForm(instance=invoice)
    formset = SalesReturnInvoiceItemInlineFormSet(instance=invoice)
    return render(request, 'sales_return_invoice_form.html', {'form': form, 'formset': formset})


def delete_all_products(request):
    """
    دالة لحذف جميع المنتجات من قاعدة البيانات.
    """
    if request.method == 'POST':
        try:
            Product.objects.all().delete()
            messages.success(request, "تم حذف جميع المنتجات بنجاح.")
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف المنتجات: {str(e)}')
        return redirect('product_list')  # تأكد من وجود مسار URL مناسب لقائمة المنتجات
