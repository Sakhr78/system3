from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import *

from django.contrib import admin
from .models import CompanySettings

@admin.register(CompanySettings)


    # لترجمة بعض العناوين في Admin (اختياري)
    # يمكنك الاستفادة من Django localization أو تركها هكذا

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'vat_number']
    search_fields = ['name', 'phone', 'vat_number']












@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name_ar', 'name_en', 'description']
    search_fields = ['name_ar', 'name_en']

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'stock', 'low_stock_threshold', 'price', 'unit')
    list_filter = ['unit']
    search_fields = ('name_ar', 'name_en')
    autocomplete_fields = ['unit']
    actions = ['export_stock_report']
    
    def export_stock_report(self, request, queryset):
        pass
    export_stock_report.short_description = 'تصدير تقرير المخزون المحدد'








@admin.register(Product)
class ProductAdminWrapper(ProductAdmin):
    pass
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import Invoice, InvoiceItem


from django.contrib import admin
from .models import InvoiceItem





from django.contrib import admin
from .models import Unit, UnitConversion, Product, Invoice, InvoiceItem

class UnitConversionInline(admin.TabularInline):
    """إتاحة إضافة تحويلات للوحدات داخل صفحة الوحدة الأساسية"""
    model = UnitConversion
    extra = 1
    fields = ['larger_unit_name', 'larger_unit_abbreviation', 'conversion_factor']
    verbose_name = "تحويل الوحدة"
    verbose_name_plural = "تحويلات الوحدات"

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    """إدارة الوحدات الأساسية"""
    list_display = ['name', 'abbreviation', 'template', 'is_active']
    search_fields = ['name', 'abbreviation']
    list_filter = ['is_active']
    inlines = [UnitConversionInline]  # إضافة الوحدات المحولة مباشرة في الوحدة الأساسية

@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    """إدارة تحويلات الوحدات"""
    list_display = ['base_unit', 'larger_unit_name', 'conversion_factor']
    search_fields = ['larger_unit_name']
    list_filter = ['base_unit']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['product', 'quantity', 'unit', 'unit_price', 'total_before_tax', 'total']
    readonly_fields = ['unit_price', 'total_before_tax', 'total']
    autocomplete_fields = ['product', 'unit']
    can_delete = True







class SalesReturnInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_type', 'customer', 'tax_amount', 'invoice_date')
    search_fields = ('invoice_number', 'customer__name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # تصفية الفواتير لتظهر فقط المرتجعات من نوع "sales_return"
        return qs.filter(invoice_type='sales_return')

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0

class SalesReturnInvoiceAdminExtended(SalesReturnInvoiceAdmin):
    inlines = [InvoiceItemInline]

admin.site.register(Invoice, SalesReturnInvoiceAdminExtended)
