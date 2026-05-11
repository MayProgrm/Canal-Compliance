import denuncias.models
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0008_pageviewlog')]
    operations = [migrations.AddField(model_name='complaint', name='relationship', field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Relación con la empresa')), migrations.AlterField(model_name='complaint', name='attachment', field=models.FileField(blank=True, null=True, upload_to=denuncias.models.attachment_upload_to, verbose_name='Archivo adjunto')), migrations.AlterField(model_name='complaintattachment', name='file', field=models.FileField(upload_to=denuncias.models.attachment_upload_to, verbose_name='Archivo adjunto'))]
