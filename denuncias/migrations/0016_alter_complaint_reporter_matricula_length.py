from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0015_customuser_require_data_update')]
    operations = [migrations.AlterField(model_name='complaint', name='reporter_matricula', field=models.CharField(max_length=11, blank=True, null=True, db_index=True, verbose_name='Matrícula del denunciante'))]
