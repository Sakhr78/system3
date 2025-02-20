from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from .forms import AdminLoginForm

class AdminLoginView(FormView):
    """
    نموذج تسجيل الدخول باستخدام FormView.
    يتم التحقق من أن المستخدم هو مشرف فقط.
    """
    template_name = 'accounts/login.html'
    form_class = AdminLoginForm
    success_url = reverse_lazy('dashboard')  # الصفحة التي سيتم التوجيه إليها بعد تسجيل الدخول

    def form_valid(self, form):
        # الحصول على المستخدم من النموذج
        user = form.get_user()
        # التحقق من أن المستخدم مشرف (superuser)
        if not user.is_superuser:
            form.add_error(None, "ليس لديك صلاحيات للوصول إلى النظام. يجب أن يكون المستخدم مشرفاً.")
            return self.form_invalid(form)
        # تسجيل الدخول
        login(self.request, user)
        messages.success(self.request, "تم تسجيل الدخول بنجاح!")
        return super().form_valid(form)


def logout_view(request):
    """
    تسجيل الخروج وإعادة التوجيه إلى صفحة تسجيل الدخول.
    """
    logout(request)
    messages.info(request, "تم تسجيل الخروج بنجاح!")
    return redirect('login')
