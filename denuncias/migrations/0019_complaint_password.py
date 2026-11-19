
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denuncias', '0018_remove_complaint_actor_matricula_enc_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='password',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Contraseña de consulta'),
        ),
    ]
