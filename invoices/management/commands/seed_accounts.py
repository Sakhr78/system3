from django.core.management.base import BaseCommand  
from decimal import Decimal  
from invoices.models import ChartOfAccount  
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'إنشاء الحسابات الأساسية إذا لم تكن موجودة في قاعدة البيانات'

    REQUIRED_ACCOUNTS = [
        {'code': '1100', 'name': 'حساب العملاء', 'account_type': 'asset', 'balance': Decimal('0.00')},
        {'code': '2100', 'name': 'حساب الموردين', 'account_type': 'liability', 'balance': Decimal('0.00')},
        {'code': '4000', 'name': 'حساب الإيرادات', 'account_type': 'income', 'balance': Decimal('0.00')},
        {'code': '5000', 'name': 'حساب المشتريات', 'account_type': 'expense', 'balance': Decimal('0.00')},
        {'code': '2200', 'name': 'حساب الضريبة', 'account_type': 'liability', 'balance': Decimal('0.00')},
        {'code': '4100', 'name': 'حساب الخصم', 'account_type': 'expense', 'balance': Decimal('0.00')},
        {'code': '1000', 'name': 'حساب النقدية', 'account_type': 'asset', 'balance': Decimal('0.00')},
    ]

    def handle(self, *args, **options):
        for account_data in self.REQUIRED_ACCOUNTS:
            account, created = ChartOfAccount.objects.get_or_create(
                code=account_data['code'],
                defaults=account_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"تم إنشاء الحساب: {account.code} - {account.name}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"الحساب موجود مسبقاً: {account.code} - {account.name}"
                ))
