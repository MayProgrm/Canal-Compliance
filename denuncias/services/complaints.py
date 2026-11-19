import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.dateparse import parse_date, parse_time

from ..models import Complaint, ComplaintAttachment, ComplaintLog, ReporterNote

logger = logging.getLogger(__name__)


def get_delegador():
    User = get_user_model()
    user = User.objects.filter(username='Delegador', is_staff=True, is_active=True).first()
    if not user:
        user = User.objects.filter(role='Delegador', is_staff=True, is_active=True).first()
    return user


def notify_delegador_new_complaint(request, complaint):
    delegador = get_delegador()
    if not delegador or not (delegador.email or '').strip():
        return
    from django.core.mail import send_mail
    try:
        detail_url = request.build_absolute_uri(
            reverse('denuncias:admin_complaint_detail', kwargs={'complaint_id': complaint.id})
        )
    except Exception:
        detail_url = ''
    subject = f"Nuevo ticket para delegación · Folio {complaint.folio}"
    body_lines = [
        f"Folio: {complaint.folio}",
        f"Estado: {complaint.get_status_display()}",
        f"Categoría: {complaint.get_category_display() if complaint.category else '-'}",
        f"Gravedad: {complaint.get_severity_display()}",
        f"Área relacionada: {complaint.actor_area or '-'}",
        f"Avisos de privacidad abiertos: {getattr(complaint, 'privacy_policies_opened', '') or '-'}",
        f"Creada: {complaint.created_at:%Y-%m-%d %H:%M}",
        "",
        f"Revisar y delegar: {detail_url}",
    ]
    send_mail(
        subject,
        "\n".join(body_lines),
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost'),
        [delegador.email],
        fail_silently=True,
    )


def resolve_category(action_type, category=None, queja_category=None, inquietud_category=None):
    action = (action_type or '').strip()
    if action == 'queja':
        return queja_category
    if action == 'inquietud':
        return inquietud_category
    return category


def build_optional_summary(optional):
    optional = optional or {}
    pref_map = {'email': 'Correo', 'phone': 'Celular', 'whatsapp': 'Whatsapp', 'any': 'Cualquier medio'}
    parts = []
    if optional.get('recurrence'):
        parts.append(f"Repetición: {'Sí' if optional['recurrence'] == 'si' else 'No'}")
    if optional.get('recurrence_since'):
        parts.append(f"Desde: {optional['recurrence_since']}")
    if optional.get('immediate_risk'):
        parts.append(f"Riesgo inmediato: {'Sí' if optional['immediate_risk'] == 'si' else 'No'}")
    if optional.get('previous_report'):
        parts.append(f"Reportado antes: {'Sí' if optional['previous_report'] == 'si' else 'No'}")
    if optional.get('previous_report_channel'):
        parts.append(f"Canal previo: {optional['previous_report_channel']}")
    if optional.get('contact_preference'):
        parts.append(f"Preferencia de contacto: {pref_map.get(optional['contact_preference'], optional['contact_preference'])}")
    if optional.get('share_permission'):
        parts.append(f"Autoriza compartir con RRHH: {'Sí' if optional['share_permission'] == 'si' else 'No'}")
    if optional.get('impact_notes'):
        parts.append(f"Impacto: {optional['impact_notes']}")
    return '; '.join(parts)


def _as_bool(value):
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in ('si', 'sí', 'true'):
            return True
        if raw in ('no', 'false'):
            return False
    return None


def _as_date(value):
    if not value:
        return None
    if hasattr(value, 'year'):
        return value
    return parse_date(str(value))


def _as_time(value):
    if not value:
        return None
    if hasattr(value, 'hour'):
        return value
    return parse_time(str(value))


def persist_new_complaint(complaint, *, files=None, request=None, optional=None,
                          password=None, privacy_opened='', incident=None):
    if password:
        complaint.set_password(password)
    if privacy_opened:
        complaint.privacy_policies_opened = privacy_opened[:255]
    complaint.save()

    incident = incident or {}
    updates = []
    if incident.get('state'):
        complaint.incident_state = incident['state']
        updates.append('incident_state')
    if incident.get('branch'):
        complaint.incident_branch = incident['branch']
        updates.append('incident_branch')
    incident_date = _as_date(incident.get('date'))
    if incident_date:
        complaint.incident_date = incident_date
        updates.append('incident_date')
    incident_time = _as_time(incident.get('time'))
    if incident_time:
        complaint.incident_time = incident_time
        updates.append('incident_time')
    knows_actor = _as_bool(incident.get('knows_actor'))
    if knows_actor is not None:
        complaint.knows_actor = knows_actor
        updates.append('knows_actor')
    if incident.get('role'):
        complaint.reporter_role = incident['role']
        updates.append('reporter_role')
    has_witnesses = _as_bool(incident.get('has_witnesses'))
    if has_witnesses is not None:
        complaint.has_witnesses = has_witnesses
        updates.append('has_witnesses')
    if incident.get('actor_name'):
        complaint.actor_name = incident['actor_name']
        updates.append('actor_name')
    if incident.get('actor_matricula'):
        complaint.actor_matricula = incident['actor_matricula']
        updates.append('actor_matricula')
    if incident.get('actor_area'):
        complaint.actor_area = incident['actor_area']
        updates.append('actor_area')
    if updates:
        complaint.save(update_fields=updates)

    try:
        delegador = get_delegador()
        if delegador:
            complaint.assigned_to = delegador
            complaint.save(update_fields=['assigned_to'])
            try:
                ComplaintLog.objects.create(
                    complaint=complaint,
                    user=delegador,
                    action='delegation_pending',
                    details='Asignado al Delegador para revisión previa a la delegación',
                )
            except Exception:
                pass
    except Exception:
        logger.exception('Error asignando denuncia al Delegador')

    try:
        summary_text = build_optional_summary(optional)
        if summary_text:
            complaint.reporter_notes_summary = summary_text[:2000]
            complaint.save(update_fields=['reporter_notes_summary'])
            ReporterNote.objects.create(complaint=complaint, content=summary_text)
    except Exception:
        pass

    attachments = list(files or [])
    if attachments:
        attachments = attachments[:5]
        for idx, file in enumerate(attachments):
            if idx == 0 and (not complaint.attachment):
                complaint.attachment = file
            else:
                ComplaintAttachment.objects.create(complaint=complaint, file=file)
        complaint.save(update_fields=['attachment'])

    try:
        from .iso_protocol import apply_iso_protocol
        apply_iso_protocol(complaint)
    except Exception:
        logger.exception('Fallo al aplicar el protocolo ISO 37301 por tipo de incidente')

    try:
        notify_delegador_new_complaint(request, complaint)
    except Exception:
        logger.exception('Fallo al notificar por correo al Delegador')

    return complaint


def chat_enabled_for(complaint):
    return bool(complaint)


def mask_email(email):
    if not email:
        return None
    local, _, domain = email.partition('@')
    masked_local = local[:1] + '***' if local else ''
    return masked_local + ('@' + domain if domain else '')


def mask_phone(phone):
    if not phone:
        return None
    digits = ''.join(ch for ch in phone if ch.isdigit())
    return '*** *** **' + digits[-2:] if len(digits) >= 2 else '***'


def get_complaint_for_reporter(folio, password):
    folio = (folio or '').strip().upper()
    if not folio:
        return None, 'not_found'
    try:
        complaint = Complaint.objects.select_related('assigned_to').get(folio=folio)
    except Complaint.DoesNotExist:
        return None, 'not_found'
    if complaint.password:
        if not password:
            return None, 'password_required'
        if not complaint.check_password(password):
            return None, 'invalid_password'
    return complaint, None
