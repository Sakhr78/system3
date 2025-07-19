from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from invoices.models import *
from .forms import *

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction



from django.contrib import messages

# قائمة المنتجات

from django.http import JsonResponse


def manage_products(request):
    products = Product.objects.all().order_by('-id')
    form = ProductForm()  # إنشاء النموذج لتضمينه في القالب
    context = {
        'products': products,
        'title': 'إدارة المنتجات (AJAX + Modal)',
        'form': form,  # تمرير النموذج إلى القالب
    }
    return render(request, 'inventory/products.html', context)
    




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




def manage_categories(request):
    """
    يعرض صفحة إدارة التصنيفات ويقوم بتمرير جميع التصنيفات
    ونموذج التصنيف إلى القالب.
    """
    categories = ProductCategory.objects.all().order_by('-id')
    category_form = ProductCategoryForm()
    context = {
        'categories': categories,
        'category_form': category_form,
        'title': 'إدارة المجموعات'
    }
    return render(request, 'inventory/category.html', context)


@csrf_exempt
def ajax_create_or_update_category(request):
    """
    يقوم بإنشاء تصنيف جديد أو تحديث تصنيف قائم باستخدام AJAX.
    في حال وجود edit_id يتم التحديث، وإلا يتم إنشاء تصنيف جديد.
    """
    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        if edit_id:
            category = get_object_or_404(ProductCategory, id=edit_id)
            form = ProductCategoryForm(request.POST, instance=category)
        else:
            form = ProductCategoryForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                obj = form.save()
            return JsonResponse({
                'status': 'success',
                'id': obj.id,
                'name': obj.name,
                'description': obj.description,
            })
        else:
            errors = {field: str(err[0]) for field, err in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            })
    return JsonResponse({'status': 'invalid request'}, status=400)


@csrf_exempt
def ajax_delete_category(request):
    """
    يقوم بحذف التصنيف بناءً على الـ delete_id المرسل عبر POST.
    """
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        category = get_object_or_404(ProductCategory, id=delete_id)
        category.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)












































@csrf_exempt
def ajax_create_or_update_unit(request):
    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        if edit_id:
            unit = get_object_or_404(Unit, id=edit_id)
            form = UnitForm(request.POST, instance=unit)
        else:
            form = UnitForm(request.POST)
            
        if form.is_valid():
            with transaction.atomic():
                obj = form.save()
            return JsonResponse({
                'status': 'success',
                'id': obj.id,
                'name': obj.name,
                'abbreviation': obj.abbreviation,
                'template': obj.template,
                'is_active': obj.is_active
            })
        else:
            errors = {field: str(err[0]) for field, err in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            })
    return JsonResponse({'status': 'invalid request'}, status=400)


@csrf_exempt
def ajax_delete_unit(request):
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        unit = get_object_or_404(Unit, id=delete_id)
        unit.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)


@csrf_exempt
def ajax_create_or_update_conversion(request):
    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        if edit_id:
            conversion = get_object_or_404(UnitConversion, id=edit_id)
            form = UnitConversionForm(request.POST, instance=conversion)
        else:
            form = UnitConversionForm(request.POST)
            
        if form.is_valid():
            with transaction.atomic():
                obj = form.save()
            return JsonResponse({
                'status': 'success',
                'id': obj.id,
                'base_unit': obj.base_unit.id,
                'larger_unit_name': obj.larger_unit_name,
                'larger_unit_abbreviation': obj.larger_unit_abbreviation,
                'conversion_factor': str(obj.conversion_factor)
            })
        else:
            errors = {field: str(err[0]) for field, err in form.errors.items()}
            return JsonResponse({
                'status': 'error',
                'errors': errors
            })
    return JsonResponse({'status': 'invalid request'}, status=400)


@csrf_exempt
def ajax_delete_conversion(request):
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        conversion = get_object_or_404(UnitConversion, id=delete_id)
        conversion.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)



# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .forms import UnitWithConversionForm

   
def create_unit_with_multiple_conversions(request):
    """
    دالة لإنشاء وحدة أساسية وإضافة عدة تحويلات لها في نفس الصفحة.
    """
    if request.method == 'POST':
        unit_form = UnitForm(request.POST)
        # وحدة مؤقتة (غير محفوظة) لتمريرها إلى الـFormSet
        temp_unit = Unit()
        conversion_formset = UnitConversionInlineFormSet(request.POST, instance=temp_unit)

        if unit_form.is_valid() and conversion_formset.is_valid():
            with transaction.atomic():
                new_unit = unit_form.save()  # احفظ الوحدة
                conversion_formset.instance = new_unit
                conversion_formset.save()    # احفظ التحويلات
            messages.success(request, "تم إنشاء الوحدة مع عدة تحويلات بنجاح.")
            return redirect('manage_units')  # عدّل الرابط حسب مشروعك
        else:
            messages.error(request, "يرجى تصحيح الأخطاء في النموذج.")
    else:
        unit_form = UnitForm()
        temp_unit = Unit()
        conversion_formset = UnitConversionInlineFormSet(instance=temp_unit)

    context = {
        'unit_form': unit_form,
        'conversion_formset': conversion_formset,
        'title': 'إنشاء وحدة مع عدة تحويلات'
    }
    return render(request, 'inventory/create_unit_with_conversion.html', context)




# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UnitForm, UnitConversionInlineFormSet

def manage_units(request):
    """
    تعرض صفحة تحتوي على:
    1) جدول الوحدات الموجودة.
    2) زر "إضافة وحدة جديدة" يفتح مودال لإنشاء وحدة + عدة تحويلات.
    """
    # جلب كل الوحدات لعرضها في الجدول
    units = Unit.objects.all().order_by('-id')
    
    # نموذج فارغ للوحدة سنستخدمه في المودال
    unit_form = UnitForm()
    
    # FormSet فارغ للتحويلات
    # (لن نستخدمه مباشرة في هذا القالب، لكن يمكن إذا أردت عرضه جاهزًا)
    temp_unit = Unit()  # كائن مؤقت
    conversion_formset = UnitConversionInlineFormSet(instance=temp_unit, prefix='conversions')

    context = {
        'units': units,
        'title': 'إدارة الوحدات',
        'unit_form': unit_form,
        'conversion_formset': conversion_formset,
        'conversions': UnitConversion.objects.all().order_by('-id')
    }
    return render(request, 'inventory/create_unit_with_conversion.html', context)

@csrf_exempt
def ajax_create_or_update_unit(request):
    """
    إنشاء أو تعديل وحدة + تحويلاتها عبر AJAX.
    edit_id => تعديل
    لا يوجد => إنشاء
    """
    if request.method == 'POST':
        edit_id = request.POST.get('edit_id', '').strip()

        if edit_id:
            # تعديل
            unit_obj = get_object_or_404(Unit, id=edit_id)
            unit_form = UnitForm(request.POST, instance=unit_obj)
            conversion_formset = UnitConversionInlineFormSet(
                request.POST,
                instance=unit_obj,
                prefix='conversions'
            )
        else:
            # إنشاء
            unit_form = UnitForm(request.POST)
            # سنحفظ الوحدة أولاً، ثم ننشئ formset
            conversion_formset = None

        if unit_form.is_valid():
            with transaction.atomic():
                saved_unit = unit_form.save(commit=False)
                saved_unit.save()

                if not edit_id:
                    # الآن نصنع الـFormSet على الوحدة الجديدة
                    conversion_formset = UnitConversionInlineFormSet(
                        request.POST,
                        instance=saved_unit,
                        prefix='conversions'
                    )

                if conversion_formset and conversion_formset.is_valid():
                    conversion_formset.save()
                    data = {
                        'status': 'success',
                        'id': saved_unit.id,
                        'name': saved_unit.name,
                        'abbreviation': saved_unit.abbreviation,
                        'template': saved_unit.template,
                        'is_active': 'نشط' if saved_unit.is_active else 'غير نشط',
                        'is_edit': bool(edit_id),
                    }
                    return JsonResponse(data)
                elif conversion_formset:
                    # أخطاء في FormSet
                    formset_errors = []
                    for f in conversion_formset.forms:
                        if f.errors:
                            formset_errors.append(f.errors.as_json())
                    return JsonResponse({
                        'status': 'invalid',
                        'errors': {'formset': formset_errors}
                    }, status=400)
                else:
                    # لا يوجد formset => لا تحويلات
                    data = {
                        'status': 'success',
                        'id': saved_unit.id,
                        'name': saved_unit.name,
                        'abbreviation': saved_unit.abbreviation,
                        'template': saved_unit.template,
                        'is_active': 'نشط' if saved_unit.is_active else 'غير نشط',
                        'is_edit': bool(edit_id),
                    }
                    return JsonResponse(data)
        else:
            # أخطاء في النموذج الرئيسي
            form_errors = {field: str(err[0]) for field, err in unit_form.errors.items()}
            return JsonResponse({'status': 'invalid', 'errors': form_errors}, status=400)
    
    return JsonResponse({'status': 'invalid request'}, status=400)


@csrf_exempt
def ajax_get_unit_data(request, unit_id):
    """
    يعيد بيانات الوحدة وتحويلاتها في شكل JSON.
    """
    unit_obj = get_object_or_404(Unit, id=unit_id)
    data = {
        'id': unit_obj.id,
        'name': unit_obj.name,
        'abbreviation': unit_obj.abbreviation,
        'template': unit_obj.template,
        'is_active': unit_obj.is_active,
        'conversions': []
    }
    for c in unit_obj.conversions.all():
        data['conversions'].append({
            'id': c.id,  # مفتاح أساسي
            'larger_unit_name': c.larger_unit_name,
            'larger_unit_abbreviation': c.larger_unit_abbreviation,
            'conversion_factor': str(c.conversion_factor),
        })
    return JsonResponse({'status': 'success', 'data': data})




@csrf_exempt
def ajax_delete_unit(request):
    """
    حذف وحدة كاملة عبر AJAX.
    """
    if request.method == 'POST':
        delete_id = request.POST.get('delete_id')
        unit_obj = get_object_or_404(Unit, id=delete_id)
        unit_obj.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)



@csrf_exempt
def ajax_delete_conversion(request):
    """
    دالة لحذف سجل تحويل (UnitConversion) محدد عبر AJAX.
    """
    if request.method == 'POST':
        conversion_id = request.POST.get('conversion_id')
        # تحقق من وجود المعرف
        if not conversion_id:
            return JsonResponse({'status': 'error', 'message': 'لم يتم توفير معرف التحويل'}, status=400)
        
        # حاول جلب سجل التحويل
        conversion_obj = get_object_or_404(UnitConversion, id=conversion_id)
        conversion_obj.delete()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'invalid request'}, status=400)
    