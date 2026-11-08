import json
import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps
from xml.sax.saxutils import escape
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_GET, require_POST
from .models import Category, Product, Order, IntegrationLog
from .integrations import configuration, provider, ProviderUnavailable

def api_errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try: return view(request, *args, **kwargs)
        except (ValueError, TypeError, KeyError, InvalidOperation, ValidationError):
            return JsonResponse({'error': 'Проверьте параметры запроса. Персональные данные не принимаются.'}, status=400)
        except ProviderUnavailable as e:
            return JsonResponse({'error': str(e)}, status=503)
    return wrapped

def body(request, allowed):
    if len(request.body) > 16000: raise ValueError()
    value = json.loads(request.body)
    if not isinstance(value, dict) or set(value) - set(allowed): raise ValueError()
    return value

def limited(request, scope, maximum=60):
    # No IP, fingerprint, contact data, or analytics identifier is stored.
    # A process-wide anonymous bucket protects the local demonstration.
    key = 'rate:' + scope
    cache.add(key, 0, 60)
    return cache.incr(key) > maximum

def serialize_product(p):
    return {'id': p.id, 'name': p.name, 'slug': p.slug, 'sku': p.sku, 'oem': p.oem, 'brand': p.brand,
            'category': p.category.slug, 'category_name': p.category.name, 'price': str(p.price),
            'old_price': str(p.old_price) if p.old_price else None, 'stock': p.stock, 'badge': p.badge,
            'description': p.description, 'specs': p.specs, 'compatibility': p.compatibility,
            'seo_title': p.seo_title, 'seo_description': p.seo_description,
            'images': [{'url': i.image.url, 'alt': i.alt or p.name} for i in p.images.all()]}

@require_GET
def bootstrap(request):
    config = configuration()
    return JsonResponse({'csrf': get_token(request), 'name': config.name, 'headline': config.headline, 'intro': config.intro,
        'seo_title': config.seo_title, 'seo_description': config.seo_description, 'canonical_url': config.canonical_url,
        'allow_indexing': config.allow_indexing, 'categories': list(Category.objects.values('name', 'slug', 'illustration', 'description')),
        'brands': list(Product.objects.filter(active=True).values_list('brand', flat=True).distinct().order_by('brand')),
        'vehicles': sorted({(c['make'], c['model']) for p in Product.objects.filter(active=True) for c in p.compatibility})})

@require_GET
@api_errors
def products(request, slug=None):
    qs = Product.objects.filter(active=True).select_related('category').prefetch_related('images')
    if slug:
        p = qs.filter(slug=slug).first()
        return JsonResponse(serialize_product(p)) if p else JsonResponse({'error': 'Товар не найден'}, status=404)
    q = request.GET.get('q', '')[:120]
    if q: qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(oem__icontains=q) | Q(brand__icontains=q))
    for field in ['category', 'brand']:
        if request.GET.get(field): qs = qs.filter(**{('category__slug' if field == 'category' else field): request.GET[field][:80]})
    if request.GET.get('stock') == '1': qs = qs.filter(stock__gt=0)
    if request.GET.get('featured') == '1': qs = qs.filter(featured=True)
    for param, lookup in [('min', 'price__gte'), ('max', 'price__lte')]:
        if request.GET.get(param):
            price = Decimal(request.GET[param])
            if not price.is_finite() or price < 0: raise ValueError()
            qs = qs.filter(**{lookup: price})
    if request.GET.get('make') or request.GET.get('model'):
        ids = [p.id for p in qs if any((not request.GET.get('make') or c['make'] == request.GET['make']) and (not request.GET.get('model') or c['model'] == request.GET['model']) for c in p.compatibility)]
        qs = qs.filter(pk__in=ids)
    qs = qs.order_by({'price': 'price', '-price': '-price', 'name': 'name', 'new': '-id'}.get(request.GET.get('sort'), 'id'))
    page = max(1, int(request.GET.get('page', 1))); size = 12
    return JsonResponse({'count': qs.count(), 'page': page, 'results': [serialize_product(p) for p in qs[(page-1)*size:page*size]]})

@require_GET
@api_errors
def delivery_options(request): return JsonResponse({'points': provider().delivery_options()})

def order_data(order):
    return {'id': str(order.id), 'number': str(order), 'items': order.items, 'recipient': order.recipient, 'phone': order.phone,
            'email': order.email, 'destination': order.destination, 'delivery': order.delivery,
            'delivery_price': str(order.delivery_price), 'total': str(order.total), 'status': order.status}

@require_POST
@api_errors
def checkout(request):
    if limited(request, 'checkout', 30): return JsonResponse({'error': 'Слишком много запросов. Попробуйте через минуту.'}, status=429)
    data = body(request, ['items', 'delivery', 'point', 'idempotency_key'])
    key = uuid.UUID(data['idempotency_key'])
    existing = Order.objects.filter(idempotency_key=key).first()
    if existing: return JsonResponse(order_data(existing))
    adapter = provider()
    if not isinstance(data['items'], list) or not 1 <= len(data['items']) <= 50: raise ValueError()
    with transaction.atomic():
        items = []; subtotal = Decimal(0); seen = set()
        for item in data['items']:
            if not isinstance(item, dict) or set(item) != {'id', 'quantity'}: raise ValueError()
            if type(item['id']) is not int or type(item['quantity']) is not int: raise ValueError()
            p = Product.objects.filter(pk=item['id'], active=True).first()
            qty = item['quantity']
            if not p or p.id in seen or not 1 <= qty <= min(p.stock, 99):
                return JsonResponse({'error': 'Количество или наличие товара изменилось. Обновите корзину.'}, status=409)
            seen.add(p.id); subtotal += p.price * qty
            items.append({'id': p.id, 'sku': p.sku, 'name': p.name, 'quantity': qty, 'price': str(p.price)})
        price, destination = adapter.quote(data['delivery'], data['point'])
        try:
            with transaction.atomic():
                order = Order.objects.create(idempotency_key=key, items=items, destination=destination, delivery=data['delivery'], delivery_price=price, total=subtotal+price)
        except IntegrityError:
            order = Order.objects.get(idempotency_key=key)
        IntegrationLog.objects.create(provider='СДЭК', operation='Имитация оформления доставки', result=f'{order}: тариф {price} ₽')
    return JsonResponse(order_data(order), status=201)

@require_POST
@api_errors
def payment(request, order_id):
    if limited(request, 'payment', 60): return JsonResponse({'error': 'Повторите через минуту.'}, status=429)
    data = body(request, ['outcome'])
    if data.get('outcome') not in ('success', 'failure', 'cancel'): raise ValueError()
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(pk=order_id).first()
        if not order: return JsonResponse({'error': 'Заказ не найден'}, status=404)
        if order.status not in ('paid', 'cancelled'): provider().pay(order, data['outcome'])
    return JsonResponse(order_data(order))

@require_GET
def robots(request):
    config = configuration()
    rules = 'Allow: /\nDisallow: /admin/\nDisallow: /api/\nDisallow: /cart\nDisallow: /checkout' if config.allow_indexing else 'Disallow: /'
    return HttpResponse(f'User-agent: *\n{rules}\nSitemap: {config.canonical_url.rstrip("/")}/sitemap.xml\n', content_type='text/plain')

@require_GET
def sitemap(request):
    base = configuration().canonical_url.rstrip('/')
    urls = ['/', '/catalog', '/delivery', '/about'] + [f'/product/{p.slug}' for p in Product.objects.filter(active=True)]
    urls += [f'/catalog?category={c.slug}' for c in Category.objects.all()]
    return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{escape(base+u)}</loc></url>' for u in urls) + '</urlset>', content_type='application/xml')
