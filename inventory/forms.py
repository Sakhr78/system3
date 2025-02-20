from django import forms

from invoices.models import *

from django.forms import inlineformset_factory

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']
        
        labels = {
            'name': 'اسم الصنف',
            'description': 'الوصف',
        }
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: إلكترونيات'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'تفاصيل الصنف'}),
        }





class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'abbreviation', 'template', 'is_active']
        labels = {
            'name': 'اسم الوحدة الأساسية',
            'abbreviation': 'التمييز (اختصار الوحدة)',
            'template': 'القالب',
            'is_active': 'نشط',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كيلوغرام'}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كغ'}),
            'template': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع الوحدة مثل (الوزن, الحجم...)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UnitConversionForm(forms.ModelForm):
    class Meta:
        model = UnitConversion
        fields = ['larger_unit_name', 'larger_unit_abbreviation', 'conversion_factor']
        labels = {
            'larger_unit_name': 'اسم الوحدة الأكبر',
            'larger_unit_abbreviation': 'اختصار الوحدة الأكبر',
            'conversion_factor': 'معامل التحويل',
        }
        widgets = {
            'larger_unit_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كرتونة'}),
            'larger_unit_abbreviation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كرت.'}),
            'conversion_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }



"""
نعرّف InlineFormSet بحيث نتمكن من ربط عدة تحويلات بوحدة أساسية واحدة.
يستخدم Unit كنموذج رئيسي، وUnitConversion كنموذج فرعي.
"""

UnitConversionInlineFormSet = inlineformset_factory(
    parent_model=Unit,
    model=UnitConversion,
    form=UnitConversionForm,
    extra=0,        # عدد النماذج التي تظهر افتراضيًا
    can_delete=True
)


"""
نموذج مدمج لإنشاء (Unit) وإضافة تحويل (UnitConversion) في نفس العملية.
"""
class UnitWithConversionForm(forms.ModelForm):
    # حقول التحويل
    larger_unit_name = forms.CharField(
        label="اسم الوحدة الأكبر",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كرتونة'})
    )
    larger_unit_abbreviation = forms.CharField(
        label="اختصار الوحدة الأكبر",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كرت.'})
    )
    conversion_factor = forms.DecimalField(
        label="معامل التحويل",
        required=False,
        decimal_places=4,
        max_digits=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'مثال: 12'})
    )

    class Meta:
        model = Unit
        fields = ['name', 'abbreviation', 'template', 'is_active']
        labels = {
            'name': 'اسم الوحدة الأساسية',
            'abbreviation': 'التمييز (اختصار الوحدة)',
            'template': 'القالب',
            'is_active': 'نشط',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كيلوغرام'}),
            'abbreviation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: كغ'}),
            'template': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع الوحدة مثل (الوزن, الحجم...)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        """
        نحفظ أولاً كائن الـUnit (الوحدة الأساسية).
        ثم إذا أدخل المستخدم بيانات التحويل (larger_unit_name, larger_unit_abbreviation, conversion_factor)
        نقوم بإنشاء UnitConversion مربوط بهذه الوحدة.
        """
        base_unit = super().save(commit=commit)

        # قراءة بيانات التحويل من الـ cleaned_data
        l_name = self.cleaned_data.get('larger_unit_name')
        l_abbr = self.cleaned_data.get('larger_unit_abbreviation')
        factor = self.cleaned_data.get('conversion_factor')

        # إذا أدخل المستخدم بيانات التحويل
        if l_name and l_abbr and factor:
            UnitConversion.objects.create(
                base_unit=base_unit,
                larger_unit_name=l_name,
                larger_unit_abbreviation=l_abbr,
                conversion_factor=factor
            )

        return base_unit
