from django.urls import path
from . import views

urlpatterns = [
    # مسارات إدارة التصنيفات
    path('categories/', views.manage_categories, name='manage_categories'),
    path('ajax_create_or_update_category/', views.ajax_create_or_update_category, name='ajax_create_or_update_category'),
    path('ajax_delete_category/', views.ajax_delete_category, name='ajax_delete_category'),




        # مسارات إدارة الوحدات 
    path('units/', views.manage_units, name='manage_units'),

    path('ajax_get_unit_data/<int:unit_id>/', views.ajax_get_unit_data, name='ajax_get_unit_data'),
    path('ajax_create_or_update_unit/', views.ajax_create_or_update_unit, name='ajax_create_or_update_unit'),
    path('ajax_delete_unit/', views.ajax_delete_unit, name='ajax_delete_unit'),
    path('ajax_delete_conversion/', views.ajax_delete_conversion, name='ajax_delete_conversion'),



    path('ajax_create_or_update_conversion/', views.ajax_create_or_update_conversion, name='ajax_create_or_update_conversion'),
    path('ajax_delete_conversion/', views.ajax_delete_conversion, name='ajax_delete_conversion'),
]
