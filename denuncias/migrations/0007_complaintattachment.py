import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0006_complaint_reporter_notes_summary_chatmessage_and_more')]
    operations = [migrations.CreateModel(name='ComplaintAttachment', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('file', models.FileField(upload_to='attachments/', verbose_name='Archivo adjunto')), ('uploaded_at', models.DateTimeField(auto_now_add=True)), ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='denuncias.complaint'))], options={'verbose_name': 'Adjunto de denuncia', 'verbose_name_plural': 'Adjuntos de denuncia', 'ordering': ['uploaded_at']})]
