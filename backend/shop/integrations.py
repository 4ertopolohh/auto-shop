"""One provider seam. Demo policy is enforced before any external request."""
from decimal import Decimal
import httpx
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Integration, IntegrationLog, SiteSettings

class ProviderUnavailable(Exception): pass

def configuration():
    return SiteSettings.objects.get_or_create(pk=1)[0]

class MockProvider:
    def delivery_options(self):
        return [
            {'id': 'MSK-01', 'city': 'Москва', 'label': 'Пункт выдачи на Лесной', 'address': 'ул. Примерная, 12', 'hours': 'Ежедневно, 09:00–21:00', 'price': 350, 'days': '2–3 дня'},
            {'id': 'MSK-02', 'city': 'Москва', 'label': 'Пункт выдачи у Парка', 'address': 'ул. Учебная, 8', 'hours': 'Ежедневно, 10:00–20:00', 'price': 350, 'days': '2–3 дня'},
            {'id': 'SPB-01', 'city': 'Санкт-Петербург', 'label': 'Пункт выдачи на Невской', 'address': 'ул. Примерная, 24', 'hours': 'Ежедневно, 09:00–21:00', 'price': 490, 'days': '3–4 дня'},
            {'id': 'KZN-01', 'city': 'Казань', 'label': 'Пункт выдачи Центральный', 'address': 'ул. Учебная, 5', 'hours': 'Ежедневно, 09:00–20:00', 'price': 550, 'days': '3–5 дней'},
        ]
    def quote(self, delivery, point):
        option = next((p for p in self.delivery_options() if p['id'] == point), None)
        if not option or delivery not in ('pickup', 'courier'):
            raise ValidationError('Выберите доступный способ и пункт доставки.')
        return Decimal(option['price'] + (200 if delivery == 'courier' else 0)), f"{option['city']}, {option['address']}" if delivery == 'pickup' else f"{option['city']}, ул. Демонстрационная, 10"
    def pay(self, order, outcome):
        order.status = {'success': 'paid', 'failure': 'failed', 'cancel': 'cancelled'}[outcome]
        order.save(update_fields=['status'])
        IntegrationLog.objects.create(provider='ЮKassa', operation='Имитация оплаты', result=f'{order}: {order.get_status_display()}')
        return order.status

def provider():
    if settings.LOCAL_ENVIRONMENT and configuration().local_test_mode:
        return MockProvider()
    # DEMO_SITE is deliberately not an admin-editable setting.
    raise ProviderUnavailable('Демонстрационный сценарий доступен при включённом локальном тестовом режиме. Реальные операции в этой сборке заблокированы.')

class RealProvider:
    """Transport adapters for a future commercial distribution; disabled in demo."""
    def __init__(self, name):
        if settings.DEMO_SITE:
            raise ProviderUnavailable('В демонстрационной версии внешние операции запрещены.')
        self.config = Integration.objects.get(provider=name, enabled=True)
        if not self.config.account or not self.config.encrypted_secret:
            raise ProviderUnavailable('Заполните идентификатор и секретный ключ в настройках интеграции.')
    def request(self, method, url, **kwargs):
        try:
            with httpx.Client(timeout=self.config.timeout, follow_redirects=False) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError):
            raise ProviderUnavailable('Сервис временно недоступен. Повторите операцию позже.') from None

class YooKassaProvider(RealProvider):
    def __init__(self): super().__init__('yookassa')
    def create_payment(self, order):
        return self.request('POST', 'https://api.yookassa.ru/v3/payments', auth=(self.config.account, self.config.secret()), headers={'Idempotence-Key': str(order.id)}, json={
            'amount': {'value': str(order.total), 'currency': 'RUB'}, 'capture': True,
            'confirmation': {'type': 'redirect', 'return_url': self.config.return_url},
            'description': str(order), 'metadata': {'order_id': str(order.id)},
        })
    def get_payment(self, payment_id):
        import uuid
        payment_id = str(uuid.UUID(payment_id))
        return self.request('GET', f'https://api.yookassa.ru/v3/payments/{payment_id}', auth=(self.config.account, self.config.secret()))

class CdekProvider(RealProvider):
    def __init__(self):
        super().__init__('cdek')
        self.base = 'https://api.edu.cdek.ru/v2' if self.config.sandbox else 'https://api.cdek.ru/v2'
    def headers(self):
        token = self.request('POST', self.base + '/oauth/token', data={'grant_type': 'client_credentials', 'client_id': self.config.account, 'client_secret': self.config.secret()})
        return {'Authorization': f"Bearer {token['access_token']}"}
    def points(self, city_code):
        return self.request('GET', self.base + '/deliverypoints', headers=self.headers(), params={'city_code': int(city_code), 'type': 'PVZ'})
    def quote(self, city_code, weight, courier=False):
        return self.request('POST', self.base + '/calculator/tariff', headers=self.headers(), json={
            'type': 1, 'tariff_code': self.config.courier_tariff if courier else self.config.warehouse_tariff,
            'from_location': {'code': self.config.origin_city}, 'to_location': {'code': int(city_code)},
            'packages': [{'weight': int(weight), 'length': self.config.length, 'width': self.config.width, 'height': self.config.height}],
        })
    def create_shipment(self, order, recipient, destination, packages):
        return self.request('POST', self.base + '/orders', headers=self.headers(), json={
            'type': 1, 'number': str(order.id), 'tariff_code': self.config.warehouse_tariff,
            'recipient': recipient, 'delivery_point': destination, 'packages': packages,
        })
