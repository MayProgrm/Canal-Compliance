
import denuncias.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('denuncias', '0021_complaint_privacy_policies_opened_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivacyNotice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(choices=[('COMETRA', 'COMETRA'), ('SEPSA', 'SEPSA'), ('SEGURITEC', 'SEGURITEC'), ('TECNOVAL', 'TECNOVAL'), ('TAMEME', 'TAMEME'), ('GRUMER', 'GRUMER')], max_length=40, unique=True, verbose_name='Empresa')),
                ('file', models.FileField(blank=True, null=True, upload_to=denuncias.models.privacy_notice_upload_to, verbose_name='PDF')),
                ('is_published', models.BooleanField(db_index=True, default=True, verbose_name='Publicado')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Aviso de privacidad',
                'verbose_name_plural': 'Avisos de privacidad',
                'ordering': ['company'],
            },
        ),
        migrations.CreateModel(
            name='ResourceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('main_doc', 'Documento principal'), ('infographic', 'Infografía'), ('update', 'Actualización reciente')], db_index=True, max_length=20, verbose_name='Tipo')),
                ('title', models.CharField(max_length=160, verbose_name='Título')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('file', models.FileField(blank=True, null=True, upload_to=denuncias.models.resource_upload_to, verbose_name='Archivo')),
                ('published_on', models.DateField(blank=True, null=True, verbose_name='Fecha')),
                ('sort_order', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Orden')),
                ('is_published', models.BooleanField(db_index=True, default=True, verbose_name='Publicado')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Recurso',
                'verbose_name_plural': 'Recursos',
                'ordering': ['kind', 'sort_order', '-published_on', '-updated_at'],
            },
        ),
    ]

