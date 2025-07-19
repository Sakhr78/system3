# accounting_app/urls.py
from django.urls import path
from .views import *
from . import views

urlpatterns = [
   # path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('aging_report/', views.aging_report_view, name='aging_report'),
    path('customer/<int:customer_id>/statement/', views.customer_statement_view, name='customer_statement'),
  
    path('customer-payment/<int:pk>/print/', views.print_customer_payment, name='print_customer_payment'),
    path('supplier-payment/<int:pk>/print/', views.print_supplier_payment, name='print_supplier_payment'),
    # صفحة عرض المدفوعات
    path('customer-payments/', views.customer_payment_list, name='customer_payment_list'),
    path('ajax-search-customer-payments/', views.ajax_search_customer_payments, name='ajax_search_customer_payments'),
    path('customer-payment/create/', views.create_customer_payment, name='create_customer_payment'),
    path('customer-payment/<int:payment_id>/delete/', views.delete_customer_payment, name='delete_customer_payment'),
    path('customer-payment/<int:payment_id>/update/', views.update_customer_payment, name='update_customer_payment'),



    path('supplier-payments/', views.supplier_payment_list, name='supplier_payment_list'),
    path('ajax-search-supplier-payments/', views.ajax_search_supplier_payments, name='ajax_search_supplier_payments'),
    path('supplier-payment/create/', views.create_supplier_payment, name='create_supplier_payment'),
    path('supplier-payment/<int:payment_id>/delete/', views.delete_supplier_payment, name='delete_supplier_payment'),
    path('supplier-payment/<int:payment_id>/update/', views.update_supplier_payment, name='update_supplier_payment'),

   # path('print/<int:payment_id>/', views.print_customer_payment, name='print_customer_payment'),

]
