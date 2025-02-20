from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from invoices.models import Invoice, InvoiceItem, Product





# ================================
# النماذج (Forms)
# ================================

class PurchaseInvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'supplier', 'invoice_type', 'invoice_number', 'invoice_date',
            'payment_method', 'notes', 'subtotal_before_discount', 'discount_percentage',
            'discount', 'subtotal_before_tax', 'tax_rate', 'tax_amount', 'total_amount',
            'qr_code','return_reason','original_invoice'
        ]
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
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
        # تعيين القيمة الافتراضية لحقل invoice_type إلى 'purchase'
        self.fields['invoice_type'].initial = 'purchase'
        self.fields['invoice_type'].required = False  # جعل الحقل غير مطلوب لأنه مخفي
        self.instance.invoice_type = 'purchase'




class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model = Invoice
        # الحقول التي تريد عرضها في المرتجع
        fields = [
            'supplier',          # يجب تحديد عميل
            'invoice_type',      # سنجعله مخفيًا ونضبط قيمته على 'purchase_return'
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
            'supplier': forms.Select(attrs={'class': 'form-control'}),
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
        # إجبار نوع الفاتورة على أن يكون 'purchase_return'
        self.fields['invoice_type'].initial = 'purchase_return'
        self.fields['invoice_type'].required = False  # جعله غير مطلوب لأنه مخفي
        self.instance.invoice_type = 'purchase_return'

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























class PurchaseReturnInvoiceForm(forms.ModelForm):
    original_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Invoice
        fields = [
            'invoice_number',
            'invoice_date',
            'original_invoice',
            'supplier',
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
            self.fields['original_invoice'].queryset = Invoice.objects.filter(invoice_type='purchase')

        # إذا كانت الفاتورة مرتبطة بفاتورة أصلية، تعيين القيمة المخفية
        if self.instance and self.instance.original_invoice:
            self.fields['original_id'].initial = self.instance.original_invoice.id

        # جعل حقل العميل (supplier) غير مطلوب حتى وإن كان معطلاً
        if 'supplier' in self.fields:
            self.fields['supplier'].required = False

        # إضافة الكلاس form-control لجميع الحقول
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        # إذا كان الكائن يحمل فاتورة أصلية، نستخدمها مباشرة
        if self.instance and self.instance.original_invoice:
            cleaned_data['original_invoice'] = self.instance.original_invoice
            cleaned_data['supplier'] = self.instance.original_invoice.supplier
        else:
            original_id = cleaned_data.get('original_id')
            if original_id:
                try:
                    original_inv = Invoice.objects.get(id=original_id, invoice_type='purchase')
                except Invoice.DoesNotExist:
                    self.add_error('original_invoice', "الفاتورة الأصلية غير موجودة.")
                else:
                    cleaned_data['original_invoice'] = original_inv
                    cleaned_data['supplier'] = original_inv.supplier
            else:
                if not cleaned_data.get('supplier'):
                    raise ValidationError("يجب اختيار عميل لفاتورة المبيعات أو المرتجع.")
        return cleaned_data

    def save(self, commit=True):
        # توليد رقم فاتورة إن لم يوجد
        if not self.cleaned_data.get('invoice_number'):
            # دالة generate_invoice_number() ينبغي أن تكون معرفّة في الموديل Invoice
            self.instance.invoice_number = self.instance.generate_invoice_number()
        return super().save(commit=commit)



class PurchaseReturnInvoiceItemForm(forms.ModelForm):
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


class PurchaseReturnInvoiceItemFormSet(BaseInlineFormSet):
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

     

PurchaseReturnInvoiceItemInlineFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=PurchaseReturnInvoiceItemForm,
    formset=PurchaseReturnInvoiceItemFormSet,
    extra=1,
    can_delete=False
)