from django.test import TestCase, Client
from django.urls import reverse
from invoices.models import Product, Invoice, InvoiceItem, Customer, PaymentMethod

class InvoiceCreationTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")
        self.payment_method = PaymentMethod.objects.create(name="Cash")
        self.product = Product.objects.create(name="Test Product", price=100)
        self.client = Client()

    def test_invoice_creation(self):
        url = reverse('create_invoice')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'customer': self.customer.id,
            'invoice_date': "2025-02-08",
            'payment_method': self.payment_method.id,
            'discount': "0",
            'notes': "This is a test invoice",
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-product': str(self.product.id),
            'items-0-quantity': '2',
        }

        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.first()
        self.assertIsNotNone(invoice)

        invoice_item = InvoiceItem.objects.first()
        self.assertIsNotNone(invoice_item)
        self.assertEqual(invoice_item.quantity, 2)
        self.assertEqual(invoice_item.unit_price, self.product.price)  # ✅ التأكد من تحديث السعر تلقائيًا
