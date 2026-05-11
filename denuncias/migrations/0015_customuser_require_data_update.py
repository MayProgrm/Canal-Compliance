from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0014_customuser_employment_end_and_more')]
    operations = [migrations.AddField(model_name='customuser', name='require_data_update', field=models.BooleanField(default=False, verbose_name='Requiere actualización de datos'))]
