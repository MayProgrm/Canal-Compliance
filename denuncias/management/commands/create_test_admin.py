from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea o actualiza un usuario administrador de prueba (username: Prueba, password: prueba)'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'Prueba'
        password = 'prueba'
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        if hasattr(user, 'is_verified'):
            setattr(user, 'is_verified', True)
        user.set_password(password)
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS("Usuario de prueba creado: username='Prueba', password='prueba'"))
        else:
            self.stdout.write(self.style.WARNING('Usuario de prueba ya existía; contraseña y flags actualizados.'))
