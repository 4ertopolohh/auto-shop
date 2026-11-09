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
    def test_search_handles_cyrillic_case_and_reordered_words(self):
        self.p.name='Фильтр масляный';self.p.save(update_fields=['name'])
        for query in ['фильтр','ФИЛЬТР','масляный фильтр','brembo фильтр']:
            self.assertEqual(self.client.get('/api/products/',{'q':query}).json()['count'],1,query)
        self.assertEqual(self.client.get('/api/products/',{'q':'фильтр свеча'}).json()['count'],0)

    def test_demo_photos_install_idempotently_and_preserve_uploaded_media(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from django.core.management import call_command
        from PIL import Image
        from .models import ProductImage
        self.p.slug='brembo-disc';self.p.save(update_fields=['slug'])
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=Path(directory)):
            target=Path(directory)/'catalog-photos/brembo-disc.webp'
            target.parent.mkdir();Image.new('RGB',(32,32),'white').save(target,'WEBP')
            call_command('install_demo_photos',verbosity=0)
            call_command('install_demo_photos',verbosity=0)
            self.assertEqual(self.p.images.count(),3)
            data=self.client.get('/api/bootstrap/').json()
            self.assertTrue(data['categories'][0]['image'].endswith('/catalog-photos/brembo-disc.webp'))
            self.p.images.all().delete()
            custom=ProductImage.objects.create(product=self.p,image='products/owner-photo.webp',position=0)
            call_command('install_demo_photos',verbosity=0)
            self.assertEqual(list(self.p.images.values_list('id',flat=True)),[custom.id])

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

    def test_analytics_accepts_only_anonymous_enum(self):
        from .models import IntegrationLog
        self.assertEqual(self.post('analytics/',{'event':'purchase'}).status_code,200)
        self.assertEqual(self.post('analytics/',{'event':'purchase','email':'real@example.com'}).status_code,400)
        self.assertEqual(IntegrationLog.objects.get().result,'purchase')

    def test_disabled_local_mode_blocks_checkout(self):
        config=SiteSettings.objects.get();config.local_test_mode=False;config.save()
        self.assertEqual(self.post('checkout/',self.payload).status_code,503)
        self.assertFalse(Order.objects.exists())

class ImportTests(TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.directory=tempfile.TemporaryDirectory();self.root=Path(self.directory.name)
        self.override=override_settings(PRIVATE_DIR=self.root,MEDIA_ROOT=self.root/'media');self.override.enable()
        from django.contrib.auth import get_user_model
        self.admin=get_user_model().objects.create_superuser(username='testadmin',password='local-test-only')
        self.client.force_login(self.admin)
    def tearDown(self):
        self.override.disable();self.directory.cleanup()
    def workbook(self, rows=None):
        from io import BytesIO
        from openpyxl import Workbook
        from .importing import HEADERS
        book=Workbook();book.active.append(HEADERS)
        for row in rows or [['NEW-01','Фильтр','Фильтры','MANN',890,5,'OEM-01','Описание','{"Высота":"120 мм"}','[{"make":"VW","model":"Polo","years":"2015"}]','',400]]:book.active.append(row)
        output=BytesIO();book.save(output);output.seek(0)
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile('catalog.xlsx',output.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    def test_preview_confirmation_and_update(self):
        response=self.client.post('/admin/shop/product/import/',{'workbook':self.workbook()})
        self.assertContains(response,'Предпросмотр: 1');self.assertEqual(Product.objects.count(),0)
        token=self.client.session['catalog_import_token']
        confirmed=self.client.post('/admin/shop/product/import/',{'confirm':'1','token':token})
        self.assertEqual(confirmed.status_code,302);self.assertEqual(Product.objects.count(),1)
        self.client.post('/admin/shop/product/import/',{'workbook':self.workbook()})
        token=self.client.session['catalog_import_token']
        self.client.post('/admin/shop/product/import/',{'confirm':'1','token':token})
        self.assertEqual(Product.objects.count(),1)
    def test_template_and_custom_admin_assets(self):
        response=self.client.get('/admin/shop/product/template/')
        self.assertEqual(response.status_code,200);self.assertTrue(response.content.startswith(b'PK'))
        self.assertContains(self.client.get('/admin/shop/product/import/'),'shop/admin.js')
    def test_invalid_price_prevents_any_write(self):
        row=['BAD-01','Фильтр','Фильтры','MANN',-10,5,'','','{}','[]','',400]
        response=self.client.post('/admin/shop/product/import/',{'workbook':self.workbook([row])})
        self.assertContains(response,'Некорректная цена');self.assertFalse(Product.objects.exists())
    def test_confirmation_requires_session_token(self):
        self.assertEqual(self.client.post('/admin/shop/product/import/',{'confirm':'1','token':str(uuid.uuid4())}).status_code,403)
    def test_zip_images_decode_and_reject_unsafe_names(self):
        from io import BytesIO
        from zipfile import ZipFile
        from PIL import Image
        from .importing import inspect_photos,inspect_workbook
        output=BytesIO();Image.new('RGB',(8,8),'white').save(output,'PNG')
        archive=self.root/'photos.zip'
        with ZipFile(archive,'w') as z:z.writestr('filter.png',output.getvalue())
        photos=inspect_photos(archive,[{'photos':['filter.png']}]);self.assertIn('filter.png',photos)
        with self.assertRaises(ValueError):inspect_photos(archive,[{'photos':['missing.jpg']}])
        row=['BAD-02','Фильтр','Фильтры','MANN',10,5,'','','{}','[]','../file.png',400]
        path=self.root/'bad.xlsx';path.write_bytes(self.workbook([row]).read())
        records,errors=inspect_workbook(path);self.assertEqual(records,[]);self.assertTrue(errors)
