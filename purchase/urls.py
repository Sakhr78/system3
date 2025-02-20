

from django.urls import path
from . import views

urlpatterns = [

    #مسارات الفاتورة المبيعات
    path('list/purchase/', views.purchase_invoice_list, name='purchase_invoice_list'),
    path('create/purchase/', views.create_purchase_invoice, name='create_purchase_invoice'),
    path('purchase/edit/<int:invoice_id>/', views.update_purchase_invoice, name='edit_purchase_invoice'),
    path('delete/purchase/<int:invoice_id>/', views.delete_purchase_invoice, name='delete_purchase_invoice'),
    path('purchase/detail/<int:invoice_id>/', views.purchase_invoice_detail, name='purchase_invoice_detail'),

    path('purchase_returns/list/', views.list_purchases_returns, name='list_purchases_returns'),
    path('purchase_returns/ajax_search/', views.ajax_search_purchases_returns, name='ajax_search_purchase_returns'),
    path('purchase_returns/<int:invoice_id>/edit/', views.update_purchase_return_invoice, name='update_purchase_return_invoice'),
    path('delete/purchase_returns/<int:invoice_id>', views.delete_purchase_return_invoice, name='delete_purchase_return_invoice'),

    path('purchase_returns/<int:invoice_id>/', views.purchase_return_invoice_detail, name='purchase_return_invoice_detail'),

    path('create/purchase-return/', views.create_purchase_return_invoice, name='create_purchase_return_invoice'),
    path('purchase-return/new/<int:original_id>/', views.create_purchase_return_invoice, name='create_purchase_return_with_original'),
    path('purchase-return/edit/<int:return_invoice_id>/', views.create_purchase_return_invoice, name='edit_purchase_return'),

  #  path('create/return/', views.create_purchase_return_invoicee, name='create_purchase_return_invoicee'),
 #   path('purchase-return-invoice/', views.create_purchase_return_invoice, name='create_purchase_return_invoice'),
 #   path('ajax/get_invoices_by_customer/', views.get_invoices_by_customer, name='get_invoices_by_customer'),
  #  path('ajax/get_invoice_details/', views.get_invoice_details, name='get_invoice_details'),

    ]
