import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Создать локального администратора со случайным паролем вне Git'
    def handle(self,*args,**kwargs):
        if not settings.LOCAL_ENVIRONMENT: raise CommandError('Только для локальной среды.')
        path=settings.PRIVATE_DIR/'admin-access.txt'
        user_model=get_user_model()
        if user_model.objects.filter(username='admin').exists():
            self.stdout.write('Administrator already exists. Password unchanged.'); return
        password=secrets.token_urlsafe(20)
        user_model.objects.create_superuser(username='admin',email='',password=password)
        path.write_text('Local demo only\nURL: http://127.0.0.1:8000/admin/\nUsername: admin\nPassword: '+password+'\n',encoding='utf-8');path.chmod(0o600)
        self.stdout.write('Administrator created. Credentials: backend/.local/admin-access.txt')
