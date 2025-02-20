from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from invoices.models import Invoice, InvoiceItem, Product


class SalesReturnInvoiceForm(forms.ModelForm):
    original_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Invoice
        fields = [
            'invoice_number',
            'invoice_date',
            'original_invoice',
            'customer',
            'payment_method',
            'notes',
            'return_reason',
            'subtotal_before_discount',
            'discount_percentage',
            'discount',
            'subtotal_before_tax',
            'tax_rate',
            'tax_amount',
            'total_amount',
            'qr_code',
        ]
        widgets = {
            
            'invoice_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
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
        # جعل حقل رقم الفاتورة غير مطلوب
        if 'invoice_number' in self.fields:
            self.fields['invoice_number'].required = False

        # تقييد الفاتورة الأصلية لتكون من فواتير المبيعات فقط
        if 'original_invoice' in self.fields:
            self.fields['original_invoice'].queryset = Invoice.objects.filter(invoice_type='sales')

        # إذا كانت الفاتورة مرتبطة بفاتورة أصلية، تعيين القيمة المخفية
        if self.instance and self.instance.original_invoice:
            self.fields['original_id'].initial = self.instance.original_invoice.id

        # جعل حقل العميل (customer) غير مطلوب حتى وإن كان معطلاً
        if 'customer' in self.fields:
            self.fields['customer'].required = False

        # إضافة الكلاس form-control لجميع الحقول
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        # إذا كان الكائن يحمل فاتورة أصلية، نستخدمها مباشرة
        if self.instance and self.instance.original_invoice:
            cleaned_data['original_invoice'] = self.instance.original_invoice
            cleaned_data['customer'] = self.instance.original_invoice.customer
        else:
            original_id = cleaned_data.get('original_id')
            if original_id:
                try:
                    original_inv = Invoice.objects.get(id=original_id, invoice_type='sales')
                except Invoice.DoesNotExist:
                    self.add_error('original_invoice', "الفاتورة الأصلية غير موجودة.")
                else:
                    cleaned_data['original_invoice'] = original_inv
                    cleaned_data['customer'] = original_inv.customer
            else:
                if not cleaned_data.get('customer'):
                    raise ValidationError("يجب اختيار عميل لفاتورة المبيعات أو المرتجع.")
        return cleaned_data


    def save(self, commit=True):
        # توليد رقم فاتورة إن لم يوجد
        if not self.cleaned_data.get('invoice_number'):
            # دالة generate_invoice_number() ينبغي أن تكون معرفّة في الموديل Invoice
            self.instance.invoice_number = self.instance.generate_invoice_number()
        return super().save(commit=commit)



class SalesReturnInvoiceItemForm(forms.ModelForm):
    """
    نموذج البنود، مع حقل اختياري لعرض اسم المنتج.
    """
    product_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    original_quantity = forms.IntegerField( required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
       )

    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'unit_price', 'unit']
        widgets = {
            'product': forms.HiddenInput(),  
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
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


class SalesReturnInvoiceItemFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.original_invoice:
            original_invoice = self.instance.original_invoice
            init_data = []
            # قراءة البنود من الفاتورة الأصلية
            for item in original_invoice.invoice_items.all():
                init_data.append({
                    'product': item.product,
                    'product_name': item.product.name_ar,
                    'original_quantity': item.quantity,
                    'quantity': 0,
                    'unit_price': item.unit_price,
                    'unit': item.unit,
                })
            # تعيين عدد النماذج الإضافية
        #    self.extra = len(init_data)

            # تحديث البيانات الابتدائية لكل نموذج فرعي
            for i, form in enumerate(self.forms):
                if i < len(init_data):
                    form.initial.update(init_data[i])


    def clean(self):
        """
        إضافة تحقق إضافي على كل نموذج فرعي، وإظهار حقل الخطأ بدقة.
        """
        super().clean()
        for idx, form in enumerate(self.forms):
            cd = form.cleaned_data
            if not cd:
                continue  # قد يكون النموذج فارغاً
            # تحقق الحقول
            product = cd.get('product')
            quantity = cd.get('quantity') or 0

            if quantity <= 0:
                form.add_error('quantity', "الكمية المرتجعة يجب أن تكون أكبر من صفر.")

     

SalesReturnInvoiceItemInlineFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=SalesReturnInvoiceItemForm,
    formset=SalesReturnInvoiceItemFormSet,
    extra=1,
    can_delete=False
)