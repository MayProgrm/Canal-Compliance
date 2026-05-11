from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0013_customuser_area_customuser_assignment_position_and_more')]
    operations = [migrations.AddField(model_name='customuser', name='employment_end', field=models.DateField(blank=True, null=True, verbose_name='Fecha de egreso')), migrations.AddField(model_name='customuser', name='employment_start', field=models.DateField(blank=True, null=True, verbose_name='Fecha de ingreso'))]
