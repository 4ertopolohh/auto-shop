from django.core.management.base import BaseCommand
from shop.models import Category,Product,ProductImage
from django.db import transaction
from django.conf import settings
class Command(BaseCommand):
    help='Установить фотографии демонстрационного каталога, сохранив собственные загрузки администратора'
    @transaction.atomic
    def handle(self,*args,**options):
        for product in Product.objects.prefetch_related('images'):
            name=f'catalog-photos/{product.slug}.webp'
            if not (settings.MEDIA_ROOT/name).is_file():continue
            existing=list(product.images.all())
            if any(not (i.image.name.startswith(f'products/{product.slug}-') or i.image.name==name) for i in existing):continue
            product.images.all().delete()
            ProductImage.objects.bulk_create([ProductImage(product=product,image=name,position=n,alt=f'{product.name} — '+['общий вид','деталь фотографии','крупный план'][n]) for n in range(3)])
        for slug,photo in {'brakes':'brembo-disc','filters':'mann-oil','engine':'mahle-piston','suspension':'kyb-shock','electrics':'ngk-spark','oil':'motul-oil'}.items():
            category=Category.objects.filter(slug=slug).first()
            if category and (settings.MEDIA_ROOT/f'catalog-photos/{photo}.webp').is_file() and (not category.image or category.image.name.startswith('catalog-photos/')):
                category.image.name=f'catalog-photos/{photo}.webp';category.save(update_fields=['image'])
        self.stdout.write('Демонстрационные фотографии установлены.')
