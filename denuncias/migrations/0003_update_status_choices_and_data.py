from django.db import migrations

def map_old_statuses(apps, schema_editor):
    Complaint = apps.get_model('denuncias', 'Complaint')
    mapping = {'pendiente': 'enviado', 'en_revision': 'admitido', 'en_consulta': 'investigacion', 'en_resolucion': 'resolucion', 'concluido': 'archivado', 'resuelto': 'resuelto', 'archivado': 'archivado'}
    for old, new in mapping.items():
        Complaint.objects.filter(status=old).update(status=new)

class Migration(migrations.Migration):
    dependencies = [('denuncias', '0002_pageviewstat_complaint_lookup_count_and_more')]
    operations = [migrations.RunPython(map_old_statuses, migrations.RunPython.noop)]
