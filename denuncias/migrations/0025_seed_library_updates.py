from datetime import date

from django.db import migrations


LEGACY_TITLE = 'Nueva interfaz de usuario'
CREATION_TITLE = 'Creación del canal de denuncias'
CREATION_DESC = (
    'Se puso en marcha el Canal de Denuncias en línea como un medio confidencial '
    'y transparente para reportar posibles faltas al Código de Ética. Desde su '
    'creación, cualquier persona puede registrar su reporte y darle seguimiento '
    'desde el sitio web.'
)

UPDATES = [
    (
        'Aplicación móvil para enviar reportes',
        date(2025, 10, 20),
        'Se habilitó la aplicación móvil del canal, que permite enviar y consultar '
        'reportes de denuncia directamente desde el teléfono, con el mismo '
        'seguimiento y la misma confidencialidad que el sitio web.',
    ),
    (
        'Actualización del Código de Ética',
        date(2025, 11, 5),
        'Se publicó la versión actualizada del Código de Ética, que sirve de '
        'referencia para clasificar y atender los reportes recibidos en el canal.',
    ),
    (
        'Actualización de formatos y procedimientos',
        date(2025, 11, 12),
        'Se revisaron y actualizaron los formatos de recepción y los procedimientos '
        'internos de atención, con el fin de agilizar la gestión de los reportes.',
    ),
    (
        'Mejoras en la recepción y canalización de reportes',
        date(2025, 11, 18),
        'Se optimizó la recepción de los reportes y su canalización al área '
        'responsable, mejorando los tiempos de respuesta y la trazabilidad del '
        'expediente.',
    ),
]


def seed_updates(apps, schema_editor):
    ResourceItem = apps.get_model('denuncias', 'ResourceItem')

    legacy = ResourceItem.objects.filter(kind='update', title=LEGACY_TITLE).first()
    if legacy is not None:
        legacy.title = CREATION_TITLE
        legacy.description = CREATION_DESC
        legacy.is_published = True
        legacy.save(update_fields=['title', 'description', 'is_published'])
    else:
        ResourceItem.objects.get_or_create(
            kind='update',
            title=CREATION_TITLE,
            defaults={
                'description': CREATION_DESC,
                'published_on': date(2025, 10, 15),
                'is_published': True,
            },
        )

    for title, published_on, description in UPDATES:
        ResourceItem.objects.get_or_create(
            kind='update',
            title=title,
            defaults={
                'description': description,
                'published_on': published_on,
                'is_published': True,
            },
        )


def unseed_updates(apps, schema_editor):
    ResourceItem = apps.get_model('denuncias', 'ResourceItem')
    ResourceItem.objects.filter(
        kind='update', title__in=[title for title, _, _ in UPDATES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('denuncias', '0024_investigationprocedure_extra_steps_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_updates, unseed_updates),
    ]
