import io
import json
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath
from zipfile import ZipFile, BadZipFile
from PIL import Image, UnidentifiedImageError
from openpyxl import load_workbook
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify
from .models import Product, Category, ProductImage

HEADERS = ['Артикул', 'Название', 'Категория', 'Бренд', 'Цена', 'Наличие', 'OEM', 'Описание', 'Характеристики', 'Совместимость', 'Фото', 'Вес, г']

def inspect_workbook(source):
    if source.stat().st_size > 5 * 1024 * 1024: raise ValueError('Таблица больше 5 МБ.')
    with ZipFile(source) as z:
        if sum(i.file_size for i in z.infolist()) > 30 * 1024 * 1024: raise ValueError('Слишком большой объём распакованной таблицы.')
    book = load_workbook(source, read_only=True, data_only=False)
    try:
        sheet = book.active
        if sheet.max_row > 2001 or sheet.max_column > 40: raise ValueError('Не более 2000 строк и 40 колонок за импорт.')
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows, ())
        if list(headers) != HEADERS: raise ValueError('Заголовки не соответствуют шаблону. Скачайте шаблон на этой странице.')
        records = []; errors = []; seen = set()
        for number, row in enumerate(rows, 2):
            if not any(v is not None for v in row): continue
            try:
                data = dict(zip(HEADERS, row))
                if any(isinstance(v, str) and v.startswith('=') for v in row): raise ValueError('Формулы запрещены; вставьте значения.')
                sku = str(data['Артикул'] or '').strip()
                if not sku or len(sku)>80 or sku in seen: raise ValueError('Артикул пустой, слишком длинный или повторяется.')
                seen.add(sku)
                price = Decimal(str(data['Цена']))
                if not price.is_finite() or not Decimal('0') < price <= Decimal('99999999.99') or price.as_tuple().exponent < -2: raise ValueError('Некорректная цена.')
                stock = int(data['Наличие'])
                if stock < 0 or stock > 1000000 or Decimal(str(data['Наличие'])) != stock: raise ValueError('Некорректное наличие.')
                name = str(data['Название'] or '').strip(); brand = str(data['Бренд'] or '').strip(); category = str(data['Категория'] or '').strip()
                if not name or len(name)>220 or not brand or len(brand)>80 or not category or len(category)>120: raise ValueError('Проверьте название, бренд и категорию.')
                specs = json.loads(data['Характеристики'] or '{}'); compatibility = json.loads(data['Совместимость'] or '[]')
                candidate = Product(name=name, specs=specs, compatibility=compatibility)
                candidate.clean()
                photos = [x.strip() for x in str(data['Фото'] or '').split(';') if x.strip()]
                if len(photos)>12 or any(PurePosixPath(x).name != x or '\\' in x for x in photos): raise ValueError('Фото: укажите до 12 имён файлов без путей.')
                weight = int(data['Вес, г'] or 500)
                if not 1 <= weight <= 1000000: raise ValueError('Некорректный вес.')
                records.append({'sku': sku, 'name': name, 'brand': brand, 'category': category, 'price': str(price), 'stock': stock, 'oem': str(data['OEM'] or '')[:160], 'description': str(data['Описание'] or ''), 'specs': specs, 'compatibility': compatibility, 'photos': photos, 'weight': weight, 'action': 'Обновление' if Product.objects.filter(sku=sku).exists() else 'Создание'})
            except Exception as e:
                from django.core.exceptions import ValidationError
                if not isinstance(e, (ValueError, TypeError, InvalidOperation, ValidationError)): raise
                errors.append(f'Строка {number}: {str(e)[:180]}')
        if not records and not errors: errors.append('Таблица не содержит товаров.')
        return records, errors
    finally: book.close()

def inspect_photos(path, records):
    required = {p for row in records for p in row['photos']}
    if not required: return {}
    if not path.exists(): raise ValueError('Для указанных фотографий нужен ZIP-архив.')
    result = {}
    try:
        with ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries)>300 or sum(i.file_size for i in entries)>60*1024*1024: raise ValueError('Архив превышает лимит: 300 файлов / 60 МБ после распаковки.')
            for name in required:
                info = archive.getinfo(name)
                if info.file_size > 8*1024*1024: raise ValueError(f'Слишком большое изображение: {name}')
                image = Image.open(io.BytesIO(archive.read(info)))
                if image.width*image.height > 20_000_000 or image.format not in ('JPEG','PNG','WEBP'): raise ValueError('Допустимы JPEG, PNG, WebP до 20 Мп.')
                image.thumbnail((1400,1400))
                output = io.BytesIO(); image.convert('RGB').save(output, 'WEBP', quality=86)
                result[name] = output.getvalue()
    except (BadZipFile, KeyError, UnidentifiedImageError, Image.DecompressionBombError):
        raise ValueError('Архив повреждён или не содержит указанные изображения.') from None
    return result

def commit_import(records, photos):
    written = []
    try:
        with transaction.atomic():
            for row in records:
                values = {k:v for k,v in row.items() if k not in ('category','photos','action')}
                category, _ = Category.objects.get_or_create(name=row['category'], defaults={'slug': 'category-'+uuid.uuid4().hex[:10]})
                values['category'] = category
                existing = Product.objects.filter(sku=row['sku']).first()
                if not existing: values['slug'] = slugify(row['brand']+'-'+row['sku'])[:45]+'-'+uuid.uuid4().hex[:6]
                product, _ = Product.objects.update_or_create(sku=row['sku'], defaults=values)
                if row['photos']:
                    product.images.all().delete()
                    for index, name in enumerate(row['photos']):
                        obj = ProductImage(product=product, position=index, alt=product.name)
                        obj.image.save(uuid.uuid4().hex+'.webp', ContentFile(photos[name]), save=True)
                        written.append(obj.image)
    except Exception:
        for file in written: file.delete(save=False)
        raise
