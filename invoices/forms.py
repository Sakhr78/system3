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



class InvoiceItemForm(forms.ModelForm):
    unit_price = forms.DecimalField(
        decimal_places=2,
        label="السعر ",
        widget=forms.NumberInput(attrs={'class': 'form-control'})  # السماح بتعديل السعر
    )

    class Meta:
        model = InvoiceItem
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
        # إزالة خاصية readonly من حقل unit_price لجعله قابلًا للتعديل
        self.fields['unit_price'].widget.attrs['readonly'] = False

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
                'placeholder': ' العنوان '
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
                'placeholder': 'العنوان  '
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








class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        fields = [
           
            'name',
            'en_name',
            'phone',
            'email',

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













# accounting_app/forms.py
