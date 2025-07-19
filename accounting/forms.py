from django import forms  
from invoices.models import CustomerPayment, SupplierPayment  

class CustomerPaymentForm(forms.ModelForm):  
    class Meta:  
        model = CustomerPayment  
        fields = [  
            'voucher_number',  
            'customer',  
            'payment_type',  
            'amount',  
            'date',  
            'notes',  
            'payment_method'  
        ]  
        labels = {  
            'voucher_number': 'رقم السند',  
            'customer': 'العميل',  
            'payment_type': 'نوع الدفعة',  
            'amount': 'المبلغ',  
            'date': 'التاريخ',  
            'notes': 'ملاحظات',  
            'payment_method': 'طريقة الدفع'  
        }  
        widgets = {  
            'voucher_number': forms.TextInput(attrs={'class': 'form-control'}),  
            'customer': forms.Select(attrs={'class': 'form-control'}),  
            'payment_type': forms.Select(attrs={'class': 'form-control'}),  
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),  
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # نوع الحقل تاريخ  
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), # حقل نصي متعدد الأسطر  
            'payment_method': forms.Select(attrs={'class': 'form-control'}),  
        }  


class SupplierPaymentForm(forms.ModelForm):  
    class Meta:  
        model = SupplierPayment  
        fields = [  
            'voucher_number',  
            'supplier',  
            'payment_type',  
            'amount',  
            'date',  
            'notes',  
            'payment_method'  
        ]  
        labels = {  
            'voucher_number': 'رقم السند',  
            'supplier': 'المورد',  
            'payment_type': 'نوع الدفعة',  
            'amount': 'المبلغ',  
            'date': 'التاريخ',  
            'notes': 'ملاحظات',  
            'payment_method': 'طريقة الدفع'  
        }  
        widgets = {  
            'voucher_number': forms.TextInput(attrs={'class': 'form-control'}),  
            'supplier': forms.Select(attrs={'class': 'form-control'}),  
            'payment_type': forms.Select(attrs={'class': 'form-control'}),  
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),  
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),  
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),  
            'payment_method': forms.Select(attrs={'class': 'form-control'}),  
        }  