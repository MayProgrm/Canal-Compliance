from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea usuarios de demostración enumerados con contraseña igual al nombre de usuario.'

    def add_arguments(self, parser):
        parser.add_argument('--prefix', type=str, default='user', help='Prefijo del nombre de usuario (por defecto: user)')
        parser.add_argument('--start', type=int, default=1, help='Número inicial (por defecto: 1)')
        parser.add_argument('--end', type=int, default=9, help='Número final inclusive (por defecto: 9)')
        parser.add_argument('--staff', action='store_true', default=True, help='Marcar como staff (por defecto: True)')
        parser.add_argument('--no-staff', dest='staff', action='store_false', help='No marcar como staff')
        parser.add_argument('--superuser', action='store_true', default=False, help='Marcar como superusuario (por defecto: False)')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Este comando solo se permite cuando DEBUG=True.')
        User = get_user_model()
        prefix = options['prefix']
        start = options['start']
        end = options['end']
        is_staff = options['staff']
        is_superuser = options['superuser']
        created = 0
        skipped = 0
        for i in range(start, end + 1):
            username = f'{prefix}{i}'
            if User.objects.filter(username=username).exists():
                skipped += 1
                self.stdout.write(self.style.WARNING(f'Ya existe: {username}, se omite'))
                continue
            user = User(username=username, email=f'{username}@example.com', is_staff=is_staff, is_superuser=is_superuser, is_active=True)
            user.set_password(username)
            user.save()
            created += 1
            self.stdout.write(self.style.SUCCESS(f'Creado usuario: {username} (staff={is_staff}, superuser={is_superuser})'))
        self.stdout.write(self.style.SUCCESS(f'Usuarios creados: {created}, existentes omitidos: {skipped}'))
