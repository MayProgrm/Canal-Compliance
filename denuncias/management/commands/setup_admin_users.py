from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):

    def handle(self, *args, **options):
        User = get_user_model()
        su_username = 'Superusuario'
        su_password = 'Superusuario'
        su, su_created = User.objects.get_or_create(username=su_username, defaults={'email': 'super@example.local'})
        su.is_staff = True
        su.is_superuser = True
        if hasattr(su, 'is_verified'):
            su.is_verified = True
            if hasattr(su, 'verification_code'):
                su.verification_code = None
            if hasattr(su, 'verification_code_expires'):
                su.verification_code_expires = None
        su.set_password(su_password)
        su.save()
        if su_created:
            self.stdout.write(self.style.SUCCESS("Creado superusuario 'Superusuario' con contraseña 'Superusuario'."))
        else:
            self.stdout.write(self.style.WARNING("Actualizado superusuario 'Superusuario' (flags y contraseña)."))
        target_username = 'Delegador'
        target_password = 'Delegador'
        existing_delegador = User.objects.filter(username=target_username).first()
        existing_prueba = User.objects.filter(username='Prueba').first()
        if existing_delegador:
            u = existing_delegador
            action_msg = "Actualizado usuario existente 'Delegador'."
            if existing_prueba and existing_prueba.pk != existing_delegador.pk:
                existing_prueba.is_active = False
                existing_prueba.save(update_fields=['is_active'])
        elif existing_prueba:
            existing_prueba.username = target_username
            u = existing_prueba
            action_msg = "Renombrado usuario 'Prueba' a 'Delegador'."
        else:
            u = User(username=target_username, email='delegador@example.local')
            action_msg = "Creado usuario 'Delegador'."
        u.is_staff = True
        u.is_superuser = False
        if hasattr(u, 'is_verified'):
            u.is_verified = True
            if hasattr(u, 'verification_code'):
                u.verification_code = None
            if hasattr(u, 'verification_code_expires'):
                u.verification_code_expires = None
        u.set_password(target_password)
        u.save()
        if hasattr(u, 'role'):
            u.role = 'Delegador'
            u.save(update_fields=['role'])
        self.stdout.write(self.style.SUCCESS(f"{action_msg} Contraseña establecida como '{target_password}'."))
        self.stdout.write(self.style.SUCCESS('Usuarios configurados: Superusuario (superuser) y Delegador (staff).'))
