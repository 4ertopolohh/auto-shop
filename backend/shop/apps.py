from django.apps import AppConfig
from django.db.backends.signals import connection_created

def register_unicode_search(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        # SQLite's built-in LOWER/NOCASE only fold ASCII characters.
        connection.connection.create_function('CASEFOLD', 1, lambda text: (text or '').casefold(), deterministic=True)

class ShopConfig(AppConfig):
    name = 'shop'
    verbose_name = 'Магазин «Крутящий момент»'
    def ready(self):
        connection_created.connect(register_unicode_search, dispatch_uid='shop_unicode_search')
