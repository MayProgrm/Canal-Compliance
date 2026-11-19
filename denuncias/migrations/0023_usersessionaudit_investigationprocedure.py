
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('denuncias', '0022_resourceitem_privacynotice'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSessionAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('login_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Inicio de sesión')),
                ('logout_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Fin de sesión')),
                ('session_key', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Dirección IP')),
                ('user_agent', models.CharField(blank=True, max_length=255, null=True, verbose_name='Navegador')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_audits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Registro de sesión',
                'verbose_name_plural': 'Registros de sesiones',
                'ordering': ['-login_at'],
            },
        ),
        migrations.CreateModel(
            name='InvestigationProcedure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step_recepcion', models.BooleanField(default=False, verbose_name='Recepción y registro del reporte')),
                ('step_admisibilidad', models.BooleanField(default=False, verbose_name='Evaluación de admisibilidad y triaje')),
                ('step_designacion', models.BooleanField(default=False, verbose_name='Designación del responsable/equipo investigador')),
                ('step_independencia', models.BooleanField(default=False, verbose_name='Verificación de independencia y ausencia de conflicto de interés')),
                ('step_plan', models.BooleanField(default=False, verbose_name='Plan de investigación documentado (objetivo, alcance, metodología)')),
                ('step_evidencias', models.BooleanField(default=False, verbose_name='Recolección y preservación de evidencia')),
                ('step_analisis', models.BooleanField(default=False, verbose_name='Análisis de evidencia y determinación de hallazgos')),
                ('step_causa_raiz', models.BooleanField(default=False, verbose_name='Análisis de causa raíz')),
                ('step_conclusion', models.BooleanField(default=False, verbose_name='Determinación de la conclusión (fundada / no fundada)')),
                ('step_acciones', models.BooleanField(default=False, verbose_name='Acciones correctivas/disciplinarias y medidas de no represalia')),
                ('step_seguimiento', models.BooleanField(default=False, verbose_name='Seguimiento y verificación de eficacia')),
                ('step_cierre', models.BooleanField(default=False, verbose_name='Cierre y conservación de la información documentada')),
                ('compliance_owner', models.CharField(blank=True, max_length=150, null=True, verbose_name='Responsable de cumplimiento')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Observaciones del procedimiento')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('complaint', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='investigation_procedure', to='denuncias.complaint')),
            ],
            options={
                'verbose_name': 'Procedimiento de investigación (ISO 37301)',
                'verbose_name_plural': 'Procedimientos de investigación (ISO 37301)',
            },
        ),
    ]
