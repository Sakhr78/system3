from django.core.management.base import BaseCommand  

class Command(BaseCommand):  
    help = "اختبار الأمر البسيط."  

    def handle(self, *args, **options):  
        self.stdout.write(self.style.SUCCESS("تم تحديد الأمر بنجاح!"))

        