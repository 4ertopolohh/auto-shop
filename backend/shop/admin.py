import uuid
import secrets
from pathlib import Path
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Category, Product, ProductImage, SiteSettings, Integration, Order, IntegrationLog
from .importing import HEADERS, inspect_workbook, inspect_photos, commit_import

admin.site.site_header = 'Крутящий момент · управление'
admin.site.site_title = 'Крутящий момент'
admin.site.index_title = 'Каталог, заказы и настройки'
admin.site.site_url = 'http://127.0.0.1:5173/'

class PhotoForm(forms.ModelForm):
    class Meta: model = ProductImage; fields = '__all__'
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'content_type'):
            from PIL import Image
            if image.size > 8*1024*1024: raise forms.ValidationError('Максимум 8 МБ.')
            try:
                im = Image.open(image)
                if im.format not in ('PNG','JPEG','WEBP') or im.width*im.height>20_000_000: raise ValueError()
                im.verify(); image.seek(0)
            except Exception: raise forms.ValidationError('Загрузите корректный JPEG, PNG или WebP.')
        return image

class ImageInline(admin.TabularInline):
    model = ProductImage; form = PhotoForm; extra = 0
    fields = ['image','preview','alt','position']; readonly_fields = ['preview']
    @admin.display(description='Предпросмотр')
    def preview(self, obj):
        return format_html('<img src="{}" width="90" height="70" style="object-fit:contain" alt=""/>', obj.image.url) if obj.image else '—'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name','slug','position']; prepopulated_fields = {'slug': ['name']}; search_fields = ['name']

class ImportForm(forms.Form):
    workbook = forms.FileField(label='Таблица .xlsx', help_text='До 5 МБ, до 2000 товаров. Используйте шаблон ниже.')
    photos = forms.FileField(label='Фотографии .zip', required=False, help_text='До 30 МБ. Имена файлов из колонки «Фото», разделённые точкой с запятой.')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    change_list_template = 'admin/shop/product_list.html'
    list_display = ['name','sku','brand','category','price','stock','active']; list_editable = ['price','stock','active']
    list_filter = ['category','brand','active','featured']; search_fields = ['name','sku','oem']; inlines = [ImageInline]
    prepopulated_fields = {'slug': ['brand','sku']}; readonly_fields = ['updated_at']
    fieldsets = [('Товар', {'fields': ['name','slug','sku','oem','brand','category','description','badge']}), ('Продажи', {'fields': ['price','old_price','stock','weight','featured','active']}), ('Подбор и характеристики', {'fields': ['specs','compatibility']}), ('Поисковая оптимизация', {'fields': ['seo_title','seo_description','updated_at']})]
    def get_urls(self):
        return [path('import/', self.admin_site.admin_view(self.import_view), name='shop_product_import'), path('template/', self.admin_site.admin_view(self.template_view), name='shop_product_template')] + super().get_urls()
    def template_view(self, request):
        if not self.has_change_permission(request): raise PermissionDenied()
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
        book = Workbook(); sheet = book.active; sheet.title = 'Товары'; sheet.append(HEADERS)
        sheet.append(['KM-EXAMPLE-01','Фильтр масляный','Фильтры','MANN-FILTER',890,12,'03C115561H','Сменный масляный фильтр','{"Высота": "123 мм"}','[{"make":"Volkswagen","model":"Polo","years":"2015–2022"}]','',350])
        for cell in sheet[1]: cell.font = Font(color='FFFFFF', bold=True); cell.fill = PatternFill('solid', fgColor='25282A')
        for n in range(1,13): sheet.column_dimensions[get_column_letter(n)].width = 24
        sheet.freeze_panes = 'A2'; sheet.auto_filter.ref = sheet.dimensions
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="catalog-template.xlsx"'; book.save(response); return response
    def import_view(self, request):
        if not (self.has_change_permission(request) and self.has_add_permission(request)): raise PermissionDenied()
        form = ImportForm(); records=[]; errors=[]; token=None
        directory = settings.PRIVATE_DIR / 'imports'; directory.mkdir(exist_ok=True)
        # Bounded retention for abandoned previews.
        import time
        for old in directory.iterdir():
            if old.is_file() and time.time()-old.stat().st_mtime > 86400: old.unlink(missing_ok=True)
        if request.method == 'POST':
            if request.POST.get('confirm'):
                token = request.POST.get('token','')
                if not secrets.compare_digest(token, request.session.get('catalog_import_token','')) or not token: raise PermissionDenied()
                try:
                    source = directory / (str(uuid.UUID(token))+'.xlsx')
                    records, errors = inspect_workbook(source)
                    photos = inspect_photos(source.with_suffix('.zip'), records)
                    if not errors:
                        commit_import(records, photos)
                        source.unlink(missing_ok=True); source.with_suffix('.zip').unlink(missing_ok=True)
                        request.session.pop('catalog_import_token', None)
                        messages.success(request, f'Импорт завершён. Обработано товаров: {len(records)}.')
                        return HttpResponseRedirect(reverse('admin:shop_product_changelist'))
                except (ValueError, FileNotFoundError) as e: errors = [str(e)]
            else:
                form = ImportForm(request.POST, request.FILES)
                if form.is_valid():
                    file = form.cleaned_data['workbook']; photos = form.cleaned_data['photos']
                    if not file.name.lower().endswith('.xlsx') or file.size > 5*1024*1024 or (photos and (not photos.name.lower().endswith('.zip') or photos.size>30*1024*1024)):
                        errors = ['Проверьте тип и размер файлов.']
                    else:
                        token = str(uuid.uuid4()); request.session['catalog_import_token'] = token
                        source = directory / (token+'.xlsx')
                        with source.open('wb') as output:
                            for chunk in file.chunks(): output.write(chunk)
                        if photos:
                            with source.with_suffix('.zip').open('wb') as output:
                                for chunk in photos.chunks(): output.write(chunk)
                        try: records, errors = inspect_workbook(source); inspect_photos(source.with_suffix('.zip'), records)
                        except Exception as e:
                            from zipfile import BadZipFile
                            if not isinstance(e, (ValueError, BadZipFile)): raise
                            errors = [str(e)]
        return TemplateResponse(request, 'admin/shop/import.html', {**self.admin_site.each_context(request), 'title': 'Импорт каталога из Excel', 'form': form, 'records': records[:100], 'total': len(records), 'errors': errors, 'token': token, 'opts': self.model._meta})

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [('Витрина', {'fields': ['name','headline','intro']}), ('Режим работы', {'fields': ['local_test_mode']}), ('Поисковые системы', {'fields': ['canonical_url','seo_title','seo_description','allow_indexing']}), ('Яндекс Метрика', {'fields': ['metrika_enabled','metrika_id']})]
    def has_add_permission(self, request): return not SiteSettings.objects.exists()
    def has_delete_permission(self, request, obj=None): return False
    def change_view(self, request, object_id, form_url='', extra_context=None):
        if settings.LOCAL_ENVIRONMENT and SiteSettings.objects.filter(pk=1, local_test_mode=True).exists():
            messages.warning(request, 'Включён локальный тестовый режим: СДЭК, ЮKassa и Метрика имитируются. Внешних запросов и реальных платежей нет.')
        return super().change_view(request, object_id, form_url, extra_context)

class IntegrationForm(forms.ModelForm):
    secret_key = forms.CharField(label='Новый секретный ключ', required=False, widget=forms.PasswordInput(render_value=False), help_text='Оставьте пустым, чтобы сохранить действующий. Значение зашифровано в БД.')
    clear_secret = forms.BooleanField(label='Удалить сохранённый ключ', required=False)
    class Meta: model = Integration; exclude = ['encrypted_secret']
    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get('clear_secret'): obj.encrypted_secret = ''
        elif self.cleaned_data.get('secret_key'): obj.set_secret(self.cleaned_data['secret_key'])
        if commit: obj.save()
        return obj

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    form = IntegrationForm; list_display = ['provider','enabled','sandbox','readiness']; readonly_fields = ['readiness']
    fieldsets = [('Подключение', {'fields': ['provider','enabled','sandbox','account','secret_key','clear_secret','readiness','timeout']}), ('ЮKassa', {'fields': ['return_url']}), ('СДЭК', {'fields': ['origin_city','warehouse_tariff','courier_tariff','length','width','height']})]
    @admin.display(description='Готовность')
    def readiness(self, obj):
        if settings.LOCAL_ENVIRONMENT and SiteSettings.objects.filter(pk=1,local_test_mode=True).exists(): return 'Подключена в локальном тестовом режиме'
        if not obj.enabled: return 'Отключена'
        if not obj.account or not obj.encrypted_secret: return 'Ошибка настройки: укажите идентификатор и ключ'
        return 'Настроена. Внешние операции заблокированы политикой демонстрационной версии'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['__str__','status','total','delivery','created_at']; list_filter = ['status','delivery']; search_fields = ['id']
    readonly_fields = [f.name for f in Order._meta.fields]
    def has_add_permission(self, request): return False

@admin.register(IntegrationLog)
class LogAdmin(admin.ModelAdmin):
    list_display = ['provider','operation','result','created_at']; list_filter = ['provider']
    readonly_fields = ['provider','operation','result','created_at']
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
