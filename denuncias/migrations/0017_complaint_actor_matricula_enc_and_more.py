
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denuncias', '0016_alter_complaint_reporter_matricula_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='actor_matricula_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='complaint',
            name='actor_name_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='complaint',
            name='email_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='complaint',
            name='phone_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='complaint',
            name='reporter_matricula_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='complaint',
            name='reporter_notes_summary_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='complaint',
            name='witnesses_names_enc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='actor_matricula',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Número de empleado del denunciado'),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='reporter_matricula',
            field=models.CharField(blank=True, db_index=True, max_length=11, null=True, verbose_name='Número de empleado del denunciante'),
        ),
    ]
