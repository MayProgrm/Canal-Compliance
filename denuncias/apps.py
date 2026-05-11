from django.apps import AppConfig

class DenunciasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'denuncias'

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group, Permission
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        from django.conf import settings
        import os

        @receiver(post_migrate, dispatch_uid='denuncias_bootstrap_actualizador')
        def _bootstrap_actualizador(sender, **kwargs):
            try:
                from .models import ResourceItem, PrivacyNotice
            except Exception:
                return

            group, _ = Group.objects.get_or_create(name='Actualizador')

            model_labels = [
                ('denuncias', ResourceItem._meta.model_name),
                ('denuncias', PrivacyNotice._meta.model_name),
            ]
            desired = set()
            for app_label, model_name in model_labels:
                for action in ('add', 'change', 'delete', 'view'):
                    desired.add(f'{action}_{model_name}')

            perms = list(Permission.objects.filter(content_type__app_label='denuncias', codename__in=list(desired)))
            if perms:
                group.permissions.set(perms)

            User = get_user_model()
            username = os.environ.get('ACTUALIZADOR_USERNAME', 'Actua').strip() or 'Actua'
            pwd = (os.environ.get('ACTUALIZADOR_PASSWORD') or '').strip()
            bootstrap_flag = (os.environ.get('ACTUALIZADOR_BOOTSTRAP') or '').strip().lower()
            bootstrap_enabled = bool(getattr(settings, 'DEBUG', False)) or bootstrap_flag in {'1', 'true', 'yes', 'on'}

            if not bootstrap_enabled and not User.objects.filter(username=username).exists():
                return

            defaults = {
                'is_staff': True,
                'is_active': True,
            }
            if hasattr(User, 'role'):
                defaults['role'] = 'Actualizador'
            if hasattr(User, 'is_verified'):
                defaults['is_verified'] = True

            user, created = User.objects.get_or_create(username=username, defaults=defaults)
            if created:
                if pwd:
                    user.set_password(pwd)
                else:
                    user.set_unusable_password()
                user.save()
            user.groups.add(group)
