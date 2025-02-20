from django.urls import path
from . import views

urlpatterns = [
    #مسارات الفاتورة المبيعات
    path('list/sales/', views.sales_invoice_list, name='sales_invoice_list'),
    path('create/sales/', views.create_sales_invoice, name='create_sales_invoice'),
    path('sales/edit/<int:invoice_id>/', views.update_sales_invoice, name='edit_sales_invoice'),
    path('delete/sales/<int:invoice_id>/', views.delete_sales_invoice, name='delete_sales_invoice'),
    path('sales/detail/<int:invoice_id>/', views.sales_invoice_detail, name='sales_invoice_detail'),

    #مسارات الفاتورة المرتجعات
    path('sales_returns/list/', views.list_sales_returns, name='list_sales_returns'),
    path('sales_returns/ajax_search/', views.ajax_search_sales_returns, name='ajax_search_sales_returns'),
    path('sales_returns/<int:invoice_id>/edit/', views.update_sales_return_invoice, name='update_sales_return_invoice'),
    path('delete/sales_returns/<int:invoice_id>', views.delete_sales_return_invoice, name='delete_sales_return_invoice'),

    path('sales_returns/<int:invoice_id>/', views.sales_return_invoice_detail, name='sales_return_invoice_detail'),

    path('create/return/', views.create_sales_return_invoice, name='create_sales_return_invoice'),
    path('sales-return/new/<int:original_id>/', views.create_sales_return_invoice, name='create_sales_return_with_original'),
    path('sales-return/edit/<int:return_invoice_id>/', views.create_sales_return_invoice, name='edit_sales_return'),

  #  path('create/return/', views.create_sales_return_invoicee, name='create_sales_return_invoicee'),
 #   path('sales-return-invoice/', views.create_sales_return_invoice, name='create_sales_return_invoice'),
 #   path('ajax/get_invoices_by_customer/', views.get_invoices_by_customer, name='get_invoices_by_customer'),
  #  path('ajax/get_invoice_details/', views.get_invoice_details, name='get_invoice_details'),

    ]
