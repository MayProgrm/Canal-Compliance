from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0010_complaint_actor_area_complaint_actor_matricula_and_more')]
    operations = [migrations.AddField(model_name='complaint', name='reporter_matricula', field=models.CharField(blank=True, db_index=True, max_length=10, null=True, verbose_name='Número de empleado'))]
