
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denuncias', '0023_usersessionaudit_investigationprocedure'),
    ]

    operations = [
        migrations.AddField(
            model_name='investigationprocedure',
            name='extra_steps',
            field=models.JSONField(blank=True, default=list, verbose_name='Pasos específicos por tipo de incidente'),
        ),
        migrations.AddField(
            model_name='investigationprocedure',
            name='protocol_family',
            field=models.CharField(blank=True, default='', max_length=40, verbose_name='Familia de incidente (protocolo aplicado)'),
        ),
    ]
