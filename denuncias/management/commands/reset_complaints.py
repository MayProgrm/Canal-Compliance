from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from denuncias.models import Complaint

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Confirmar la eliminación sin pedir confirmación interactiva')
        parser.add_argument('--dry-run', action='store_true', help='Mostrar lo que se eliminaría sin realizar cambios')
        parser.add_argument('--keep-files', action='store_true', help='No eliminar los archivos adjuntos del sistema de archivos')
        parser.add_argument('--force', action='store_true', help='Permitir ejecución cuando DEBUG=False (no recomendado)')

    def handle(self, *args, **options):
        if not settings.DEBUG and (not options['force']):
            raise CommandError('Este comando solo se permite en DEBUG. Usa --force bajo tu responsabilidad.')
        qs = Complaint.objects.all()
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING('No hay denuncias para eliminar.'))
            return
        self.stdout.write(self.style.NOTICE(f'Se eliminarán {count} denuncias y sus registros asociados.'))
        if options['dry_run']:
            for c in qs[:10]:
                self.stdout.write(f" - {c.folio} (adjunto: {('sí' if c.attachment else 'no')})")
            if count > 10:
                self.stdout.write(f' ... y {count - 10} más')
            self.stdout.write(self.style.SUCCESS('Dry-run completado. No se realizaron cambios.'))
            return
        if not options['yes']:
            raise CommandError('Falta confirmación. Ejecuta con --yes para proceder.')
        if not options['keep_files']:
            for complaint in qs.iterator():
                if complaint.attachment:
                    try:
                        complaint.attachment.delete(save=False)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'No se pudo eliminar archivo de {complaint.folio}: {e}'))
        deleted = qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Eliminación completa. Objetos eliminados: {deleted[0]} (incluye denuncias y logs).'))
