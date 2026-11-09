import uuid
from decimal import Decimal
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Category(models.Model):
    image = models.ImageField('Фото категории', upload_to='categories/', blank=True)
    name = models.CharField('Название', max_length=120)
    slug = models.SlugField('Адрес категории', unique=True)
    description = models.TextField('Описание', blank=True)
    illustration = models.CharField('Иллюстрация', max_length=40, default='brakes', help_text='brakes, filters, engine, suspension, electrics, oil')
    position = models.PositiveIntegerField('Порядок', default=0)
    class Meta:
        verbose_name = 'Категория'; verbose_name_plural = 'Категории'; ordering = ['position', 'name']
    def __str__(self): return self.name

class Product(models.Model):
    name = models.CharField('Название', max_length=220)
    slug = models.SlugField('Адрес карточки', unique=True)
    sku = models.CharField('Артикул', max_length=80, unique=True)
    oem = models.CharField('OEM-номер', max_length=160, blank=True)
    brand = models.CharField('Бренд', max_length=80, db_index=True)
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField('Цена, ₽', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    old_price = models.DecimalField('Старая цена, ₽', max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField('Количество на складе', default=0)
    description = models.TextField('Описание')
    specs = models.JSONField('Характеристики', default=dict, help_text='Объект: {"Диаметр": "280 мм"}')
    compatibility = models.JSONField('Совместимость', default=list, help_text='Список: [{"make": "Volkswagen", "model": "Polo", "years": "2015–2022"}]')
    weight = models.PositiveIntegerField('Вес, г', default=500, validators=[MinValueValidator(1)])
    featured = models.BooleanField('На главной', default=False)
    active = models.BooleanField('Опубликован', default=True)
    badge = models.CharField('Метка', max_length=30, blank=True)
    seo_title = models.CharField('SEO-заголовок', max_length=200, blank=True)
    seo_description = models.TextField('SEO-описание', blank=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    class Meta:
        verbose_name = 'Товар'; verbose_name_plural = 'Товары'; ordering = ['id']
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name='positive_product_price')]
    def __str__(self): return f'{self.brand} · {self.name}'
    def clean(self):
        if not isinstance(self.specs, dict) or not all(isinstance(k, str) and isinstance(v, (str, int, float)) for k, v in self.specs.items()):
            raise ValidationError({'specs': 'Укажите объект с названиями и значениями характеристик.'})
        if not isinstance(self.compatibility, list) or not all(isinstance(c, dict) and all(isinstance(c.get(k), str) for k in ('make', 'model', 'years')) for c in self.compatibility):
            raise ValidationError({'compatibility': 'Для каждой модели укажите make, model, years.'})

class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE, related_name='images')
    image = models.FileField('Изображение', upload_to='products/', help_text='PNG, JPEG, WebP; SVG доступны только из встроенного наполнения.')
    alt = models.CharField('Описание изображения', max_length=220, blank=True)
    position = models.PositiveIntegerField('Порядок', default=0)
    class Meta:
        ordering = ['position', 'id']; verbose_name = 'Фото товара'; verbose_name_plural = 'Фотографии'

class SiteSettings(models.Model):
    name = models.CharField('Название магазина', max_length=120, default='Крутящий момент')
    headline = models.CharField('Заголовок главной', max_length=160, default='Всё начинается с правильной детали.')
    intro = models.TextField('Описание главной', default='Запчасти, в которых можно быть уверенным. Найдите свою — по автомобилю, названию или артикулу.')
    local_test_mode = models.BooleanField('Локальный тестовый режим', default=True, help_text='Имитирует СДЭК, ЮKassa и Метрику только при SHOP_ENV=local. Реальные данные не принимаются ни в одном режиме этой демонстрационной сборки.')
    canonical_url = models.URLField('Основной адрес сайта', default='http://localhost:5173')
    seo_title = models.CharField('Название для поисковых систем', max_length=200, default='Крутящий момент — магазин автозапчастей')
    seo_description = models.TextField('Описание для поисковых систем', default='Автозапчасти по марке автомобиля, артикулу и OEM-номеру. Каталог, подбор, доставка СДЭК.')
    allow_indexing = models.BooleanField('Разрешить индексацию', default=False, help_text='По умолчанию демоверсия закрыта от индексации. Карта сайта доступна всегда.')
    metrika_id = models.CharField('Номер счётчика Метрики', max_length=20, blank=True)
    metrika_enabled = models.BooleanField('Включить Метрику', default=False, help_text='В этой демонстрационной сборке события только имитируются, внешние скрипты не загружаются.')
    class Meta:
        verbose_name = 'Настройки сайта'; verbose_name_plural = 'Настройки сайта'
    def __str__(self): return 'Сайт, SEO и тестовый режим'
    def clean(self):
        if self.local_test_mode and not settings.LOCAL_ENVIRONMENT:
            raise ValidationError({'local_test_mode': 'Тестовый режим запрещён вне локальной среды.'})
        if self.metrika_id and not self.metrika_id.isdigit():
            raise ValidationError({'metrika_id': 'Используйте только цифры.'})
    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        super().save(*args, **kwargs)

class Integration(models.Model):
    provider = models.CharField('Сервис', max_length=20, unique=True, choices=[('yookassa','ЮKassa'),('cdek','СДЭК')])
    enabled = models.BooleanField('Включена', default=False)
    account = models.CharField('ID магазина / Account СДЭК', max_length=120, blank=True)
    encrypted_secret = models.TextField('Зашифрованный ключ', blank=True, editable=False)
    sandbox = models.BooleanField('Песочница провайдера', default=True)
    origin_city = models.PositiveIntegerField('Код города отправки СДЭК', default=44, help_text='44 — Москва. Код из справочника СДЭК.')
    warehouse_tariff = models.PositiveIntegerField('Тариф до пункта выдачи', default=136)
    courier_tariff = models.PositiveIntegerField('Тариф до двери', default=137)
    length = models.PositiveIntegerField('Длина упаковки, см', default=30, validators=[MinValueValidator(1)])
    width = models.PositiveIntegerField('Ширина упаковки, см', default=25, validators=[MinValueValidator(1)])
    height = models.PositiveIntegerField('Высота упаковки, см', default=20, validators=[MinValueValidator(1)])
    timeout = models.PositiveIntegerField('Таймаут, сек', default=15, validators=[MinValueValidator(1), MaxValueValidator(30)])
    return_url = models.URLField('Адрес возврата после оплаты', default='http://localhost:5173/checkout')
    class Meta:
        verbose_name = 'Интеграция'; verbose_name_plural = 'Интеграции'
    def __str__(self): return self.get_provider_display()
    def set_secret(self, value): self.encrypted_secret = Fernet(settings.FIELD_KEY.encode()).encrypt(value.encode()).decode()
    def secret(self): return Fernet(settings.FIELD_KEY.encode()).decrypt(self.encrypted_secret.encode()).decode() if self.encrypted_secret else ''

class Order(models.Model):
    id = models.UUIDField('Номер', primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.UUIDField('Ключ повторного запроса', unique=True)
    items = models.JSONField('Состав заказа', default=list)
    recipient = models.CharField('Получатель (вымышленный)', max_length=80, default='Алексей Демонстрационный')
    phone = models.CharField('Телефон (вымышленный)', max_length=30, default='+7 (000) 000-00-00')
    email = models.EmailField('Почта (вымышленная)', default='buyer@example.invalid')
    destination = models.CharField('Демонстрационный адрес', max_length=180)
    delivery = models.CharField('Способ доставки', max_length=20)
    delivery_price = models.DecimalField('Доставка, ₽', max_digits=10, decimal_places=2)
    total = models.DecimalField('Итого, ₽', max_digits=12, decimal_places=2)
    status = models.CharField('Статус', max_length=20, default='pending', choices=[('pending','Ожидает оплаты'),('paid','Оплачен (имитация)'),('failed','Ошибка оплаты (имитация)'),('cancelled','Отменён')])
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    class Meta:
        verbose_name = 'Заказ'; verbose_name_plural = 'Заказы'; ordering = ['-created_at']
    def __str__(self): return f'КМ-{str(self.id)[:8].upper()}'

class IntegrationLog(models.Model):
    provider = models.CharField('Сервис', max_length=30)
    operation = models.CharField('Операция', max_length=80)
    result = models.CharField('Результат', max_length=180)
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    class Meta:
        verbose_name = 'Событие интеграции'; verbose_name_plural = 'Журнал интеграций'; ordering = ['-created_at']
