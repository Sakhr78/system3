from django.urls import path
from . import views

urlpatterns = [
    # لوحة التحكم
    path('', views.invoice_dashboard, name='dashboard'),
    
    # إدارة الفواتير
 
 
    #path('invoices/list/return/', views.return_invoice_list, name='return_invoice_list'),
   # path('invoices/list/transfer/', views.transfer_invoice_list, name='transfer_invoice_list'),
   # path('invoices/list/adjustment/', views.adjustment_invoice_list, name='adjustment_invoice_list'),
   # path('invoices/list/expense/', views.expense_invoice_list, name='expense_invoice_list'),
   # path('invoices/list/other/', views.other_invoice_list, name='other_invoice_list'),


    path('invoices/list/statistics/', views.dashboard, name='sales_statistics'),




    # تفاصيل وطباعة الفاتورة
#    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),

   # path('invoices/edit/<int:invoice_id>/', views.edit_invoice, name='edit_invoice'),




    # مسار تعديل فاتورة المبيعات
    # مسار تعديل فاتورة المشتريات
    path('print-view/<int:invoice_id>/', views.invoice_print_view, name='invoice_print_view'),
  #  path('print/<int:invoice_id>/', views.print_invoice, name='print_invoice'),
    
    
    
    path('supplier/create/', views.create_supplier, name='create_supplier'),
    path('supplier/edit/<int:supplier_id>/', views.edit_supplier, name='edit_supplier'),
    path('supplier/delete/<int:supplier_id>/', views.delete_supplier, name='delete_supplier'),
    path('supplier/list/', views.supplier_list, name='supplier_list'),
    path('supplier/detail/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),

    path('customer/create/', views.create_customer, name='create_customer'),
    path('customer/edit/<int:customer_id>/', views.edit_customer, name='edit_customer'),
    path('customer/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('customer/list/', views.customer_list, name='customer_list'),
    path('customer/detail/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    


    # PaymentMethods (Single Page + AJAX)
    path('payment-methods/manage/', views.manage_payment_methods, name='manage_payment_methods'),
    path('payment-methods/ajax_create_or_update/', views.ajax_create_or_update_payment_method, name='ajax_create_or_update_payment_method'),
    path('payment-methods/ajax_delete/', views.ajax_delete_payment_method, name='ajax_delete_payment_method'),



 # ... مسارات أخرى
    path('products/', views.manage_products, name='manage_products'),
    path('ajax_create_or_update_product/', views.ajax_create_or_update_product, name='ajax_create_or_update_product'),
    path('ajax_delete_product/', views.ajax_delete_product, name='ajax_delete_product'),



    path('company-settings/', views.company_settings, name='company_settings'),
    ]   
