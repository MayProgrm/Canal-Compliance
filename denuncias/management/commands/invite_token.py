from django.core.management.base import BaseCommand
from django.conf import settings
from denuncias.utils import totp
import time

class Command(BaseCommand):
    help = 'Muestra el token de invitación dinámico (TOTP) para registro de administradores.'

    def add_arguments(self, parser):
        parser.add_argument('--digits', type=int, default=8, help='Número de dígitos del token')
        parser.add_argument('--timestep', type=int, default=60, help='Duración del paso en segundos')

    def handle(self, *args, **options):
        secret = getattr(settings, 'ADMIN_INVITE_SECRET', None)
        if not secret:
            self.stderr.write(self.style.ERROR('ADMIN_INVITE_SECRET no está configurado; usando ADMIN_INVITE_CODE estático.'))
            code = getattr(settings, 'ADMIN_INVITE_CODE', None)
            if code:
                self.stdout.write(self.style.WARNING(f'Código estático actual: {code}'))
            else:
                self.stderr.write(self.style.ERROR('No hay configuración de invitación disponible.'))
            return
        digits = options['digits']
        timestep = options['timestep']
        now = int(time.time())
        current = totp(secret, timestep=timestep, digits=digits, for_time=now)
        next_token = totp(secret, timestep=timestep, digits=digits, for_time=now + timestep)
        prev_token = totp(secret, timestep=timestep, digits=digits, for_time=now - timestep)
        self.stdout.write(self.style.SUCCESS(f'Token actual: {current}'))
        self.stdout.write(f'Anterior (tolerado): {prev_token}')
        self.stdout.write(f'Siguiente (tolerado): {next_token}')
        self.stdout.write(f'Válido durante el intervalo de {timestep} segundos.')
