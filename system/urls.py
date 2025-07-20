# invoice_system/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from invoices import views


from django.urls import path
from .views import AdminLoginView, logout_view


urlpatterns = [
    path('admin/', admin.site.urls),
#    path('invoice/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('', include('invoices.urls')),
    path('', include('sales.urls')),
    path('', include('purchase.urls')),
    path('', include('inventory.urls')),
    path('', include('accounting.urls')),






    path('login/', AdminLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
