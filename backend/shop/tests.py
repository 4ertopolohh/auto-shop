import json
import uuid
from decimal import Decimal
from unittest.mock import patch
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, Client, override_settings
from .models import Category, Product, SiteSettings, Order, Integration
from .integrations import provider, ProviderUnavailable, YooKassaProvider

class CommerceTests(TestCase):
    def setUp(self):
        SiteSettings.objects.create(pk=1)
        cat=Category.objects.create(name='Тормоза',slug='brakes')
        self.p=Product.objects.create(name='Диск',slug='disc',sku='ABC',brand='BREMBO',category=cat,price=Decimal('1000'),stock=2,description='Описание',specs={'Диаметр':'256 мм'},compatibility=[{'make':'VW','model':'Polo','years':'2015'}])
        self.payload={'items':[{'id':self.p.id,'quantity':2}],'delivery':'pickup','point':'MSK-01','idempotency_key':str(uuid.uuid4())}
    def post(self, url, data): return self.client.post('/api/'+url,json.dumps(data),content_type='application/json')
    def test_catalog_filters_and_private_configuration(self):
        self.assertEqual(self.client.get('/api/products/?q=ABC&category=brakes&make=VW').json()['count'],1)
        self.assertEqual(self.client.get('/api/products/?make=Toyota').json()['count'],0)
        self.assertEqual(self.client.get('/api/products/?min=NaN').status_code,400)
        payload=self.client.get('/api/bootstrap/').json()
        self.assertNotIn('local_test_mode',payload)
        self.assertNotIn('encrypted_secret',str(payload))
    def test_price_is_server_controlled_and_checkout_idempotent(self):
        r=self.post('checkout/',self.payload)
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.json()['total'],'2350.00')
        again=self.post('checkout/',self.payload)
        self.assertEqual(r.json()['id'],again.json()['id']);self.assertEqual(Order.objects.count(),1)
        order=Order.objects.get();self.assertEqual(order.phone,'+7 (000) 000-00-00')
    def test_contacts_and_forged_prices_are_rejected_without_storage(self):
        for key,value in [('email','real@example.com'),('phone','89991234567'),('total',1)]:
            self.assertEqual(self.post('checkout/',{**self.payload,key:value}).status_code,400)
        self.assertFalse(Order.objects.exists())
    def test_stock_and_duplicate_lines(self):
        self.payload['items'][0]['quantity']=3
        self.assertEqual(self.post('checkout/',self.payload).status_code,409)
        self.payload['items']=[{'id':self.p.id,'quantity':1}]*2
        self.assertEqual(self.post('checkout/',self.payload).status_code,409)
    def test_payment_transitions_and_immutability(self):
        order=self.post('checkout/',self.payload).json()
        url=f"orders/{order['id']}/payment/"
        self.assertEqual(self.post(url,{'outcome':'failure'}).json()['status'],'failed')
        self.assertEqual(self.post(url,{'outcome':'success'}).json()['status'],'paid')
        self.assertEqual(self.post(url,{'outcome':'cancel'}).json()['status'],'paid')
        self.p.refresh_from_db();self.assertEqual(self.p.stock,2)
    def test_csrf_and_admin_permissions(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/api/checkout/',json.dumps(self.payload),content_type='application/json').status_code,403)
        response=c.get('/api/bootstrap/');token=response.json()['csrf']
        self.assertEqual(c.post('/api/checkout/',json.dumps(self.payload),content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,201)
        self.assertEqual(c.get('/admin/shop/product/import/').status_code,302)
    @override_settings(LOCAL_ENVIRONMENT=False)
    def test_demo_mode_blocked_outside_local(self):
        with self.assertRaises(ProviderUnavailable):provider()
        with self.assertRaises(ValidationError):SiteSettings.objects.get().full_clean()
    def test_real_network_blocked_even_with_configuration(self):
        with patch('httpx.Client') as network:
            with self.assertRaises(ProviderUnavailable):YooKassaProvider()
            network.assert_not_called()
    def test_secret_encryption(self):
        config=Integration(provider='yookassa');config.set_secret('not-a-real-key');config.save()
        self.assertNotIn('not-a-real-key',config.encrypted_secret);self.assertEqual(config.secret(),'not-a-real-key')
    def test_sitemap_and_robots(self):
        self.assertContains(self.client.get('/robots.txt'),'Disallow: /')
        self.assertContains(self.client.get('/sitemap.xml'),'/product/disc')
