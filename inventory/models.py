from django.db import models

# Create your models here.

from django.db import models
from django.core.exceptions import ValidationError


# نموذج وحدة القياس الأساسية
class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الوحدة الأساسية")

    name_en = models.CharField("انجليزي اسم الوحدة" , max_length=50, unique=True)  # مثال: كيلوجرام
    symbol = models.CharField("الرمز", max_length=10, unique=True)   # مثال: KG
    template = models.CharField(max_length=50, verbose_name="القالب", help_text="مثال: الوزن")
    is_active = models.BooleanField(default=True, verbose_name="نشط") 
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

# نموذج لتحويل الوحدات (علاقة بين وحدتين)
class UnitConversion(models.Model):
    from_unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='from_conversions')
    to_unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='to_conversions')
    conversion_factor = models.DecimalField("عامل التحويل", max_digits=15, decimal_places=4)  # مثال: 1 كجم = 1000 جم → العامل 1000
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        unique_together = ('from_unit', 'to_unit')  # منع تكرار التحويلات
    
    def clean(self):
        if self.from_unit == self.to_unit:
            raise ValidationError("لا يمكن تحويل الوحدة إلى نفسها!")
    
    def __str__(self):
        return f"1 {self.from_unit} = {self.conversion_factor} {self.to_unit}"
