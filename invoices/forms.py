from django import forms
from .models import *
from django.forms.models import inlineformset_factory

from django import forms
from .models import *


from django import forms
from .models import Invoice, InvoiceItem
from django.forms.models import inlineformset_factory


import json
import base64
import qrcode
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from datetime import timezone as dt_timezone

from django import forms
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.forms.models import inlineformset_factory
from django.core.files import File
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

# ================================
# النماذج (Forms)
# ================================

class SalesInvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer', 'invoice_type', 'invoice_number', 'invoice_date',
            'payment_method', 'notes', 'subtotal_before_discount', 'discount_percentage',
            'discount', 'subtotal_before_tax', 'tax_rate', 'tax_amount', 'total_amount',
            'qr_code','return_reason','original_invoice'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'invoice_type': forms.HiddenInput(), 
            'return_reason': forms.HiddenInput(),
            'original_invoice': forms.HiddenInput(),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الفاتورة'
            }),
            'invoice_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'أية ملاحظات'
            }),
            'subtotal_before_discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'subtotal_before_tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'qr_code': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين القيمة الافتراضية لحقل invoice_type إلى 'sales'
        self.fields['invoice_type'].initial = 'sales'
        self.fields['invoice_type'].required = False  # جعل الحقل غير مطلوب لأنه مخفي
        self.instance.invoice_type = 'sales'


from django import forms
from .models import Invoice

class SalesReturnForm(forms.ModelForm):
    class Meta:
        model = Invoice
        # الحقول التي تريد عرضها في المرتجع
        fields = [
            'customer',          # يجب تحديد عميل
            'invoice_type',      # سنجعله مخفيًا ونضبط قيمته على 'sales_return'
            'invoice_number',    # رقم فاتورة المرتجع
            'invoice_date',      # تاريخ الفاتورة
            'payment_method',    # طريقة الدفع (اختياري إذا كان منطقيًا في المرتجع)
            'notes',             # ملاحظات عامة
            'return_reason',     # سبب المرتجع (نجعله إلزاميًا)
            'subtotal_before_discount',
            'discount_percentage',
            'discount',
            'subtotal_before_tax',
            'tax_rate',
            'tax_amount',
            'total_amount',
            'qr_code'
        ]
        widgets = {
            'invoice_type': forms.HiddenInput(),  # إخفاء نوع الفاتورة
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الفاتورة'
            }),
            'invoice_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'أية ملاحظات'
            }),
            'return_reason': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'سبب المرتجع (مثلاً: المنتج معيب، خطأ شحن ...)'
            }),
            'subtotal_before_discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'subtotal_before_tax': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'qr_code': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إجبار نوع الفاتورة على أن يكون 'sales_return'
        self.fields['invoice_type'].initial = 'sales_return'
        self.fields['invoice_type'].required = False  # جعله غير مطلوب لأنه مخفي
        self.instance.invoice_type = 'sales_return'

        # جعل حقل return_reason إلزاميًا في الفورم (يمكنك أيضًا فرضه في الموديل نفسه)
        self.fields['return_reason'].required = True

    def clean(self):
        """
        التحقق من أن سبب المرتجع موجود، 
        وأية تحقق إضافي تريده عند كون الفاتورة مرتجع.
        """
        cleaned_data = super().clean()

        # تأكد من إدخال سبب المرتجع
        if not cleaned_data.get('return_reason'):
            self.add_error('return_reason', 'يجب إدخال سبب المرتجع في فاتورة مرتجع المبيعات.')

        return cleaned_data




class InvoiceItemForm(forms.ModelForm):
    # حقل السعر للوحدة يظهر كحقل قراءة فقط ويتم تحديثه تلقائيًا بناءً على اختيار المنتج ووحدة التحويل
    unit_price = forms.DecimalField(
        decimal_places=2,
        label="السعر الوحدوي",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = InvoiceItem
        # عرض الحقول المطلوبة مع إضافة حقل الوحدة (unit)
        fields = ['product', 'quantity', 'unit', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'min': '1',
                'class': 'form-control',
                'placeholder': '1'
            }),
            'unit': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # التأكيد على جعل حقل السعر للوحدة readonly حتى يتم تحديثه عن طريق الجافا سكريبت
        self.fields['unit_price'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.full_clean()
        if commit:
            instance.save()
        return instance


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem,
    form=InvoiceItemForm,
    extra=0,
    
    can_delete=True
)








class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 
            'phone', 
            'email',
            'address_line',
            'city',
            'country',
            'vat_number',
            'cr_number',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'اسم المورد'
            }),
           
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'رقم الهاتف / الجوال'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'البريد الإلكتروني'
            }),
            'address_line': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'عنوان الشارع 1'
            }),
           
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'المدينة'
            }),
        
          
            'country': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'البلد'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'الرقم الضريبي (إن وجد)'
            }),
            'cr_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'رقم السجل التجاري (إن وجد)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'ملاحظات إضافية',
                'rows': 3
            }),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 
            'phone', 
            'email',
            'address_line',
            'city',
         
            'country',
            'vat_number',
            'cr_number',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'اسم العميل'
            }),
           
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'رقم الهاتف / الجوال'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'البريد الإلكتروني'
            }),
            'address_line': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'عنوان الشارع 1'
            }),
           
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'المدينة'
            }),
            
            'country': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'البلد'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'الرقم الضريبي (إن وجد)'
            }),
            'cr_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'رقم السجل التجاري (إن وجد)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'ملاحظات إضافية',
                'rows': 3
            }),
        }







from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # الحقول التي نريد عرضها وتحريرها في النموذج
        fields = [
            'name_ar', 
            'serial_number', 
            'category',
            'unit',
            'price',
            'description',
            'stock',
            'low_stock_threshold'
        ]
        
        # يمكنك تخصيص الودجات (Widgets) وبعض الأمور الأخرى
        widgets = {
            'name_ar': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'اسم المنتج بالعربي'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'الرقم التسلسلي'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'وصف المنتج'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

        # لتخصيص أسماء الحقول المعروضة، أو توضيحها للمستخدم
        labels = {
            'name_ar': 'الاسم بالعربي',
            'serial_number': 'الرقم التسلسلي',
            'category': 'الصنف',
            'unit': 'وحدة القياس',
            'price': 'السعر',
            'description': 'الوصف',
            'stock': 'الكمية المتاحة',
            'low_stock_threshold': 'حد التنبيه',
        }
        
        # يمكنك أيضاً إضافة help_texts أو error_messages إذا لزم الأمر
        help_texts = {
            'name_ar': 'اكتب اسم المنتج باللغة العربية',
            'stock': 'الكمية المتوفرة حالياً في المخزون',
        }



from django import forms
from .models import Unit, UnitConversion, PaymentMethod, ProductCategory



class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name_ar', 'name_en', 'description']
        
        labels = {
            'name_ar': 'الاسم بالعربي',
            'name_en': 'الاسم بالإنجليزي',
            'description': 'الوصف',
        }
        
        widgets = {
            'name_ar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: نقداً'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cash'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'تفاصيل عن طريقة الدفع'}),
        }




class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = [
           
            'name',
            'en_name',
            'phone',
            'fax',
            'address',
            'city',
            'postal_code',
            'country',
            'vat_number',
            'cr_number',
            'vat_rate',
            'logo'
        ]
        widgets = {
          
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم التجاري'
            }),
            'en_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Trading Name (English)'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الجوال'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الفاكس'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'العنوان'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الرمز البريدي'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الدولة',
                'value': 'المملكة العربية السعودية'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الرقم الضريبي'
            }),
            'cr_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم السجل التجاري'
            }),
            'vat_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '15.00'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def clean_vat_rate(self):
        vat_rate = self.cleaned_data.get('vat_rate')
        if vat_rate is not None:
            if vat_rate < 0 or vat_rate > 100:
                raise forms.ValidationError('نسبة الضريبة يجب أن تكون بين 0 و 100')
        return vat_rate
