from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

class Command(BaseCommand):
    help = 'Crea o actualiza un administrador de prueba solo en modo DEBUG.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Este comando solo se permite cuando DEBUG=True.')
        password = config('TEST_ADMIN_PASSWORD', default='')
        if not password:
            raise CommandError('Define TEST_ADMIN_PASSWORD antes de ejecutar este comando.')

        User = get_user_model()
        username = 'Prueba'
        validate_password(password, user=User(username=username))
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        if hasattr(user, 'is_verified'):
            setattr(user, 'is_verified', True)
        user.set_password(password)
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS("Usuario de prueba creado: Prueba."))
        else:
            self.stdout.write(self.style.WARNING('Usuario de prueba ya existía; contraseña y flags actualizados.'))
