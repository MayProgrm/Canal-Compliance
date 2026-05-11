from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0010_complaint_actor_area_complaint_actor_matricula_and_more')]
    operations = [migrations.AddField(model_name='complaint', name='witnesses_count', field=models.IntegerField(blank=True, null=True, verbose_name='Cantidad de testigos')), migrations.AddField(model_name='complaint', name='witnesses_names', field=models.TextField(blank=True, null=True, verbose_name='Nombres de testigos'))]
