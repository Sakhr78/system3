# accounting_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from decimal import Decimal

from .forms import ReceiptVoucherForm, PaymentVoucherForm
from invoices.models import ReceiptVoucher, PaymentVoucher

# ========== سندات القبض ==========
"""
def receipt_voucher_list(request):
    """
    عرض قائمة سندات القبض
    """
    vouchers = ReceiptVoucher.objects.all()
    return render(request, 'accounting_app/receipt_voucher_list.html', {
        'vouchers': vouchers
    })

def create_receipt_voucher(request):
    """
    إنشاء سند قبض جديد
    """
    voucher = None  # لتمييز إنشاء سند جديد عن تعديل سند موجود في القالب
    if request.method == 'POST':
        form = ReceiptVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save()
            return redirect('receipt_voucher_list')  # انتقل إلى قائمة سندات القبض
    else:
        form = ReceiptVoucherForm()
    return render(request, 'accounting_app/create_receipt_voucher.html', {
        'form': form,
        'voucher': voucher
    })

def update_receipt_voucher(request, pk):
    """
    تعديل سند قبض موجود
    """
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    if request.method == 'POST':
        form = ReceiptVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('receipt_voucher_list')
    else:
        form = ReceiptVoucherForm(instance=voucher)
    return render(request, 'accounting_app/create_receipt_voucher.html', {
        'form': form,
        'voucher': voucher
    })

def delete_receipt_voucher(request, pk):
    """
    حذف سند قبض
    """
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    if request.method == 'POST':
        voucher.delete()
        return redirect('receipt_voucher_list')
    # استخدم صفحة تأكيد الحذف
    return render(request, 'accounting_app/confirm_delete.html', {
        'object': voucher
    })


# ========== سندات الصرف ==========

def payment_voucher_list(request):
    """
    عرض قائمة سندات الصرف
    """
    vouchers = PaymentVoucher.objects.all()
    return render(request, 'accounting_app/payment_voucher_list.html', {
        'vouchers': vouchers
    })

def create_payment_voucher(request):
    """
    إنشاء سند صرف جديد
    """
    voucher = None
    if request.method == 'POST':
        form = PaymentVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save()
            return redirect('payment_voucher_list')
    else:
        form = PaymentVoucherForm()
    return render(request, 'accounting_app/create_payment_voucher.html', {
        'form': form,
        'voucher': voucher
    })

def update_payment_voucher(request, pk):
    """
    تعديل سند صرف موجود
    """
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    if request.method == 'POST':
        form = PaymentVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('payment_voucher_list')
    else:
        form = PaymentVoucherForm(instance=voucher)
    return render(request, 'accounting_app/create_payment_voucher.html', {
        'form': form,
        'voucher': voucher
    })

def delete_payment_voucher(request, pk):
    """
    حذف سند صرف
    """
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    if request.method == 'POST':
        voucher.delete()
        return redirect('payment_voucher_list')
    return render(request, 'accounting_app/confirm_delete.html', {
        'object': voucher
    })
