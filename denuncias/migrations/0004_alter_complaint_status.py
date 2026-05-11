from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0003_update_status_choices_and_data')]
    operations = [migrations.AlterField(model_name='complaint', name='status', field=models.CharField(choices=[('enviado', 'Enviado'), ('admitido', 'Admitido a trámite'), ('investigacion', 'En investigación'), ('info_adicional', 'Información adicional'), ('resolucion', 'Resolución'), ('resuelto', 'Resuelto'), ('archivado', 'Archivado'), ('transferido', 'Transferido')], db_index=True, default='enviado', max_length=20, verbose_name='Estado'))]
