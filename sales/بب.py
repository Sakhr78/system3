from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from invoices.models import Invoice, InvoiceItem

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
            'subtotal_before_discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subtotal_before_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'qr_code': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # invoice_number غير مطلوب
        self.fields['invoice_number'].required = False

        # قصر original_invoice على فواتير مبيعات
        if 'original_invoice' in self.fields:
            self.fields['original_invoice'].queryset = Invoice.objects.filter(invoice_type='sales')

        # إذا كانت الفاتورة الحالية تشير إلى فاتورة أصلية
        if self.instance and self.instance.original_invoice:
            self.fields['original_id'].initial = self.instance.original_invoice.id

    def clean(self):
        cleaned_data = super().clean()
        original_id = cleaned_data.get('original_id')
        if original_id:
            try:
                original_inv = Invoice.objects.get(id=original_id, invoice_type='sales')
            except Invoice.DoesNotExist:
                self.add_error('original_invoice', "الفاتورة الأصلية غير موجودة.")
            else:
                cleaned_data['original_invoice'] = original_inv
                cleaned_data['customer'] = original_inv.customer
        return cleaned_data

    def save(self, commit=True):
        if not self.cleaned_data.get('invoice_number'):
            # تحتاج لطريقة generate_invoice_number في موديل Invoice
            self.instance.invoice_number = self.instance.generate_invoice_number()
        return super().save(commit=commit)





class SalesReturnInvoiceItemForm(forms.ModelForm):
    """
    نموذج عناصر فاتورة مرتجع المبيعات
    """

    unit_price = forms.DecimalField(
        decimal_places=2,
        label="السعر الوحدوي",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'unit', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),  
            'quantity': forms.NumberInput(attrs={
                'min': '1',
                'class': 'form-control',
                'placeholder': '1'
            }),
            'unit': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # اجعل `unit_price` غير قابل للتحرير
        self.fields['unit_price'].widget.attrs['readonly'] = True

        # عند وجود فاتورة أصلية، حصر المنتجات المسموح بإرجاعها فقط بتلك المنتجات
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].invoice and kwargs['instance'].invoice.original_invoice:
            original_invoice = kwargs['instance'].invoice.original_invoice
            allowed_products = original_invoice.invoice_items.values_list('product', flat=True)
            self.fields['product'].queryset = self.fields['product'].queryset.filter(id__in=allowed_products)

    def clean_quantity(self):
        """
        التحقق من أن الكمية المرتجعة لا تتجاوز الكمية الأصلية في الفاتورة الأصلية
        """
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')

        if not product or not quantity:
            return quantity  # تخطي التحقق إذا لم يكن المنتج محددًا

        # البحث عن الكمية الأصلية في الفاتورة الأصلية
        if self.instance.invoice.original_invoice:
            original_invoice = self.instance.invoice.original_invoice
            original_item = original_invoice.invoice_items.filter(product=product).first()

            if original_item and quantity > original_item.quantity:
                raise ValidationError(f"🚨 الكمية المرتجعة ({quantity}) أكبر من الكمية الأصلية ({original_item.quantity})")

        return quantity


# إنشاء Formset متوافق مع المرتجع


class SalesReturnInvoiceItemFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.original_invoice:
            original_invoice = self.instance.original_invoice
            initial_data = []
            for item in original_invoice.invoice_items.all():
                initial_data.append({
                    'product': item.product,
                    'product_name': item.product.name_ar,
                    'original_quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'unit': item.unit
                })
            self.initial = initial_data
            self.extra = len(initial_data)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields['original_quantity'] = forms.IntegerField(
            widget=forms.NumberInput(attrs={'readonly': True}),
            required=False
        )


    def clean(self):
        super().clean()
        for form in self.forms:
            cd = form.cleaned_data
            if not cd:
                # قد يكون النموذج فارغًا
                continue

            if not cd.get('product'):
                form.add_error('product', "يجب اختيار منتج.")

            qty = cd.get('quantity', 0)
            if qty <= 0:
                form.add_error('quantity', "يجب إدخال كمية مرتجعة أكبر من صفر.")

            # التحقق المحاسبي بعدم تجاوز الكمية الأصلية





SalesReturnInvoiceItemInlineFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=SalesReturnInvoiceItemForm,
    formset=SalesReturnInvoiceItemFormSet,
    extra=0,
    can_delete=False
)