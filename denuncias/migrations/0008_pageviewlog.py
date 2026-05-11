from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0007_complaintattachment')]
    operations = [migrations.CreateModel(name='PageViewLog', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('route_name', models.CharField(max_length=100)), ('viewed_at', models.DateTimeField(auto_now_add=True, db_index=True))], options={'verbose_name': 'Registro de vista de página', 'verbose_name_plural': 'Registros de vistas de páginas', 'ordering': ['-viewed_at']})]
