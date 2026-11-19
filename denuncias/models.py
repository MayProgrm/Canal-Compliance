from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import string
import secrets
import os
import uuid

def attachment_upload_to(instance, filename):
    try:
        ext = os.path.splitext(filename)[1].lower()
    except Exception:
        ext = ''
    return f'attachments/{uuid.uuid4().hex}{ext}'

def evidence_preview_upload_to(instance, filename):
    return f'evidence_previews/{uuid.uuid4().hex}.pdf'

def resource_upload_to(instance, filename):
    try:
        ext = os.path.splitext(filename)[1].lower()
    except Exception:
        ext = ''
    return f'resources/{uuid.uuid4().hex}{ext}'

def privacy_notice_upload_to(instance, filename):
    try:
        ext = os.path.splitext(filename)[1].lower()
    except Exception:
        ext = ''
    company = (getattr(instance, 'company', '') or '').strip().lower() or 'empresa'
    return f'privacy_notices/{company}/{uuid.uuid4().hex}{ext}'

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expires = models.DateTimeField(blank=True, null=True)
    company = models.CharField(max_length=120, blank=True, null=True, verbose_name='Empresa')
    role = models.CharField(max_length=120, blank=True, null=True, verbose_name='Rol')
    area = models.CharField(max_length=120, blank=True, null=True, verbose_name='Área')
    branch = models.CharField(max_length=120, blank=True, null=True, verbose_name='Sucursal')
    matricula = models.CharField(max_length=30, blank=True, null=True, verbose_name='Matrícula', db_index=True)
    assignment_position = models.PositiveIntegerField(default=0, verbose_name='Posición de asignación', db_index=True)
    employment_start = models.DateField(blank=True, null=True, verbose_name='Fecha de ingreso')
    employment_end = models.DateField(blank=True, null=True, verbose_name='Fecha de egreso')
    require_data_update = models.BooleanField(default=False, verbose_name='Requiere actualización de datos')

    def generate_verification_code(self):
        self.verification_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.verification_code_expires = timezone.now() + timezone.timedelta(minutes=10)
        self.save()
        return self.verification_code

class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('Fraude y corrupción', 'Fraude y corrupción'),
        ('Soborno', 'Soborno'),
        ('Malversación o robo', 'Malversación o robo'),
        ('Blanqueo de capitales', 'Blanqueo de capitales'),
        ('Acoso laboral (mobbing)', 'Acoso laboral (mobbing)'),
        ('Acoso laboral', 'Acoso laboral'),
        ('Acoso sexual', 'Acoso sexual'),
        ('Discriminación', 'Discriminación'),
        ('Hostigamiento laboral', 'Hostigamiento laboral'),
        ('Hostigamiento sexual', 'Hostigamiento sexual'),
        ('Conflictos de interés', 'Conflictos de interés'),
        ('Violación de la política interna (Código de Ética)', 'Violación de la política interna (Código de Ética)'),
        ('Violación del Código de Ética', 'Violación del Código de Ética'),
        ('Incumplimiento de la normativa de Protección de Datos', 'Incumplimiento de la normativa de Protección de Datos'),
        ('Incumplimiento de la Política de Protección de Datos Personales', 'Incumplimiento de la Política de Protección de Datos Personales'),
        ('Violación de la seguridad de la información', 'Violación de la Seguridad de la Información'),
        ('Infracciones de derecho de la competencia', 'Infracciones de Derecho de la Competencia'),
        ('Incumplimientos graves de seguridad y salud laboral', 'Incumplimientos graves de Seguridad y Salud Laboral'),
        ('Incumplimientos de Seguridad y Salud laboral', 'Incumplimientos de Seguridad y Salud Laboral'),
        ('Uso indebido de activos/recursos de la empresa', 'Uso indebido de activos/recursos de la empresa'),
        ('Prácticas laborales ilegales', 'Prácticas laborales ilegales'),
        ('Prácticas laborales ilegales (Inquietud del Sistema de Gestión de Cumplimiento)', 'Prácticas laborales ilegales (Inquietud del Sistema de Gestión de Cumplimiento)'),
        ('Incumplimiento a la Política del Sistema de Gestión de Cumplimiento', 'Incumplimiento a la Política del Sistema de Gestión de Cumplimiento'),
        ('Incumplimiento a los procedimientos de alguna Ley o del Sistema de Gestión de Cumplimiento', 'Incumplimiento a los procedimientos de alguna Ley o del Sistema de Gestión de Cumplimiento'),
        ('Incumplimiento a la Política de Prevención de Lavado de Dinero', 'Incumplimiento a la Política de Prevención de Lavado de Dinero'),
        ('Extorsión', 'Extorsión'),
        ('Malversación o Robo', 'Malversación o Robo'),
        ('Deficiencias en servicios', 'Deficiencias en servicios'),
        ('Procesos administrativos', 'Procesos administrativos'),
        ('Condiciones laborales', 'Condiciones laborales'),
        ('Ambiente de trabajo', 'Ambiente de trabajo'),
        ('Interpretación normativa', 'Interpretación normativa'),
        ('Situaciones ambiguas', 'Situaciones ambiguas')
    ]
    ACTION_TYPE_CHOICES = [('denuncia', 'Denuncia'), ('queja', 'Queja'), ('inquietud', 'Inquietud'), ('consulta', 'Consulta')]
    SEVERITY_CHOICES = [('muy_grave', 'Muy grave'), ('grave', 'Grave'), ('media', 'Media'), ('leve', 'Leve')]
    STATUS_CHOICES = [('enviado', 'Enviado'), ('admitido', 'Admitido a trámite'), ('investigacion', 'En investigación'), ('info_adicional', 'Información adicional'), ('resolucion', 'Resolución'), ('resuelto', 'Resuelto'), ('rechazado', 'Rechazado'), ('archivado', 'Archivado'), ('transferido', 'Transferido')]
    folio = models.CharField(max_length=20, unique=True, editable=False)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES, default='denuncia', verbose_name='Tipo de acción', db_index=True)

    password = models.CharField(max_length=128, blank=True, null=True, verbose_name='Contraseña de consulta')
    privacy_policies_opened = models.CharField(max_length=255, blank=True, null=True, verbose_name='Avisos de privacidad abiertos')
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nombre')
    email = models.EmailField(blank=True, null=True, verbose_name='Correo electrónico')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Teléfono')
    reporter_matricula = models.CharField(max_length=11, blank=True, null=True, verbose_name='Número de empleado del denunciante', db_index=True)
    category = models.CharField(max_length=120, choices=CATEGORY_CHOICES, blank=True, null=True, verbose_name='Tipo de denuncia', db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='media', verbose_name='Gravedad', db_index=True)
    description = models.TextField(verbose_name='Descripción de la denuncia')
    attachment = models.FileField(upload_to=attachment_upload_to, blank=True, null=True, verbose_name='Archivo adjunto')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enviado', verbose_name='Estado', db_index=True)
    response = models.TextField(blank=True, null=True, verbose_name='Respuesta del administrador')
    lookup_count = models.IntegerField(default=0, verbose_name='Consultas del estado')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Asignado a')
    reporter_notes_summary = models.TextField(blank=True, null=True, verbose_name='Notas del denunciante (resumen)')
    relationship = models.CharField(max_length=30, blank=True, null=True, verbose_name='Relación con la empresa')
    incident_state = models.CharField(max_length=60, blank=True, null=True, verbose_name='Estado de la incidencia')
    incident_branch = models.CharField(max_length=120, blank=True, null=True, verbose_name='Sucursal')
    incident_date = models.DateField(blank=True, null=True, verbose_name='Fecha del hecho')
    incident_time = models.TimeField(blank=True, null=True, verbose_name='Hora del hecho')
    knows_actor = models.BooleanField(blank=True, null=True, verbose_name='¿Conoce al denunciado?')
    reporter_role = models.CharField(max_length=20, blank=True, null=True, verbose_name='Participación del denunciante')
    has_witnesses = models.BooleanField(blank=True, null=True, verbose_name='¿Hay testigos?')
    witnesses_count = models.IntegerField(blank=True, null=True, verbose_name='Cantidad de testigos')
    witnesses_names = models.TextField(blank=True, null=True, verbose_name='Nombres de testigos')
    actor_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nombre del denunciado')
    actor_matricula = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número de empleado del denunciado')
    actor_area = models.CharField(max_length=100, blank=True, null=True, verbose_name='Área del denunciado')

    class Meta:
        verbose_name = 'Denuncia'
        verbose_name_plural = 'Denuncias'
        ordering = ['-created_at']

    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if not self.folio:
            self.folio = self.generate_folio()
        if not self.severity:
            self.severity = self.compute_severity()
        elif self.severity == 'media':
            self.severity = self.compute_severity()
        super().save(*args, **kwargs)

    def generate_folio(self):
        while True:
            alphabet = string.ascii_uppercase + string.digits
            folio = 'GSI-' + ''.join(secrets.choice(alphabet) for _ in range(6))
            if not Complaint.objects.filter(folio=folio).exists():
                return folio

    def __str__(self):
        return f'{self.folio} - {self.get_status_display()}'

    def compute_severity(self):
        cat = (self.category or '').strip()
        muy_grave = {'Acoso sexual', 'Blanqueo de capitales', 'Incumplimientos graves de seguridad y salud laboral'}
        grave = {'Fraude y corrupción', 'Malversación o robo', 'Malversación o Robo', 'Violación de la seguridad de la información', 'Incumplimiento de la normativa de Protección de Datos'}
        media = {'Acoso laboral (mobbing)', 'Discriminación', 'Conflictos de interés', 'Violación de la política interna (Código de Ética)', 'Infracciones de derecho de la competencia', 'Uso indebido de activos/recursos de la empresa', 'Prácticas laborales ilegales', 'Extorsión'}
        if cat in muy_grave:
            return 'muy_grave'
        if cat in grave:
            return 'grave'
        if cat in media:
            return 'media'
        return 'media'

class InvestigationPlan(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='investigation_plan')
    objective = models.TextField(blank=True, null=True, verbose_name='Objetivo')
    scope = models.TextField(blank=True, null=True, verbose_name='Alcance')
    activities = models.TextField(blank=True, null=True, verbose_name='Actividades previstas')
    key_dates = models.TextField(blank=True, null=True, verbose_name='Fechas clave')
    deadline = models.DateField(blank=True, null=True, verbose_name='Plazo (fecha límite)')
    responsible = models.CharField(max_length=150, blank=True, null=True, verbose_name='Responsable')

    class Meta:
        verbose_name = 'Plan de investigación'
        verbose_name_plural = 'Planes de investigación'

class EvidenceItem(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='evidence_items')
    kind = models.CharField(max_length=60, verbose_name='Tipo de evidencia')
    description = models.TextField(verbose_name='Descripción')
    obtained_at = models.DateField(blank=True, null=True, verbose_name='Fecha de obtención')
    obtained_by = models.CharField(max_length=120, blank=True, null=True, verbose_name='Obtenida/cargada por')
    related_fact = models.TextField(blank=True, null=True, verbose_name='Relación con hecho específico')
    file = models.FileField(upload_to=attachment_upload_to, blank=True, null=True, verbose_name='Archivo')
    preview_pdf = models.FileField(upload_to=evidence_preview_upload_to, blank=True, null=True, verbose_name='Vista previa PDF')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering = ['-created_at']

class Finding(models.Model):
    CONFIRMATION_CHOICES = [('confirmado', 'Confirmado'), ('no_confirmado', 'No confirmado'), ('no_concluyente', 'No concluyente')]
    RISK_CHOICES = [('alto', 'Alto'), ('medio', 'Medio'), ('bajo', 'Bajo')]
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='findings')
    code = models.CharField(max_length=20, verbose_name='Código')
    description = models.TextField(verbose_name='Descripción del hallazgo')
    evidence_refs = models.CharField(max_length=200, blank=True, null=True, verbose_name='Evidencias que lo respaldan')
    confirmation = models.CharField(max_length=20, choices=CONFIRMATION_CHOICES, verbose_name='Grado de confirmación')
    risk = models.CharField(max_length=20, choices=RISK_CHOICES, verbose_name='Riesgo asociado')
    policy_ref = models.TextField(blank=True, null=True, verbose_name='Referencia de política/ley/procedimiento')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hallazgo'
        verbose_name_plural = 'Hallazgos'
        ordering = ['-created_at']

class CaseReport(models.Model):
    CONCLUSION_CHOICES = [('fundada', 'Fundada'), ('parcialmente_fundada', 'Parcialmente fundada'), ('no_fundada', 'No fundada'), ('no_concluyente', 'No concluyente')]
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='case_report')
    case_summary = models.TextField(blank=True, null=True, verbose_name='Resumen del caso')
    case_id = models.CharField(max_length=40, blank=True, null=True, verbose_name='ID del caso')
    start_date = models.DateField(blank=True, null=True, verbose_name='Fecha de inicio')
    end_date = models.DateField(blank=True, null=True, verbose_name='Fecha de fin')
    complaint_type = models.CharField(max_length=120, blank=True, null=True, verbose_name='Tipo de denuncia')
    investigated_facts = models.TextField(blank=True, null=True, verbose_name='Hechos investigados')
    methodology = models.TextField(blank=True, null=True, verbose_name='Metodología')
    main_findings = models.TextField(blank=True, null=True, verbose_name='Hallazgos principales')
    conclusion = models.CharField(max_length=30, choices=CONCLUSION_CHOICES, blank=True, null=True, verbose_name='Conclusión')
    recommendations = models.TextField(blank=True, null=True, verbose_name='Recomendaciones')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Informe del caso'
        verbose_name_plural = 'Informes del caso'

class InvestigationProcedure(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='investigation_procedure')
    step_recepcion = models.BooleanField(default=False, verbose_name='Recepción y registro del reporte')
    step_admisibilidad = models.BooleanField(default=False, verbose_name='Evaluación de admisibilidad y triaje')
    step_designacion = models.BooleanField(default=False, verbose_name='Designación del responsable/equipo investigador')
    step_independencia = models.BooleanField(default=False, verbose_name='Verificación de independencia y ausencia de conflicto de interés')
    step_plan = models.BooleanField(default=False, verbose_name='Plan de investigación documentado (objetivo, alcance, metodología)')
    step_evidencias = models.BooleanField(default=False, verbose_name='Recolección y preservación de evidencia')
    step_analisis = models.BooleanField(default=False, verbose_name='Análisis de evidencia y determinación de hallazgos')
    step_causa_raiz = models.BooleanField(default=False, verbose_name='Análisis de causa raíz')
    step_conclusion = models.BooleanField(default=False, verbose_name='Determinación de la conclusión (fundada / no fundada)')
    step_acciones = models.BooleanField(default=False, verbose_name='Acciones correctivas/disciplinarias y medidas de no represalia')
    step_seguimiento = models.BooleanField(default=False, verbose_name='Seguimiento y verificación de eficacia')
    step_cierre = models.BooleanField(default=False, verbose_name='Cierre y conservación de la información documentada')
    compliance_owner = models.CharField(max_length=150, blank=True, null=True, verbose_name='Responsable de cumplimiento')
    notes = models.TextField(blank=True, null=True, verbose_name='Observaciones del procedimiento')
    protocol_family = models.CharField(max_length=40, blank=True, default='', verbose_name='Familia de incidente (protocolo aplicado)')
    extra_steps = models.JSONField(default=list, blank=True, verbose_name='Pasos específicos por tipo de incidente')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Procedimiento de investigación (ISO 37301)'
        verbose_name_plural = 'Procedimientos de investigación (ISO 37301)'

    STEP_FIELDS = [
        'step_recepcion', 'step_admisibilidad', 'step_designacion', 'step_independencia',
        'step_plan', 'step_evidencias', 'step_analisis', 'step_causa_raiz',
        'step_conclusion', 'step_acciones', 'step_seguimiento', 'step_cierre',
    ]

    @property
    def extra_completed_count(self):
        return sum(1 for step in (self.extra_steps or []) if step.get('done'))

    @property
    def completed_count(self):
        base = sum(1 for f in self.STEP_FIELDS if getattr(self, f))
        return base + self.extra_completed_count

    @property
    def total_steps(self):
        return len(self.STEP_FIELDS) + len(self.extra_steps or [])

    @property
    def progress_percent(self):
        total = self.total_steps
        return int(round((self.completed_count / total) * 100)) if total else 0

    def __str__(self):
        return f'{self.complaint.folio} - ISO 37301 ({self.completed_count}/{self.total_steps})'

class ComplaintLog(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100, verbose_name='Acción')
    details = models.TextField(blank=True, null=True, verbose_name='Detalles')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')

    class Meta:
        verbose_name = 'Registro de cambio'
        verbose_name_plural = 'Registros de cambios'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.complaint.folio} - {self.action} - {self.timestamp}'

class ChatMessage(models.Model):
    SENDER_CHOICES = [('reporter', 'Denunciante'), ('admin', 'Administrador')]
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensaje de chat'
        verbose_name_plural = 'Mensajes de chat'

    def __str__(self):
        return f'{self.complaint.folio} [{self.sender}] {self.created_at:%Y-%m-%d %H:%M}'

class ReporterNote(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='reporter_notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Nota del denunciante'
        verbose_name_plural = 'Notas del denunciante'

    def __str__(self):
        return f'{self.complaint.folio} nota {self.created_at:%Y-%m-%d %H:%M}'

class ComplaintAttachment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=attachment_upload_to, verbose_name='Archivo adjunto')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Adjunto de denuncia'
        verbose_name_plural = 'Adjuntos de denuncia'
        ordering = ['uploaded_at']

    def __str__(self):
        try:
            return f'{self.complaint.folio} -> {self.file.name}'
        except Exception:
            return self.file.name

class PageViewStat(models.Model):
    route_name = models.CharField(max_length=100, unique=True)
    count = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Métrica de página'
        verbose_name_plural = 'Métricas de páginas'
        ordering = ['route_name']

    def __str__(self):
        return f'{self.route_name} -> {self.count}'

class PageViewLog(models.Model):
    route_name = models.CharField(max_length=100)
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Registro de vista de página'
        verbose_name_plural = 'Registros de vistas de páginas'
        ordering = ['-viewed_at']

    def __str__(self):
        return f'{self.route_name} @ {self.viewed_at:%Y-%m-%d %H:%M}'

class UserSessionAudit(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='session_audits')
    login_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Inicio de sesión')
    logout_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='Fin de sesión')
    session_key = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='Dirección IP')
    user_agent = models.CharField(max_length=255, blank=True, null=True, verbose_name='Navegador')

    class Meta:
        verbose_name = 'Registro de sesión'
        verbose_name_plural = 'Registros de sesiones'
        ordering = ['-login_at']

    @property
    def duration_seconds(self):
        if self.logout_at and self.login_at:
            delta = (self.logout_at - self.login_at).total_seconds()
            return int(delta) if delta > 0 else 0
        return 0

    @property
    def is_active(self):
        return self.logout_at is None

    def __str__(self):
        return f'{self.user} · {self.login_at:%Y-%m-%d %H:%M}'

class ResourceItem(models.Model):
    KIND_CHOICES = [
        ('main_doc', 'Documento principal'),
        ('infographic', 'Infografía'),
        ('update', 'Actualización reciente'),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES, db_index=True, verbose_name='Tipo')
    title = models.CharField(max_length=160, verbose_name='Título')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    file = models.FileField(upload_to=resource_upload_to, blank=True, null=True, verbose_name='Archivo')
    published_on = models.DateField(blank=True, null=True, verbose_name='Fecha')
    sort_order = models.PositiveIntegerField(default=0, db_index=True, verbose_name='Orden')
    is_published = models.BooleanField(default=True, db_index=True, verbose_name='Publicado')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'
        ordering = ['kind', 'sort_order', '-published_on', '-updated_at']

    def __str__(self):
        return f'{self.get_kind_display()}: {self.title}'

class PrivacyNotice(models.Model):
    COMPANY_CHOICES = [
        ('COMETRA', 'COMETRA'),
        ('SEPSA', 'SEPSA'),
        ('SEGURITEC', 'SEGURITEC'),
        ('TECNOVAL', 'TECNOVAL'),
        ('TAMEME', 'TAMEME'),
        ('GRUMER', 'GRUMER'),
    ]

    company = models.CharField(max_length=40, choices=COMPANY_CHOICES, unique=True, verbose_name='Empresa')
    file = models.FileField(upload_to=privacy_notice_upload_to, blank=True, null=True, verbose_name='PDF')
    is_published = models.BooleanField(default=True, db_index=True, verbose_name='Publicado')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aviso de privacidad'
        verbose_name_plural = 'Avisos de privacidad'
        ordering = ['company']

    def __str__(self):
        return f'Aviso de privacidad {self.company}'
