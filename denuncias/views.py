from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse, Http404, HttpResponse, FileResponse
import mimetypes
import os
import calendar
from datetime import date, timedelta
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, F, Case, When, IntegerField, Count, Sum, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings
from django.utils.dateparse import parse_date, parse_time
import logging
from io import BytesIO
from .utils import validate_totp_token
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit
from .models import Complaint, PageViewStat, ChatMessage, ReporterNote, ComplaintAttachment, PageViewLog, ComplaintLog, PrivacyNotice, ResourceItem, InvestigationProcedure, UserSessionAudit
from .forms import ComplaintForm, ComplaintLookupForm, AdminRegistrationForm, AdminLoginForm, AdminSetUserPasswordForm, VerificationCodeForm, ComplaintResponseForm, ChatMessageForm, ReporterNoteForm, UserProfileForm, StyledPasswordChangeForm, InvestigationPlanForm, EvidenceItemForm, FindingForm, CaseReportForm, ResourceItemForm, PrivacyNoticeForm, InvestigationProcedureForm
from .models import InvestigationPlan, EvidenceItem, Finding, CaseReport
from .services.complaints import (
    persist_new_complaint,
    resolve_category,
    chat_enabled_for,
    mask_email,
    mask_phone,
    get_complaint_for_reporter,
)
from .services.iso_protocol import apply_iso_protocol, resolve_incident_family, FAMILY_LABELS
from .services.pdf_preview import build_preview, viewer_kind
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    canvas = None
    letter = None
    colors = None
    REPORTLAB_AVAILABLE = False
try:
    import qrcode
    QRCODE_AVAILABLE = True
except Exception:
    qrcode = None
    QRCODE_AVAILABLE = False
import io

def _ensure_default_library_items():
    marker_title = '__LIBRARY_SEEDED__'
    ResourceItem.objects.get_or_create(kind='update', title=marker_title, defaults={'is_published': False, 'sort_order': 999999})

def _build_monthly_metrics():
    visits_qs = PageViewLog.objects.filter(route_name='home').annotate(month=TruncMonth('viewed_at')).values('month').annotate(n=Count('id')).order_by('month')
    lookup_qs = Complaint.objects.filter(lookup_count__gte=2).annotate(month=TruncMonth('created_at')).values('month').annotate(n=Count('id')).order_by('month')
    faq_qs = PageViewLog.objects.filter(route_name='faq').annotate(month=TruncMonth('viewed_at')).values('month').annotate(n=Count('id')).order_by('month')
    submissions_qs = Complaint.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(n=Count('id')).order_by('month')
    followups_qs = Complaint.objects.filter(lookup_count__gte=2).annotate(month=TruncMonth('created_at')).values('month').annotate(n=Count('id')).order_by('month')
    categories_qs = Complaint.objects.annotate(month=TruncMonth('created_at')).values('month', 'category').annotate(n=Count('id')).order_by('month', 'category')
    months = set()
    for r in visits_qs:
        months.add(r['month'])
    for r in submissions_qs:
        months.add(r['month'])
    for r in followups_qs:
        months.add(r['month'])
    for r in lookup_qs:
        months.add(r['month'])
    for r in faq_qs:
        months.add(r['month'])
    for r in categories_qs:
        months.add(r['month'])
    months = sorted([m for m in months if m is not None])
    monthly_metrics = {}
    for m in months:
        label = m.strftime('%Y-%m')
        monthly_metrics[label] = {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'lookup_complaint': 0, 'faq': 0, 'categories': {}}
    for r in visits_qs:
        label = r['month'].strftime('%Y-%m') if r['month'] else 'N/A'
        monthly_metrics.setdefault(label, {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'lookup_complaint': 0, 'faq': 0, 'categories': {}})
        monthly_metrics[label]['visits_portal'] = r['n']
    for r in submissions_qs:
        label = r['month'].strftime('%Y-%m') if r['month'] else 'N/A'
        monthly_metrics.setdefault(label, {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'lookup_complaint': 0, 'faq': 0, 'categories': {}})
        monthly_metrics[label]['submissions'] = r['n']
    for r in followups_qs:
        label = r['month'].strftime('%Y-%m') if r['month'] else 'N/A'
        monthly_metrics.setdefault(label, {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'lookup_complaint': 0, 'faq': 0, 'categories': {}})
        monthly_metrics[label]['followups_gt3'] = r['n']
    for r in lookup_qs:
        label = r['month'].strftime('%Y-%m') if r['month'] else 'N/A'
        monthly_metrics.setdefault(label, {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'lookup_complaint': 0, 'faq': 0, 'categories': {}})
        monthly_metrics[label]['lookup_complaint'] = r['n']
    for r in faq_qs:
        label = r['month'].strftime('%Y-%m') if r['month'] else 'N/A'
        monthly_metrics.setdefault(label, {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'lookup_complaint': 0, 'faq': 0, 'categories': {}})
        monthly_metrics[label]['faq'] = r['n']
    for r in categories_qs:
        label = r['month'].strftime('%Y-%m') if r['month'] else 'N/A'
        cat = r['category'] or 'Sin categoría'
        monthly_metrics.setdefault(label, {'visits_portal': 0, 'submissions': 0, 'followups_gt3': 0, 'categories': {}})
        monthly_metrics[label]['categories'][cat] = r['n']
    return monthly_metrics

def public_home(request):
    stat, _ = PageViewStat.objects.get_or_create(route_name='home', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    try:
        PageViewLog.objects.create(route_name='home')
    except Exception:
        pass
    return render(request, 'denuncias/index.html')

def public_faq(request):
    stat, _ = PageViewStat.objects.get_or_create(route_name='faq', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    try:
        PageViewLog.objects.create(route_name='faq')
    except Exception:
        pass
    return render(request, 'denuncias/public_preguntas_frecuentes.html')

def public_guide(request):
    stat, _ = PageViewStat.objects.get_or_create(route_name='guide', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    try:
        PageViewLog.objects.create(route_name='guide')
    except Exception:
        pass
    return render(request, 'denuncias/public_guia.html')

def public_updates(request):
    stat, _ = PageViewStat.objects.get_or_create(route_name='updates', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    try:
        PageViewLog.objects.create(route_name='updates')
    except Exception:
        pass
    _ensure_default_library_items()
    main_documents = list(ResourceItem.objects.filter(kind='main_doc', is_published=True).order_by('sort_order', '-updated_at'))
    infographics = list(ResourceItem.objects.filter(kind='infographic', is_published=True).order_by('sort_order', '-updated_at'))
    recent_updates = list(ResourceItem.objects.filter(kind='update', is_published=True).order_by('-published_on', 'sort_order', '-updated_at'))
    return render(
        request,
        'denuncias/public_actualizaciones.html',
        {'main_documents': main_documents, 'infographics': infographics, 'recent_updates': recent_updates},
    )

@ratelimit(key='ip', rate='3/m', method='POST', block=False)
def public_submit_complaint(request):
    try:
        company_codes = [c for c, _ in getattr(PrivacyNotice, 'COMPANY_CHOICES', [])]
        if company_codes:
            for code in company_codes:
                PrivacyNotice.objects.get_or_create(company=code, defaults={'is_published': True})
    except Exception:
        pass

    privacy_notices = list(PrivacyNotice.objects.filter(is_published=True).order_by('company'))
    now = timezone.now()
    attempts = request.session.get('submit_attempts', [])
    now_ts = now.timestamp()
    attempts = [ts for ts in attempts if now_ts - ts < 60]
    if request.method == 'POST' and (
        len(attempts) >= 3 or getattr(request, 'limited', False)
    ):
        messages.error(request, 'Has alcanzado el límite de envíos. Inténtalo de nuevo en unos segundos.')
        form = ComplaintForm(request.POST, request.FILES)
        return render(
            request,
            'denuncias/public_enviar_denuncia.html',
            {'form': form, 'privacy_notices': privacy_notices},
            status=429,
        )
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            privacy_opened = (request.POST.get('privacy_policies_opened') or '').strip()
            terms_ok = request.POST.get('terms_accept') == 'on'
            if not terms_ok or not privacy_opened:
                if not privacy_opened:
                    form.add_error(None, 'Debes abrir una política de privacidad antes de enviar el reporte.')
                if not terms_ok:
                    form.add_error(None, 'Debes confirmar que has leído y aceptas la Política de Privacidad para enviar el reporte.')
                return render(request, 'denuncias/public_enviar_denuncia.html', {'form': form, 'privacy_notices': privacy_notices})

            complaint = form.save(commit=False)
            complaint.category = resolve_category(
                form.cleaned_data.get('action_type'),
                form.cleaned_data.get('category'),
                form.cleaned_data.get('queja_category'),
                form.cleaned_data.get('inquietud_category'),
            )
            incident = {
                'state': (request.POST.get('inc_state') or '').strip(),
                'branch': (request.POST.get('inc_branch') or '').strip(),
                'date': (request.POST.get('inc_date') or '').strip(),
                'time': (request.POST.get('inc_time') or '').strip(),
                'knows_actor': (request.POST.get('inc_knows_actor') or '').strip().lower(),
                'role': (request.POST.get('inc_role') or '').strip(),
                'has_witnesses': (request.POST.get('inc_has_witness') or '').strip().lower(),
                'actor_name': (request.POST.get('actor_name') or '').strip(),
                'actor_matricula': (request.POST.get('actor_matricula') or '').strip(),
                'actor_area': (request.POST.get('actor_area') or '').strip(),
            }
            optional = {}
            if request.POST.get('extra_choice') == 'si':
                optional = {
                    'recurrence': (form.cleaned_data.get('recurrence') or '').strip(),
                    'recurrence_since': (form.cleaned_data.get('recurrence_since') or '').strip(),
                    'immediate_risk': (form.cleaned_data.get('immediate_risk') or '').strip(),
                    'previous_report': (form.cleaned_data.get('previous_report') or '').strip(),
                    'previous_report_channel': (form.cleaned_data.get('previous_report_channel') or '').strip(),
                    'contact_preference': (form.cleaned_data.get('contact_preference') or '').strip(),
                    'share_permission': (form.cleaned_data.get('share_permission') or '').strip(),
                    'impact_notes': (form.cleaned_data.get('impact_notes') or '').strip(),
                }
            complaint = persist_new_complaint(
                complaint,
                files=form.cleaned_data.get('attachments'),
                request=request,
                optional=optional,
                password=form.cleaned_data.get('password'),
                privacy_opened=privacy_opened,
                incident=incident,
            )
            messages.success(request, f'Tu reporte ha sido enviado exitosamente. Tu folio es: {complaint.folio}')
            attempts.append(now.timestamp())
            request.session['submit_attempts'] = attempts
            try:
                from django.urls import reverse
                lookup_base = request.build_absolute_uri(reverse('denuncias:lookup_complaint'))
                lookup_url = f"{lookup_base}?folio={complaint.folio}"
            except Exception:
                lookup_url = ''
            qr_lines = [
                f"Folio: {complaint.folio}",
                f"Consulta: {lookup_url}",
                "Recomendaciones:",
                "- Guarda tu folio.",
                "- Consulta el avance en el portal.",
                "- No compartas datos sensibles.",
            ]
            request.session['last_folio'] = complaint.folio
            request.session['last_lookup_url'] = lookup_url
            request.session[f'auth_folio_{complaint.folio}'] = True
            return redirect('denuncias:complaint_submitted')
    else:
        form = ComplaintForm()
    stat, _ = PageViewStat.objects.get_or_create(route_name='submit_complaint', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    return render(request, 'denuncias/public_enviar_denuncia.html', {'form': form, 'privacy_notices': privacy_notices})

@require_GET
def complaint_submitted(request):
    folio = request.session.get('last_folio') or request.GET.get('folio')
    if not folio:
        return redirect('denuncias:lookup_complaint')
    try:
        complaint = Complaint.objects.get(folio=folio)
    except Complaint.DoesNotExist:
        return redirect('denuncias:lookup_complaint')
    try:
        from django.urls import reverse
        lookup_base = request.build_absolute_uri(reverse('denuncias:lookup_complaint'))
        lookup_url = f"{lookup_base}?folio={complaint.folio}"
    except Exception:
        lookup_url = request.session.get('last_lookup_url') or ''
    qr_lines = [
        f"Folio: {complaint.folio}",
        f"Consulta: {lookup_url}",
        "Recomendaciones:",
        "- Guarda tu folio.",
        "- Consulta el avance en el portal.",
        "- No compartas datos sensibles.",
    ]
    qr_text = "\n".join(qr_lines)
    return render(request, 'denuncias/denuncia_enviada.html', {'complaint': complaint, 'qr_text': qr_text})

def _eligible_assignment_admins():
    User = get_user_model()
    return list(User.objects.filter(is_staff=True, is_active=True, is_superuser=False).order_by('assignment_position', 'username'))

def _has_conflict_of_interest(admin, complaint: Complaint) -> bool:
    admin_username = (admin.username or '').strip().lower()
    admin_fullname = (admin.get_full_name() or '').strip().lower()
    admin_matricula = (getattr(admin, 'matricula', None) or '').strip().lower()
    reporter_name = (complaint.name or '').strip().lower()
    reporter_matricula = (complaint.reporter_matricula or '').strip().lower()
    actor_name = (complaint.actor_name or '').strip().lower()
    actor_matricula = (complaint.actor_matricula or '').strip().lower()
    description = (complaint.description or '').strip().lower()
    if reporter_name and (reporter_name == admin_fullname or reporter_name == admin_username):
        return True
    if actor_name and (actor_name == admin_fullname or actor_name == admin_username):
        return True
    id_ref = admin_matricula or admin_username
    if reporter_matricula and reporter_matricula == id_ref:
        return True
    if actor_matricula and actor_matricula == id_ref:
        return True
    text = description
    if admin_username and admin_username in text:
        return True
    if admin_fullname and admin_fullname in text:
        return True
    return False

def _auto_assign_complaint_round_robin(complaint: Complaint) -> None:
    admins = _eligible_assignment_admins()
    if not admins:
        return
    start_idx = 0
    try:
        last_log = ComplaintLog.objects.filter(action='auto_assign').order_by('-id').first()
        if last_log and last_log.user:
            for i, a in enumerate(admins):
                if a.id == last_log.user_id:
                    start_idx = (i + 1) % len(admins)
                    break
    except Exception:
        start_idx = 0
    chosen = None
    for offset in range(len(admins)):
        idx = (start_idx + offset) % len(admins)
        candidate = admins[idx]
        if not _has_conflict_of_interest(candidate, complaint):
            chosen = candidate
            break
    if not chosen:
        return
    Complaint.objects.filter(pk=complaint.pk, assigned_to__isnull=True).update(assigned_to=chosen)
    try:
        ComplaintLog.objects.create(complaint=complaint, user=chosen, action='auto_assign', details=f'Asignado automáticamente por round-robin a {chosen.get_full_name() or chosen.username}')
    except Exception:
        logging.exception('Error registrando ComplaintLog de auto-asignación')

def _notify_admins_new_complaint(request, complaint: Complaint) -> None:
    admins = _eligible_assignment_admins()
    recipients = [a.email for a in admins if (a.email or '').strip()]
    if not recipients:
        return
    from django.core.mail import send_mail
    from django.urls import reverse
    from django.conf import settings as dj_settings
    detail_url = request.build_absolute_uri(reverse('denuncias:admin_complaint_detail', kwargs={'complaint_id': complaint.id}))
    subject = f"Nuevo ticket de denuncia · Folio {complaint.folio}"
    assigned = complaint.assigned_to.get_full_name() if getattr(complaint, 'assigned_to', None) and complaint.assigned_to.get_full_name() else (complaint.assigned_to.username if getattr(complaint, 'assigned_to', None) else '-')
    body_lines = [
        f"Folio: {complaint.folio}",
        f"Estado: {complaint.get_status_display()}",
        f"Categoría: {complaint.get_category_display() if complaint.category else '-'}",
        f"Gravedad: {complaint.get_severity_display()}",
        f"Asignado: {assigned}",
        f"Creada: {complaint.created_at:%Y-%m-%d %H:%M}",
        "",
        f"Ver detalle: {detail_url}",
    ]
    send_mail(subject, "\n".join(body_lines), getattr(dj_settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost'), recipients, fail_silently=True)

def _notify_admin_assigned(request, complaint: Complaint, admin_user) -> None:
    if not admin_user or not (admin_user.email or '').strip():
        return
    from django.core.mail import send_mail
    from django.urls import reverse
    from django.conf import settings as dj_settings
    detail_url = request.build_absolute_uri(reverse('denuncias:admin_complaint_detail', kwargs={'complaint_id': complaint.id}))
    subject = f"Denuncia asignada · Folio {complaint.folio}"
    body_lines = [
        f"Folio: {complaint.folio}",
        f"Estado: {complaint.get_status_display()}",
        f"Categoría: {complaint.get_category_display() if complaint.category else '-'}",
        f"Gravedad: {complaint.get_severity_display()}",
        f"Área relacionada: {complaint.actor_area or '-'}",
        f"Asignado a: {admin_user.get_full_name() or admin_user.username}",
        "",
        f"Ver detalle: {detail_url}",
    ]
    send_mail(subject, "\n".join(body_lines), getattr(dj_settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost'), [admin_user.email], fail_silently=True)

@ratelimit(key='ip', rate='20/m', method='POST', block=False)
def public_lookup_complaint(request):
    complaint = None
    folio_qs = (request.GET.get('folio') or request.POST.get('folio') or '').strip().upper()
    if folio_qs and not folio_qs.startswith('GSI-'):
        folio_qs = f'GSI-{folio_qs}'
    is_authenticated = request.session.get(f'auth_folio_{folio_qs}') is True

    if request.method == 'POST':
        form = ComplaintLookupForm(request.POST)
        if getattr(request, 'limited', False):
            messages.error(request, 'Demasiados intentos de consulta. Espera unos segundos e inténtalo de nuevo.')
        elif form.is_valid():
            folio = form.cleaned_data['folio'].upper()
            password = form.cleaned_data.get('password')
            complaint, error = get_complaint_for_reporter(folio, password)
            if error == 'password_required':
                form.add_error('password', 'Esta denuncia está protegida. Ingresa tu contraseña.')
            elif error == 'invalid_password':
                form.add_error('password', 'Contraseña incorrecta.')
            elif error == 'not_found':
                messages.error(request, 'No se encontró ninguna denuncia con ese folio.')
            else:
                request.session[f'auth_folio_{folio}'] = True
                is_authenticated = True
                Complaint.objects.filter(pk=complaint.pk).update(lookup_count=F('lookup_count') + 1)
                complaint.refresh_from_db(fields=['lookup_count'])
                try:
                    if complaint.lookup_count >= 2:
                        stat, _ = PageViewStat.objects.get_or_create(route_name='lookup_complaint', defaults={'count': 0})
                        PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
                    PageViewLog.objects.create(route_name='lookup_complaint')
                except Exception:
                    pass
                from urllib.parse import urlencode
                qs = urlencode({'folio': complaint.folio})
                return redirect(f"{reverse('denuncias:lookup_complaint')}?{qs}")
        if complaint is None and folio_qs and request.session.get(f'auth_folio_{folio_qs}') is True:
            try:
                complaint = Complaint.objects.select_related('assigned_to').get(folio=folio_qs)
            except Complaint.DoesNotExist:
                complaint = None
    else:
        folio_qs = (request.GET.get('folio') or '').strip().upper()
        if folio_qs and not folio_qs.startswith('GSI-'):
            folio_qs = f'GSI-{folio_qs}'
        form = ComplaintLookupForm(initial={'folio': folio_qs or 'GSI-'})
        if folio_qs and request.session.get(f'auth_folio_{folio_qs}') is True:
            try:
                complaint = Complaint.objects.select_related('assigned_to').get(folio=folio_qs)
            except Complaint.DoesNotExist:
                complaint = None

    show_reporter_name = False
    if complaint:
        admin_display_name = None
        if getattr(complaint, 'assigned_to', None):
            admin_display_name = complaint.assigned_to.get_full_name() or complaint.assigned_to.username
        reporter_name = (complaint.name or '').strip()
        if reporter_name:
            show_reporter_name = not admin_display_name or reporter_name != (admin_display_name or '').strip()
    chat_enabled = chat_enabled_for(complaint)
    chat_messages = ChatMessage.objects.filter(complaint=complaint).order_by('created_at') if complaint else []
    reporter_notes = ReporterNote.objects.filter(complaint=complaint).order_by('created_at') if complaint else []
    optional_items = []
    if complaint and (complaint.reporter_notes_summary or '').strip():
        try:
            optional_items = [s.strip() for s in complaint.reporter_notes_summary.split(';') if s.strip()]
        except Exception:
            optional_items = [(complaint.reporter_notes_summary or '').strip()]
    masked_email = mask_email(getattr(complaint, 'email', None))
    masked_phone = mask_phone(getattr(complaint, 'phone', None))
    return render(request, 'denuncias/public_consultar_denuncia.html', {'form': form, 'complaint': complaint, 'show_reporter_name': show_reporter_name, 'chat_enabled': chat_enabled, 'chat_messages': chat_messages, 'reporter_notes': reporter_notes, 'chat_form': ChatMessageForm(), 'note_form': ReporterNoteForm(), 'masked_email': masked_email, 'masked_phone': masked_phone, 'optional_items': optional_items})

def submit_chat_message(request, folio):
    folio = folio.upper()
    if request.method != 'POST':
        from urllib.parse import urlencode
        qs = urlencode({'folio': folio})
        return redirect(f"{reverse('denuncias:lookup_complaint')}?{qs}")
    if not request.session.get(f'auth_folio_{folio}'):
        messages.error(request, 'Sesión no válida. Ingresa tu contraseña nuevamente.')
        from urllib.parse import urlencode
        qs = urlencode({'folio': folio})
        return redirect(f"{reverse('denuncias:lookup_complaint')}?{qs}")
    complaint = get_object_or_404(Complaint, folio=folio)
    if not chat_enabled_for(complaint):
        messages.error(request, 'El chat no está habilitado para el estado actual de la denuncia.')
        from urllib.parse import urlencode
        qs = urlencode({'folio': complaint.folio})
        return redirect(f"{reverse('denuncias:lookup_complaint')}?{qs}")
    form = ChatMessageForm(request.POST)
    if form.is_valid():
        ChatMessage.objects.create(complaint=complaint, sender='reporter', message=form.cleaned_data['message'])
        messages.success(request, 'Mensaje enviado.')
    else:
        messages.error(request, 'No se pudo enviar el mensaje.')
    from urllib.parse import urlencode
    qs = urlencode({'folio': complaint.folio})
    return redirect(f"{reverse('denuncias:lookup_complaint')}?{qs}")

def add_reporter_note(request, folio):
    folio = folio.upper()
    if request.method != 'POST':
        return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={folio}")
    if not request.session.get(f'auth_folio_{folio}'):
        messages.error(request, 'Sesión no válida. Ingresa tu contraseña nuevamente.')
        return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={folio}")
    complaint = get_object_or_404(Complaint, folio=folio)
    form = ReporterNoteForm(request.POST)
    if form.is_valid():
        ReporterNote.objects.create(complaint=complaint, content=form.cleaned_data['content'])
        messages.success(request, 'Nota agregada.')
    else:
        messages.error(request, 'No se pudo agregar la nota.')
    return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={complaint.folio}")

def admin_register(request, code):
    invite_code = code
    secret = getattr(settings, 'ADMIN_INVITE_SECRET', None)
    expected_code = getattr(settings, 'ADMIN_INVITE_CODE', None)
    valid = False
    if secret:
        valid = validate_totp_token(invite_code, secret, timestep=60, digits=8, window=1)
    elif expected_code:
        valid = invite_code == expected_code
    if not valid:
        raise Http404('Página no encontrada')
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_verified = True
            user.verification_code = None
            user.verification_code_expires = None
            user.save()
            login(request, user)
            messages.success(request, 'Cuenta creada y verificada. Bienvenido al panel de administración.')
            return redirect('denuncias:home')
    else:
        form = AdminRegistrationForm()
    return render(request, 'denuncias/admin_register.html', {'form': form})

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def admin_verify(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    masked_phone = None
    if user.phone_number:
        digits = ''.join((ch for ch in user.phone_number if ch.isdigit()))
        if len(digits) >= 2:
            masked_phone = f'*** *** **{digits[-2:]}'
        else:
            masked_phone = '***'
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if user.verification_code == code and user.verification_code_expires and (timezone.now() < user.verification_code_expires):
                user.is_verified = True
                user.verification_code = None
                user.verification_code_expires = None
                user.save()
                login(request, user)
                messages.success(request, 'Verificación exitosa. Bienvenido al panel de administración.')
                return redirect('denuncias:admin_dashboard')
            messages.error(request, 'Código inválido o expirado.')
    else:
        form = VerificationCodeForm()
    return render(request, 'denuncias/admin_verification.html', {'form': form, 'user': user, 'debug': getattr(settings, 'DEBUG', False), 'masked_phone': masked_phone})

def logout_view(request):
    if request.user.is_authenticated:
        record_logout(request)
        logout(request)
        messages.success(request, 'Sesión cerrada correctamente.')
    login_url = reverse('denuncias:login')
    token_cfg = getattr(settings, 'ADMIN_LOGIN_TOKEN', '')
    if token_cfg:
        return redirect(f'{login_url}?token={token_cfg}')
    return redirect(login_url)

def admin_login_redirect(request):
    token_cfg = getattr(settings, 'ADMIN_LOGIN_TOKEN', '')
    login_url = reverse('denuncias:login')
    next_url = request.GET.get('next')
    if token_cfg:
        if next_url:
            return redirect(f'{login_url}?token={token_cfg}&next={next_url}')
        return redirect(f'{login_url}?token={token_cfg}')
    else:
        if next_url:
            return redirect(f'{login_url}?next={next_url}')
        return redirect(login_url)

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('denuncias:dashboard')
    token_cfg = getattr(settings, 'ADMIN_LOGIN_TOKEN', '')
    if token_cfg:
        provided = (request.GET.get('token') or request.POST.get('token') or '').strip()
        gate_ok = request.session.get('admin_login_gate_ok') is True
        if provided and provided == token_cfg:
            request.session['admin_login_gate_ok'] = True
            gate_ok = True
        if not gate_ok:
            raise Http404()
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if _is_verified_admin_user(user):
            login(request, user)
            record_login(request, user)
            try:
                del request.session['admin_login_gate_ok']
            except Exception:
                pass
            if next_url and next_url.startswith('/denuncias/'):
                return redirect(next_url)
            if getattr(user, 'is_staff', False) and (getattr(user, 'role', '') == 'Delegador' or user.username == 'Delegador'):
                return redirect('denuncias:delegador_queue')
            if (getattr(user, 'role', '') or '').strip().lower() == 'actualizador':
                return redirect('denuncias:actualizador_dashboard')
            return redirect('denuncias:dashboard')
        else:
            messages.error(request, AdminLoginForm.GENERIC_LOGIN_ERROR)
    return render(request, 'denuncias/login.html', {'next': next_url})

@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def admin_login(request):
    force = (request.GET.get('force') or '').strip().lower() in {'1', 'true', 'yes', 'on'}
    if request.method == 'GET' and not force and request.user.is_authenticated and getattr(request.user, 'is_staff', False):
        u = request.user
        if getattr(u, 'role', '') == 'Delegador' or u.username == 'Delegador':
            return redirect('denuncias:delegador_queue')
        if (getattr(u, 'role', '') or '').strip().lower() == 'actualizador':
            return redirect('denuncias:actualizador_dashboard')
        return redirect('denuncias:admin_dashboard')

    now = timezone.now()
    attempts = request.session.get('login_attempts', [])
    now_ts = now.timestamp()
    attempts = [ts for ts in attempts if now_ts - ts < 60]
    if request.method == 'POST' and getattr(request, 'limited', False):
        messages.error(request, 'Demasiados intentos de inicio de sesión. Espera unos segundos e inténtalo de nuevo.')
        form = AdminLoginForm(request.POST)
        return render(request, 'denuncias/admin_login.html', {'form': form}, status=429)
    if request.method == 'GET':
        next_url = request.GET.get('next', '').strip()
        if next_url:
            request.session['admin_next'] = next_url
    if request.method == 'POST' and len(attempts) >= 5:
        messages.error(request, 'Demasiados intentos de inicio de sesión. Espera unos segundos e inténtalo de nuevo.')
        form = AdminLoginForm(request.POST)
        return render(request, 'denuncias/admin_login.html', {'form': form})
    if request.method == 'POST':
        if request.user.is_authenticated:
            record_logout(request)
            logout(request)
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if _is_verified_admin_user(user):
                login(request, user)
                record_login(request, user)
                request.session['login_attempts'] = []
                next_url = request.session.pop('admin_next', '')
                if next_url and next_url.startswith('/denuncias/'):
                    return redirect(next_url)
                if getattr(user, 'role', '') == 'Delegador' or user.username == 'Delegador':
                    return redirect('denuncias:delegador_queue')
                if (getattr(user, 'role', '') or '').strip().lower() == 'actualizador':
                    return redirect('denuncias:actualizador_dashboard')
                return redirect('denuncias:admin_dashboard')
            else:
                form.add_error(
                    'password',
                    AdminLoginForm.GENERIC_LOGIN_ERROR,
                )
                attempts.append(now_ts)
                request.session['login_attempts'] = attempts
        else:
            attempts.append(now_ts)
            request.session['login_attempts'] = attempts
    else:
        form = AdminLoginForm()
    return render(request, 'denuncias/admin_login.html', {'form': form})

def admin_logout(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('denuncias:admin_login')

def _is_verified_admin_user(user):
    dev_bypass = (
        getattr(settings, 'DEBUG', False)
        and getattr(settings, 'ADMIN_DEV_BYPASS', False)
    )
    return bool(
        getattr(user, 'is_authenticated', False)
        and getattr(user, 'is_staff', False)
        and (
            getattr(user, 'is_verified', False)
            or dev_bypass
        )
    )

def is_admin(user):
    if not _is_verified_admin_user(user):
        return False
    if user.is_superuser:
        return True
    return (getattr(user, 'role', '') or '').strip().lower() != 'actualizador'

def is_actualizador(user):
    if not _is_verified_admin_user(user):
        return False
    if user.is_superuser:
        return True
    role = (getattr(user, 'role', '') or '').strip().lower()
    if role == 'actualizador':
        return True
    try:
        return user.groups.filter(name='Actualizador').exists()
    except Exception:
        return False

def _client_ip(request):
    if getattr(settings, 'USE_X_FORWARDED_FOR', False):
        xff = request.META.get('HTTP_X_FORWARDED_FOR') or ''
        parts = [p.strip() for p in xff.split(',') if p.strip()]
        if parts:
            trusted = int(getattr(settings, 'TRUSTED_PROXY_COUNT', 1) or 1)
            index = max(len(parts) - trusted, 0)
            return parts[index]
    return request.META.get('REMOTE_ADDR')

def record_login(request, user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return
    try:
        ip = _client_ip(request)
        UserSessionAudit.objects.create(
            user=user,
            login_at=timezone.now(),
            session_key=(request.session.session_key or '')[:64],
            ip_address=ip if ip else None,
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:255],
        )
    except Exception:
        pass

def record_logout(request):
    if not getattr(request.user, 'is_authenticated', False):
        return
    try:
        audit = (
            UserSessionAudit.objects.filter(user=request.user, logout_at__isnull=True)
            .order_by('-login_at')
            .first()
        )
        if audit:
            audit.logout_at = timezone.now()
            audit.save(update_fields=['logout_at'])
    except Exception:
        pass

def _format_duration(seconds):
    seconds = int(seconds or 0)
    if seconds <= 0:
        return '—'
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours:
        return f'{hours}h {minutes:02d}m'
    return f'{minutes}m'

@user_passes_test(is_actualizador, login_url='denuncias:admin_login')
def actualizador_dashboard(request):
    resources = ResourceItem.objects.exclude(title='__LIBRARY_SEEDED__')
    return render(
        request,
        'denuncias/actualizador_dashboard.html',
        {
            'resources_total': resources.count(),
            'docs_total': resources.filter(kind='main_doc').count(),
            'infographics_total': resources.filter(kind='infographic').count(),
            'updates_total': resources.filter(kind='update').count(),
            'privacy_total': PrivacyNotice.objects.count(),
        },
    )

@user_passes_test(is_actualizador, login_url='denuncias:admin_login')
def actualizador_library(request):
    seed_title = '__LIBRARY_SEEDED__'
    edit_id = (request.GET.get('edit') or '').strip()
    edit_item = None
    if edit_id.isdigit():
        edit_item = ResourceItem.objects.filter(pk=int(edit_id)).exclude(title=seed_title).first()

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip().lower()
        if action == 'delete':
            item_id = (request.POST.get('item_id') or '').strip()
            if item_id.isdigit():
                item = ResourceItem.objects.filter(pk=int(item_id)).exclude(title=seed_title).first()
                if item:
                    item.delete()
                    messages.success(request, 'Recurso eliminado.')
            return redirect('denuncias:actualizador_library')

        item_id = (request.POST.get('item_id') or '').strip()
        instance = None
        if item_id.isdigit():
            instance = ResourceItem.objects.filter(pk=int(item_id)).exclude(title=seed_title).first()
        form = ResourceItemForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cambios guardados.')
            return redirect('denuncias:actualizador_library')
        create_form = form
    else:
        create_form = ResourceItemForm(instance=edit_item)

    items = list(ResourceItem.objects.exclude(title=seed_title).order_by('kind', 'sort_order', '-published_on', '-updated_at'))
    grouped = {'main_doc': [], 'infographic': [], 'update': []}
    for it in items:
        grouped.setdefault(it.kind, []).append(it)
    kind_labels = dict(ResourceItem.KIND_CHOICES)
    groups = [(k, kind_labels.get(k, k), grouped.get(k, [])) for k in ['main_doc', 'infographic', 'update']]
    return render(
        request,
        'denuncias/actualizador_library.html',
        {
            'groups': groups,
            'form': create_form,
            'edit_item': edit_item,
        },
    )

@user_passes_test(is_actualizador, login_url='denuncias:admin_login')
def actualizador_privacy(request):
    edit_id = (request.GET.get('edit') or '').strip()
    edit_notice = None
    if edit_id.isdigit():
        edit_notice = PrivacyNotice.objects.filter(pk=int(edit_id)).first()

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip().lower()
        if action == 'delete':
            notice_id = (request.POST.get('notice_id') or '').strip()
            if notice_id.isdigit():
                n = PrivacyNotice.objects.filter(pk=int(notice_id)).first()
                if n:
                    n.delete()
                    messages.success(request, 'Aviso eliminado.')
            return redirect('denuncias:actualizador_privacy')

        notice_id = (request.POST.get('notice_id') or '').strip()
        instance = None
        if notice_id.isdigit():
            instance = PrivacyNotice.objects.filter(pk=int(notice_id)).first()
        form = PrivacyNoticeForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cambios guardados.')
            return redirect('denuncias:actualizador_privacy')
        notice_form = form
    else:
        notice_form = PrivacyNoticeForm(instance=edit_notice)

    notices = list(PrivacyNotice.objects.all().order_by('company'))
    return render(
        request,
        'denuncias/actualizador_privacy.html',
        {
            'notices': notices,
            'form': notice_form,
            'edit_notice': edit_notice,
        },
    )

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_dashboard(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    complaints = Complaint.objects.select_related('assigned_to').all()
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if search_query:
        complaints = complaints.filter(Q(folio__icontains=search_query) | Q(name__icontains=search_query) | Q(email__icontains=search_query) | Q(description__icontains=search_query))
    category_filter = request.GET.get('category', '')
    severity_filter = request.GET.get('severity', '')
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    if severity_filter:
        complaints = complaints.filter(severity=severity_filter)
    
    return render(request, 'denuncias/dashboard.html', {'complaints': complaints})

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_download_main_attachment(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    if is_delegador:
        raise PermissionDenied("El Delegador no tiene acceso a los adjuntos.")
    if not request.user.is_superuser:
        if complaint.assigned_to != request.user:
            raise Http404("No autorizado")

    if not complaint.attachment:
        raise Http404("Archivo no encontrado")

    try:
        ComplaintLog.objects.create(
            complaint=complaint,
            user=request.user,
            action='file_access',
            details=f"Acceso a adjunto principal: {complaint.attachment.name}"
        )
    except Exception:
        pass

    try:
        return FileResponse(
            complaint.attachment,
            as_attachment=True,
            filename=os.path.basename(complaint.attachment.name),
        )
    except FileNotFoundError:
        raise Http404("El archivo físico no existe")

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_download_attachment(request, complaint_id, attachment_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    if is_delegador:
        raise PermissionDenied("El Delegador no tiene acceso a los adjuntos.")
    if not request.user.is_superuser:
        if complaint.assigned_to != request.user:
            raise Http404("No autorizado")

    attachment = get_object_or_404(ComplaintAttachment, id=attachment_id, complaint=complaint)
    
    if not attachment.file:
        raise Http404("Archivo no encontrado")

    try:
        ComplaintLog.objects.create(
            complaint=complaint,
            user=request.user,
            action='file_access',
            details=f"Acceso a adjunto extra: {attachment.file.name}"
        )
    except Exception:
        pass

    try:
        return FileResponse(
            attachment.file,
            as_attachment=True,
            filename=os.path.basename(attachment.file.name),
        )
    except FileNotFoundError:
        raise Http404("El archivo físico no existe")

def _evidence_permitted(request, complaint):
    """Superusuario y Delegador acceden a todo; el resto solo a sus casos."""
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    if request.user.is_superuser or is_delegador:
        return True
    return complaint.assigned_to == request.user

def _evidence_source(evidence):
    """Devuelve el archivo a mostrar y su tipo de visor.

    Si el original no se puede previsualizar se usa la vista previa PDF
    generada al subirlo (Word, Excel, PowerPoint).
    """
    if evidence.preview_pdf:
        return evidence.preview_pdf, 'pdf'
    return evidence.file, viewer_kind(evidence.file.name)

def _evidence_watermark(request):
    user = request.user
    name = (user.get_full_name() or '').strip() or user.username
    return f'{name} · {timezone.localtime():%d/%m/%Y %H:%M}'

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_view_evidence(request, complaint_id, evidence_id):
    """Muestra la evidencia dentro del panel, con marca de agua."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if not _evidence_permitted(request, complaint):
        raise Http404("No autorizado")

    evidence = get_object_or_404(EvidenceItem, id=evidence_id, complaint=complaint)
    if not evidence.file:
        raise Http404("Archivo no encontrado")

    source, kind = _evidence_source(evidence)

    return render(request, 'denuncias/evidence_viewer.html', {
        'complaint': complaint,
        'evidence': evidence,
        'view_kind': kind,
        'source_name': os.path.basename(source.name),
        'watermark': _evidence_watermark(request),
        'stream_url': reverse('denuncias:admin_download_evidence', args=[complaint.id, evidence.id]),
    })

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_download_evidence(request, complaint_id, evidence_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if not _evidence_permitted(request, complaint):
        raise Http404("No autorizado")

    evidence = get_object_or_404(EvidenceItem, id=evidence_id, complaint=complaint)
    
    if not evidence.file:
        raise Http404("Archivo no encontrado")

    source, kind = _evidence_source(evidence)
    if kind == 'none':
        raise Http404("Este formato no puede visualizarse.")

    try:
        ComplaintLog.objects.create(
            complaint=complaint,
            user=request.user,
            action='file_access',
            details=f"Acceso a evidencia: {evidence.file.name}"
        )
    except Exception:
        pass

    try:
        response = FileResponse(
            source,
            as_attachment=False,
            filename=os.path.basename(source.name),
        )
    except FileNotFoundError:
        raise Http404("El archivo físico no existe")

    # Permite incrustar el archivo en el visor del panel (mismo origen).
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
    return response

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_send_chat_message(request, complaint_id):
    complaint = get_object_or_404(Complaint.objects.select_related('assigned_to'), id=complaint_id)
    if not request.user.is_superuser:
        assigned_id = getattr(complaint.assigned_to, 'id', None)
        if assigned_id not in (None, request.user.id):
            messages.error(request, 'No tienes permiso para interactuar con este reporte.')
            return redirect('denuncias:dashboard')
    if request.method != 'POST':
        return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)
    form = ChatMessageForm(request.POST)
    if form.is_valid():
        ChatMessage.objects.create(complaint=complaint, sender='admin', message=form.cleaned_data['message'])
        messages.success(request, 'Mensaje enviado al chat.')
    else:
        messages.error(request, 'No se pudo enviar el mensaje.')
    return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='admin_login')
def admin_reset_complaints(request):
    if request.method != 'POST':
        return redirect('denuncias:admin_dashboard')
    if not getattr(settings, 'DEBUG', False):
        messages.error(request, 'Acción no permitida en producción.')
        return redirect('denuncias:admin_dashboard')
    if request.POST.get('confirm') != 'CONFIRMAR':
        messages.error(request, 'Escribe CONFIRMAR para ejecutar esta acción.')
        return redirect('denuncias:admin_dashboard')
    admin_password = (request.POST.get('admin_password') or '').strip()
    if not admin_password or (not request.user.check_password(admin_password)):
        messages.error(request, 'Contraseña de administrador inválida.')
        return redirect('denuncias:admin_dashboard')
    qs = Complaint.objects.all()
    for c in qs.iterator():
        if c.attachment:
            try:
                c.attachment.delete(save=False)
            except Exception:
                pass
    deleted_total = qs.delete()[0]
    messages.success(request, f'Se eliminaron {deleted_total} objetos (denuncias y registros).')
    return redirect('denuncias:admin_dashboard')

def admin_root(request):
    return redirect('denuncias:admin_login')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_reset_metrics(request):
    if request.method != 'POST':
        return redirect('denuncias:admin_metrics_config')
    if not getattr(settings, 'DEBUG', False):
        messages.error(request, 'Acción no permitida en producción.')
        return redirect('denuncias:admin_metrics_config')
    if request.POST.get('confirm') != 'CONFIRMAR':
        messages.error(request, 'Escribe CONFIRMAR para ejecutar esta acción.')
        return redirect('denuncias:admin_metrics_config')
    admin_password = (request.POST.get('admin_password') or '').strip()
    if not admin_password or (not request.user.check_password(admin_password)):
        messages.error(request, 'Contraseña de administrador inválida.')
        return redirect('denuncias:admin_metrics_config')
    updated = PageViewStat.objects.all().update(count=0, last_viewed=None)
    messages.success(request, f'Se reiniciaron {updated} métricas de páginas.')
    return redirect('denuncias:admin_metrics_config')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_reset_monthly_metrics(request):
    if request.method != 'POST':
        return redirect('denuncias:admin_metrics_config')
    if not getattr(settings, 'DEBUG', False):
        messages.error(request, 'Acción no permitida en producción.')
        return redirect('denuncias:admin_metrics_config')
    if request.POST.get('confirm') != 'CONFIRMAR':
        messages.error(request, 'Escribe CONFIRMAR para ejecutar esta acción.')
        return redirect('denuncias:admin_metrics_config')
    admin_password = (request.POST.get('admin_password') or '').strip()
    if not admin_password or (not request.user.check_password(admin_password)):
        messages.error(request, 'Contraseña de administrador inválida.')
        return redirect('denuncias:admin_metrics_config')
    deleted_logs = PageViewLog.objects.all().delete()[0]
    updated_lookups = Complaint.objects.all().update(lookup_count=0)
    messages.success(request, f'Se borraron {deleted_logs} registros de vistas y se reiniciaron {updated_lookups} contadores de seguimiento.')
    return redirect('denuncias:admin_metrics_config')

def dashboard(request):
    if not _is_verified_admin_user(request.user):
        login_url = reverse('denuncias:admin_login')
        token_cfg = getattr(settings, 'ADMIN_LOGIN_TOKEN', '')
        qs = f'next={request.path}'
        if token_cfg:
            qs = f'token={token_cfg}&' + qs
        return redirect(f'{login_url}?{qs}')
    if getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador':
        return redirect('denuncias:delegador_queue')
    if (getattr(request.user, 'role', '') or '').strip().lower() == 'actualizador':
        return redirect('denuncias:actualizador_dashboard')
    stat, _ = PageViewStat.objects.get_or_create(route_name='dashboard', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    try:
        PageViewLog.objects.create(route_name='dashboard')
    except Exception:
        pass
    
    base_complaints = Complaint.objects.select_related('assigned_to').all()
    if not request.user.is_superuser:
        base_complaints = base_complaints.filter(assigned_to=request.user)
            
    stats = {'total': base_complaints.count()}
    status_counts = {}
    status_cards = []
    for code, label in Complaint.STATUS_CHOICES:
        cnt = base_complaints.filter(status=code).count()
        status_counts[code] = cnt
        status_cards.append({'code': code, 'label': label, 'count': cnt})
        
    received_count = status_counts.get('enviado', 0)
    closed_count = status_counts.get('resuelto', 0) + status_counts.get('archivado', 0)
    transferred_count = status_counts.get('transferido', 0)
    active_count = stats['total'] - (closed_count + transferred_count)
    
    mini_cards = []
    mini_cards.append({'label': 'Denuncias recibidas', 'count': received_count})
    mini_cards.append({'label': 'Denuncias activas', 'count': active_count})
    mini_cards.append({'label': 'Cerradas (Resuelto + Archivado)', 'count': closed_count})
    
    complaints = base_complaints
    
    status_filter = request.GET.get('status', '').strip()
    category_filter = request.GET.get('category', '').strip()
    severity_filter = request.GET.get('severity', '').strip()
    search_query = request.GET.get('search', '').strip()
    date_from = request.GET.get('from', '').strip()
    date_to = request.GET.get('to', '').strip()

    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    if severity_filter:
        complaints = complaints.filter(severity=severity_filter)
    if search_query:
        complaints = complaints.filter(Q(folio__icontains=search_query) | Q(name__icontains=search_query) | Q(email__icontains=search_query) | Q(description__icontains=search_query))
    if date_from:
        try:
            df = parse_date(date_from)
            if df:
                complaints = complaints.filter(created_at__date__gte=df)
        except Exception:
            pass
    if date_to:
        try:
            dt = parse_date(date_to)
            if dt:
                complaints = complaints.filter(created_at__date__lte=dt)
        except Exception:
            pass
            
    complaints = complaints.order_by('-created_at')
    
    denuncias = complaints.filter(action_type='denuncia')[:20]
    consultas = complaints.filter(action_type='consulta')[:20]

    monthly_metrics = _build_monthly_metrics()

    status_labels = dict(Complaint.STATUS_CHOICES)
    severity_labels = dict(Complaint.SEVERITY_CHOICES)
    category_labels = dict(Complaint.CATEGORY_CHOICES)

    active_filters = sum(1 for v in [status_filter, category_filter, severity_filter, search_query, date_from, date_to] if v)

    return render(request, 'denuncias/dashboard.html', {
        'denuncias': denuncias,
        'consultas': consultas,
        'status_cards': status_cards,
        'mini_cards': mini_cards,
        'total_complaints': stats['total'],
        'active_complaints': active_count,
        'status_choices': Complaint.STATUS_CHOICES,
        'severity_choices': Complaint.SEVERITY_CHOICES,
        'category_choices': Complaint.CATEGORY_CHOICES,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'category_filter': category_filter,
        'status_filter_label': status_labels.get(status_filter, status_filter),
        'severity_filter_label': severity_labels.get(severity_filter, severity_filter),
        'category_filter_label': category_labels.get(category_filter, category_filter),
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'active_filters': active_filters,
        'page_obj': None
    })

def public_download_main_attachment(request, folio):
    folio = folio.upper()
    if not request.session.get(f'auth_folio_{folio}'):
        return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={folio}")
    complaint = get_object_or_404(Complaint, folio=folio)
    if not complaint.attachment:
        raise Http404("No hay archivo")
    try:
        if request.user.is_authenticated:
            ComplaintLog.objects.create(
                complaint=complaint,
                user=request.user,
                action='file_access_public',
                details=f"Acceso público a adjunto principal: {complaint.attachment.name}"
            )
    except Exception:
        pass
    try:
        return FileResponse(
            complaint.attachment,
            as_attachment=True,
            filename=os.path.basename(complaint.attachment.name),
        )
    except FileNotFoundError:
        raise Http404("El archivo físico no existe")

def public_download_attachment(request, folio, attachment_id):
    folio = folio.upper()
    if not request.session.get(f'auth_folio_{folio}'):
        return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={folio}")
    complaint = get_object_or_404(Complaint, folio=folio)
    attachment = get_object_or_404(ComplaintAttachment, id=attachment_id, complaint=complaint)
    try:
        if request.user.is_authenticated:
            ComplaintLog.objects.create(
                complaint=complaint,
                user=request.user,
                action='file_access_public',
                details=f"Acceso público a adjunto adicional: {attachment.file.name}"
            )
    except Exception:
        pass
    try:
        return FileResponse(
            attachment.file,
            as_attachment=True,
            filename=os.path.basename(attachment.file.name),
        )
    except FileNotFoundError:
        raise Http404("El archivo físico no existe")

@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def public_chatbot(request):
    return _unused_chatbot(request)

def _unused_chatbot(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    import json
    import re
    from django.urls import reverse
    from django.conf import settings
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip().lower()
        is_init = data.get('init', False)
    except:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    
    response_data = {
        'response': '',
        'options': []
    }

    main_menu = [
        {'text': '📝 Quiero denunciar', 'value': 'menu_denunciar'},
        {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
        {'text': '📘 Guía de denuncias', 'value': 'menu_guia'},
        {'text': '❓ Preguntas frecuentes', 'value': 'menu_faq'},
        {'text': '📚 Biblioteca', 'value': 'menu_biblioteca'},
        {'text': '👤 Hablar con un asesor', 'value': 'faq_human_contact'},
        {'text': '💬 Otras inquietudes', 'value': 'menu_otros'}
    ]
    knowledge_base = {
        'def_denuncia': (
            "Reporte formal sobre actos graves que violan la ley, el Código de Ética o los valores de la organización, "
            "implicando riesgos legales, financieros o reputacionales."
        ),
        'def_queja': (
            "Manifestación de insatisfacción respecto a procesos internos, servicios administrativos o condiciones laborales "
            "que, sin ser delitos, afectan el ambiente de trabajo o el bienestar del colaborador."
        ),
        'def_inquietud': (
            "Consulta o duda sobre la interpretación de normativas, el Código de Ética o situaciones ambiguas donde no se "
            "tiene certeza de si constituyen una falta, buscando orientación preventiva."
        ),
        'cats_denuncia': (
            "Ejemplos:\n"
            "• Fraude y corrupción: Reporte de sobornos, falsificación de documentos o robo de activos.\n"
            "• Acoso y discriminación: Hostigamiento laboral, acoso sexual o discriminación por género, raza o religión."
        ),
        'cats_queja': (
            "Ejemplos:\n"
            "• Deficiencias en servicios: Falta de insumos básicos o mal estado de instalaciones.\n"
            "• Procesos administrativos: Errores continuos no resueltos o falta de claridad en procedimientos."
        ),
        'cats_inquietud': (
            "Ejemplos:\n"
            "• Conflictos de interés: Consultas sobre regalos de proveedores o clientes.\n"
            "• Interpretación normativa: Dudas sobre cómo aplicar el Código de Conducta en situaciones complejas."
        )
    }

    is_greeting = bool(re.match(
        r'^(hola|buenas|buenos d|buen d|saludos|hey|hello|hi|qué tal|que tal)\b', message
    )) and len(message.split()) <= 4
    if is_init or message in ['menu', 'inicio', 'hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos'] or is_greeting:
        response_data['response'] = "¡Hola! Soy el asistente virtual del Canal de Denuncias. Estoy aquí para orientarte de manera confidencial y profesional. ¿En qué puedo ayudarte hoy?"
        response_data['options'] = main_menu
        return JsonResponse(response_data)

    def normalize(text):
        replacements = (
            ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
            ("ñ", "n"), ("ü", "u")
        )
        for a, b in replacements:
            text = text.replace(a, b).replace(a.upper(), b.upper())
        text = re.sub(r'[^\w\s]', '', text) 
        return text

    msg_norm = normalize(message)

    qa_list = [
        (r"\bque\s+es\s+una\s+denuncia\b|\bdefinicion\s+de\s+denuncia\b|\bdenuncia\s*que\s*es\b",
         "Definición de denuncia:\n\n" + knowledge_base['def_denuncia'] + "\n\n" + knowledge_base['cats_denuncia'],
         [
             {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
             {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
             {'text': '🔙 Menú Principal', 'value': 'menu'}
         ]),
        (r"\bque\s+es\s+una\s+queja\b|\bdefinicion\s+de\s+queja\b|\bqueja\s*que\s*es\b",
         "Definición de queja:\n\n" + knowledge_base['def_queja'] + "\n\n" + knowledge_base['cats_queja'],
         [
             {'text': '📝 Ir a Denunciar', 'value': 'menu_denunciar'},
             {'text': '📘 Ver guía', 'value': 'menu_guia'},
             {'text': '🔙 Menú Principal', 'value': 'menu'}
         ]),
        (r"\bque\s+es\s+una\s+inquietud\b|\bdefinicion\s+de\s+inquietud\b|\binquietud\s*que\s*es\b",
         "Definición de inquietud:\n\n" + knowledge_base['def_inquietud'] + "\n\n" + knowledge_base['cats_inquietud'],
         [
             {'text': '📘 Ver guía', 'value': 'menu_guia'},
             {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
             {'text': '🔙 Menú Principal', 'value': 'menu'}
         ]),
        (r"\bcomo\s+hacer\s+una\s+denuncia\b|\bcomo\s+denunciar\b|\bquiero\s+denunciar\b",
         "Para realizar una denuncia, selecciona la opción '¡Quiero denunciar!' en el menú superior o desde aquí. Es seguro, puedes hacerlo de forma anónima y recibirás un folio y contraseña.",
         [
             {'text': '🚨 Ir a Denunciar', 'value': 'menu_denunciar'},
             {'text': '🔙 Menú Principal', 'value': 'menu'}
         ]),
        (r"\bcomo\s+consultar\s+mi\s+denuncia\b|\bconsultar\s+denuncia\b|\bestatus\s+de\s+mi\s+denuncia\b",
         "Para consultar, usa tu Folio y tu Contraseña en la sección 'Consultar denuncia'.",
         [
             {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
             {'text': '🔙 Menú Principal', 'value': 'menu'}
         ])
    ]

    for pattern, text, opts in qa_list:
        if re.search(pattern, message):
            response_data['response'] = text
            response_data['options'] = opts
            mem = request.session.get('chatbot_memory', [])
            mem.append({'q': message, 'intent': 'qa_direct'})
            request.session['chatbot_memory'] = mem
            return JsonResponse(response_data)

    from functools import lru_cache
    import os

    def strip_text(html):
        txt = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
        txt = re.sub(r'<style[\s\S]*?</style>', ' ', txt, flags=re.I)
        txt = re.sub(r'\{\%[\s\S]*?\%\}', ' ', txt)
        txt = re.sub(r'\{\{[\s\S]*?\}\}', ' ', txt)
        txt = re.sub(r'<[^>]+>', ' ', txt)
        txt = re.sub(r'\s+', ' ', txt)
        return txt.strip()

    @lru_cache(maxsize=1)
    def load_corpus():
        base = settings.BASE_DIR
        tpl_dir = os.path.join(base, 'templates', 'denuncias')
        files = [
            'public_guia.html',
            'index.html',
            'public_enviar_denuncia.html',
            'public_consultar_denuncia.html',
            'complaint_detail.html',
            'base_public.html'
        ]
        corpus = []
        for fn in files:
            path = os.path.join(tpl_dir, fn)
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        raw = f.read()
                    text = strip_text(raw)
                    corpus.append({'file': fn, 'text': text})
                except:
                    pass
        return corpus

    def split_sentences(text):
        text = re.sub(r'\s+', ' ', text).strip()
        parts = re.split(r'(?<=[\.!?])\s+', text)
        return [p.strip() for p in parts if p.strip()]

    def format_sentence(s):
        s = s.strip()
        if not s:
            return s
        s = s[0].upper() + s[1:]
        if s[-1] not in '.!?':
            s += '.'
        return s

    def polish_spanish(text):
        if not isinstance(text, str):
            return text
        repl = {
            ' mexico ': ' México ',
            'mexico ': 'México ',
            ' mexico': ' México',
            'contrasena': 'contraseña',
            'Contrasena': 'Contraseña',
            'anonimo': 'anónimo',
            'Anonimo': 'Anónimo'
        }
        lines = []
        for raw_line in text.split('\n'):
            line = re.sub(r'\s+', ' ', raw_line).strip()
            if not line:
                lines.append('')
                continue
            for a, b in repl.items():
                line = line.replace(a, b)
            polished = []
            for s in split_sentences(line):
                if re.search(r'[0-9A-Za-zÁÉÍÓÚÑáéíóúñ]$', s):
                    polished.append(format_sentence(s))
                else:
                    polished.append(s[0].upper() + s[1:] if s else s)
            lines.append(' '.join(polished))
        return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines))

    def retrieve_snippets(q, k=2):
        qn = normalize(q)
        corpus = load_corpus()
        scores = []
        words = qn.split()
        for doc in corpus:
            t = doc['text'].lower()
            s = 0
            for w in words:
                if len(w) > 3 and w in t:
                    s += 1
            if s == 0:
                import difflib
                ratios = [difflib.SequenceMatcher(None, w, t[:1000]).ratio() for w in words if len(w) > 3]
                s = sum(r for r in ratios if r > 0.4)
            if s > 0:
                scores.append((s, doc))
        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        def best_sentences(text, tokens, n=3):
            sents = split_sentences(text)
            scored = []
            for s in sents:
                sn = s.lower()
                score = 0
                for w in tokens:
                    if len(w) > 3 and w in sn:
                        score += 1
                if score > 0:
                    scored.append((score, s))
            if not scored:
                return sents[:n]
            scored.sort(key=lambda x: x[0], reverse=True)
            return [format_sentence(s) for _, s in scored[:n]]
        for _, doc in scores[:k]:
            sents = best_sentences(doc['text'], words)
            snippet = ' '.join(sents)
            results.append({'file': doc['file'], 'snippet': snippet})
        return results

    def get_denuncia_categories():
        cats = []
        for val, lab in Complaint.CATEGORY_CHOICES:
            cats.append(lab)
        return sorted(set(cats))

    def classify_category(q):
        qn = normalize(q)
        cats = get_denuncia_categories()
        matches = []
        for c in cats:
            cn = normalize(c).lower()
            score = 0
            for w in cn.split():
                if len(w) > 3 and w in qn:
                    score += 1
            if score > 0:
                matches.append((score, c))
        matches.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in matches[:3]]

    import difflib
    
    intents_map = {
        'menu_denunciar': {
            'keywords': ['denuncia', 'denunciar', 'reportar', 'reporte', 'queja', 'quejar', 'acusar', 'poner dedo', 'incidente', 'delito', 'falta', 'infraccion', 'testigo', 'victima', 'sucedio', 'paso algo', 'hacer denuncia', 'quiero reportar', 'iniciar queja', 'levantar reporte', 'informar', 'notificar', 'aviso', 'avisar'],
            'weight': 1
        },
        'menu_consultar': {
            'keywords': ['consultar', 'ver', 'checar', 'estatus', 'estado', 'seguimiento', 'como va', 'respuesta', 'avanzo', 'folio', 'numero de reporte', 'ticket', 'revisar', 'como va mi caso', 'respuesta denuncia', 'progreso', 'notificacion'],
            'weight': 1
        },
        'faq_password': {
            'keywords': ['contraseña', 'clave', 'password', 'pin', 'acceso', 'entrar', 'loguear', 'perdi', 'olvide', 'olvido', 'recuperar', 'recordar', 'no me acuerdo', 'restablecer', 'cambiar clave', 'no puedo entrar', 'clave perdida', 'no recuerdo', 'resetear'],
            'weight': 2 
        },
        'faq_human_contact': {
            'keywords': ['hablar con alguien', 'persona', 'humano', 'persona real', 'quien responde', 'quien lee', 'quien atiende', 'administrador', 'agente', 'asesor', 'chat en vivo', 'tiempo real', 'contacto humano', 'operador', 'telefonico', 'llamada'],
            'weight': 1.5
        },
        'faq_anonimato': {
            'keywords': ['anonimo', 'anónimo', 'nombre', 'identidad', 'quien soy', 'secreto', 'privado', 'confidencial', 'mis datos', 'personal', 'saber quien', 'oculto', 'escondido', 'ip', 'rastrear', 'descubrir', 'se sabra quien soy', 'doy mi nombre', 'seguro'],
            'weight': 1
        },
        'info_evidencia': {
            'keywords': ['evidencia', 'prueba', 'foto', 'video', 'archivo', 'documento', 'papel', 'adjuntar', 'subir', 'mandar', 'imagen', 'audio', 'grabacion', 'pdf', 'word', 'excel', 'captura', 'pruebas'],
            'weight': 1
        },
        'info_recomendaciones': {
            'keywords': ['recomendacion', 'recomendaciones', 'consejo', 'consejos', 'tip', 'tips', 'sugerencia', 'mejorar denuncia', 'como hacer denuncia', 'guia practica', 'seguridad', 'pasos'],
            'weight': 1
        },
        'faq_represalias': {
            'keywords': ['represalia', 'represalias', 'miedo', 'temor', 'venganza', 'castigo', 'consecuencia', 'despido', 'correr', 'jefe', 'problemas', 'meterme en problemas', 'seguro', 'proteccion', 'protegerme', 'sancion', 'afectar', 'desquitar'],
            'weight': 1
        },
        'info_proceso': {
            'keywords': ['tiempo', 'tarda', 'demora', 'cuando', 'dias', 'horas', 'respuesta', 'saber', 'paso', 'etapa', 'duracion', 'rapido', 'lento', 'proceso', 'investigacion', 'analisis', 'cuanto tiempo'],
            'weight': 1
        },
        'menu_biblioteca': {
            'keywords': ['biblioteca', 'documento', 'manual', 'guia', 'codigo', 'etica', 'politica', 'reglamento', 'pdf', 'leer', 'descargar', 'norma', 'regla', 'ley'],
            'weight': 1
        },
        'incident_alert': {
            'keywords': ['robo', 'hurto', 'acoso', 'acosa', 'acosado', 'acosando', 'sexual', 'laboral', 'fraude', 'dinero', 'soborno', 'mordida', 'corrupcion', 'discriminacion', 'racismo', 'golpe', 'violencia', 'amenaza', 'matar', 'herir', 'agresion', 'tocamiento', 'insulto', 'abus', 'abuso', 'abusado', 'director', 'jefe', 'gerente', 'hostigamiento', 'bullying', 'maltrato'],
            'weight': 3
        },
        'menu_otros': {
            'keywords': ['contacto', 'telefono', 'correo', 'email', 'llamar', 'celular', 'duda', 'pregunta', 'saber', 'informacion'],
            'weight': 0.5
        },
        'faq_users': {
            'keywords': ['quien puede', 'puedo denunciar', 'colaborador', 'proveedor', 'cliente', 'externo', 'usuario', 'quienes', 'para quien', 'aplica a mi', 'soy externo'],
            'weight': 1
        },
        'faq_rejected': {
            'keywords': ['no procede', 'rechazada', 'rechazo', 'desestimada', 'falsa', 'no valida', 'mentira', 'que pasa si no', 'consecuencias', 'invalida', 'descartada'],
            'weight': 1
        },
        'faq_modify': {
            'keywords': ['agregar mas', 'olvide adjuntar', 'subir mas', 'mas pruebas', 'mas evidencia', 'complementar', 'anadir', 'corregir', 'cambiar', 'modificar', 'editar'],
            'weight': 1
        },
        'faq_scope': {
            'keywords': ['que puedo denunciar', 'tipo de denuncia', 'temas', 'motivos', 'razones', 'ejemplos', 'casos', 'situaciones', 'robo hormiga', 'conflicto de interes', 'mal uso', 'categorias'],
            'weight': 1
        },
        'faq_denuncia_def': {
            'keywords': ['que es una denuncia', 'definicion de denuncia', 'significa denuncia', 'denuncia que es', 'que es denuncia', 'entiendo por denuncia', 'concepto denuncia'],
            'weight': 2
        },
        'faq_queja_def': {
            'keywords': ['que es una queja', 'definicion de queja', 'significa queja', 'queja que es', 'que es queja', 'entiendo por queja', 'concepto queja'],
            'weight': 2
        },
        'faq_inquietud_def': {
            'keywords': ['que es una inquietud', 'definicion de inquietud', 'significa inquietud', 'inquietud que es', 'que es inquietud', 'entiendo por inquietud', 'concepto inquietud'],
            'weight': 2
        },
        'faq_categorias_denuncia': {
            'keywords': ['tipos de denuncia', 'categorias de denuncia', 'que puedo denunciar', 'temas de denuncia', 'ejemplos denuncia'],
            'weight': 1.5
        },
        'faq_categorias_queja': {
            'keywords': ['tipos de queja', 'categorias de queja', 'motivos de queja', 'ejemplos queja'],
            'weight': 1.5
        },
        'faq_categorias_inquietud': {
            'keywords': ['tipos de inquietud', 'categorias de inquietud', 'temas de inquietud', 'ejemplos inquietud'],
            'weight': 1.5
        },
        'site_navegacion': {
            'keywords': ['secciones', 'que tiene la pagina', 'opciones del sitio', 'donde encuentro', 'apartados', 'menu del sitio', 'para que sirve cada', 'como funciona la pagina', 'que puedo hacer aqui', 'necesito ayuda', 'ayuda', 'no se usar'],
            'weight': 1.5
        },
        'site_folio': {
            'keywords': ['folio', 'formato del folio', 'numero de folio', 'empieza con gsi', 'prefijo gsi', 'donde esta mi folio', 'clave de seguimiento', 'ticket'],
            'weight': 2
        },
        'site_avisos_privacidad': {
            'keywords': ['aviso de privacidad', 'avisos de privacidad', 'privacidad', 'tratamiento de datos', 'cometra', 'grumer', 'seguritec', 'sepsa', 'tameme', 'tecnoval'],
            'weight': 1.5
        },
        'site_datos_personales': {
            'keywords': ['telefono o red', 'numero de empleado', 'matricula', 'solo numeros', 'numerico', '10 digitos', 'datos del denunciado', 'datos de contacto'],
            'weight': 2
        },
        'site_preguntas_adicionales': {
            'keywords': ['preguntas adicionales', 'preguntas extra', 'preguntas opcionales', 'contestar mas preguntas'],
            'weight': 2
        },
        'site_app': {
            'keywords': ['aplicacion movil', 'app', 'android', 'descargar app', 'celular', 'telefono movil', 'ios'],
            'weight': 1.5
        },
        'site_empresas': {
            'keywords': ['que empresas', 'empresas del grupo', 'companias', 'a que empresa', 'organizaciones participantes'],
            'weight': 1.5
        }
    }

    direct_commands = ['menu_denunciar', 'menu_consultar', 'menu_guia', 'menu_faq', 'menu_biblioteca', 'menu_otros', 
                       'info_derechos', 'info_proceso', 'info_evidencia', 'info_recomendaciones',
                       'faq_anonimato', 'faq_represalias', 'faq_password', 'faq_human_contact',
                       'faq_denuncia_def', 'faq_queja_def', 'faq_inquietud_def',
                       'faq_categorias_denuncia', 'faq_categorias_queja', 'faq_categorias_inquietud',
                       'site_navegacion', 'site_folio', 'site_avisos_privacidad', 'site_datos_personales',
                       'site_preguntas_adicionales', 'site_app', 'site_empresas']
    
    detected_intent = None
    
    if message in direct_commands:
        detected_intent = message
    else:
        scores = {}
        words = msg_norm.split()
        
        for intent, data in intents_map.items():
            score = 0
            for keyword in data['keywords']:
                keyword_norm = normalize(keyword)
                
                if keyword_norm in msg_norm: 
                    score += data['weight']
                    if len(keyword) > 4: score += 0.5
                else:
                    for word in words:
                        if len(keyword_norm) > 3 and len(word) > 3:
                            ratio = difflib.SequenceMatcher(None, keyword_norm, word).ratio()
                            if ratio > 0.85:
                                score += data['weight']
                                break
            
            if score > 0:
                scores[intent] = score
        
        if scores:
            detected_intent = max(scores, key=scores.get)
            if scores[detected_intent] < 0.6:
                detected_intent = None

    if (re.search(r"\bpreguntas\b", msg_norm) and re.search(r"\bfrecuentes\b", msg_norm)):
        detected_intent = 'menu_faq'
    if re.search(r"\bque\s+pue?do\s+reportar\b", msg_norm):
        detected_intent = 'faq_scope'
    time_kws = ['tiempo', 'dura', 'duracion', 'tarda', 'demora', 'horas', 'dias', 'investigacion']
    if any(kw in msg_norm for kw in time_kws):
        detected_intent = 'info_proceso'
    if re.search(r"(queja).*?(denuncia)|(denuncia).*?(queja)|como\s+se\s+si.*(queja|denuncia)", msg_norm):
        detected_intent = 'faq_queja_vs_denuncia'
    if re.search(r"que\s+hago\s+despues\s+de\s+consultar", msg_norm):
        detected_intent = 'after_consultar'
    
    if detected_intent == 'incident_alert':
        response_data['response'] = (
            "⚠️ Lo que mencionas parece ser un incidente delicado que debe ser tratado con seriedad.\n\n"
            "Te recomiendo encarecidamente ir a la sección **'¡Quiero denunciar!'** para formalizar el reporte. "
            "Nuestro equipo de ética investigará el caso confidencialmente."
        )
        response_data['options'] = [
            {'text': '🚨 Ir a Denunciar', 'value': 'menu_denunciar'},
            {'text': '💬 Hablar de otra cosa', 'value': 'menu'}
        ]

    elif detected_intent == 'menu_denunciar':
        response_data['response'] = (
            "Para realizar una denuncia, selecciona la opción **'¡Quiero denunciar!'** en el menú superior o haz clic abajo.\n\n"
            "• Es un proceso 100% seguro.\n"
            "• Puedes elegir hacerlo de forma **anónima**.\n"
            "• Recibirás un folio (inicia con GSI-) y una contraseña para consultar."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'menu_consultar':
        response_data['response'] = (
            "Para ver cómo va tu reporte, entra a **'Consultar denuncia'**.\n\n"
            "Necesitas:\n"
            "1. Tu **folio**, que siempre inicia con **GSI-**.\n"
            "2. Tu **contraseña**, la que se generó al enviar el reporte.\n\n"
            "Ahí podrás ver el **estatus del ticket**, revisar los **mensajes del investigador** y enviar información nueva cuando lo necesites."
        )
        response_data['options'] = [
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'faq_password':
        response_data['response'] = (
            "🔐 **Sobre la Contraseña:**\n"
            "Esta se genera automáticamente UNA sola vez al enviar tu denuncia.\n\n"
            "⚠️ **Importante:** Si elegiste el anonimato y perdiste tu contraseña, **NO** hay forma de recuperarla (por tu propia seguridad). Deberás crear un reporte nuevo."
        )
        response_data['options'] = [
            {'text': 'Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'faq_anonimato':
        response_data['response'] = (
            "🕵️ **Anonimato Garantizado:**\n"
            "Si seleccionas 'Anónimo', el sistema NO registra tu nombre, correo, ni dirección IP. "
            "Tu identidad está totalmente protegida y nadie podrá saber quién eres."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'info_evidencia':
        response_data['response'] = (
            "📂 **Guía de Evidencia Efectiva**\n\n"
            "Para que tu denuncia prospere, intenta responder estas preguntas en tu descripción:\n"
            "• **¿Qué?** Describe claramente los hechos.\n"
            "• **¿Quién?** Nombres de implicados y testigos.\n"
            "• **¿Cuándo?** Fechas y horas aproximadas.\n"
            "• **¿Dónde?** Lugar exacto del incidente.\n\n"
            "📎 **Archivos:** Puedes adjuntar varios archivos (fotos, videos, correos, audios o documentos). "
            "Formatos aceptados: PDF, DOC, DOCX, JPG, JPEG, PNG, GIF, TXT, RTF, ODT, ODS, ODP, XLS, XLSX, PPT y PPTX, "
            "con un máximo de 10MB por archivo."
        )
        response_data['options'] = [{'text': '🔙 Volver a Guía', 'value': 'menu_guia'}]

    elif detected_intent == 'faq_represalias':
        response_data['response'] = (
            "🛡️ **Cero Represalias:**\n"
            "Nuestra política prohíbe estrictamente cualquier castigo, amenaza o represalia contra quien denuncia de buena fe.\n\n"
            "Si sientes que estás siendo víctima de represalias, repórtalo inmediatamente."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'info_proceso':
        response_data['response'] = (
            "🔄 **El Proceso de Denuncia**\n\n"
            "1. **Envío:** Llenas el formulario (anónimo o con datos) y recibes un folio y contraseña.\n"
            "2. **Análisis (24-48h):** El Comité de Ética revisa si la denuncia cumple los criterios para ser admitida.\n"
            "3. **Investigación:** Se recaban pruebas y realizan entrevistas. El tiempo varía según la complejidad.\n"
            "4. **Resolución:** Se toman medidas correctivas y se cierra el caso. Se te notificará el resultado.\n\n"
            "💡 *Tip: Usa tu folio para consultar avances periódicamente.*"
        )
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '📘 Ver guía', 'value': 'menu_guia'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'menu_biblioteca':
        response_data['response'] = (
            "En la **Biblioteca** (menú superior) puedes leer y descargar:\n"
            "• Código de Ética\n"
            "• Política de Denuncias\n"
            "• Manuales de Usuario"
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'faq_queja_vs_denuncia':
        response_data['response'] = (
            "Para decidir entre **Queja** y **Denuncia**:\n\n"
            "• **Queja:** Inconformidades sobre servicios, procesos o condiciones laborales (ambiente, deficiencias).\n"
            "• **Denuncia:** Conductas no éticas o incumplimientos (fraude, acoso, discriminación, seguridad de la información, etc.).\n\n"
            "Si describes el caso, puedo sugerirte la categoría más adecuada."
        )
        response_data['options'] = [
            {'text': '📝 Ir a Denunciar', 'value': 'menu_denunciar'},
            {'text': '📘 Ver guía', 'value': 'menu_guia'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'after_consultar':
        response_data['response'] = (
            "Después de **consultar tu estado** puedes:\n\n"
            "1) **Agregar información o evidencia** si tienes nuevos datos.\n"
            "2) **Dejar una nota** para el comité si deseas aclarar algo.\n"
            "3) **Solicitar contacto** indicando tu preferencia de comunicación.\n\n"
            "Usa tu folio y contraseña para realizar estas acciones desde el portal."
        )
        response_data['options'] = [
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '📘 Ver guía', 'value': 'menu_guia'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'menu_otros':
        response_data['response'] = (
            "Si tienes una duda general o administrativa, también puedes enviarla por el canal.\n"
            "Si prefieres hablar con alguien, puedes dejar tus datos de contacto en el formulario (opcional)."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'faq_human_contact':
        response_data['response'] = (
            "👤 **Atención personalizada:**\n"
            "Este canal no es un chat en tiempo real. Las denuncias y consultas son recibidas por administradores asignados (Comité de Ética) que revisan cada caso.\n\n"
            "Si deseas hablar con alguien, envía tu reporte e indica que solicitas contacto. Nos comunicaremos contigo a través del sistema de mensajería del folio."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'faq_users':
        response_data['response'] = (
            "👥 **¿Quién puede denunciar?**\n"
            "El canal está abierto para:\n"
            "• Colaboradores y empleados.\n"
            "• Proveedores y contratistas.\n"
            "• Clientes y público en general."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'faq_rejected':
        response_data['response'] = (
            "❌ **¿Qué pasa si mi denuncia no procede?**\n"
            "Si la investigación determina que no hubo falta o no hay pruebas suficientes, el caso se cerrará.\n"
            "Siempre recibirás una explicación en el portal de consulta.\n"
            "Recuerda: NO habrá represalias por denunciar de buena fe, aunque no proceda."
        )
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'faq_modify':
        response_data['response'] = (
            "📝 **Agregar información:**\n"
            "Puedes complementar tu denuncia en cualquier momento:\n"
            "1. Entra a **'Consultar denuncia'**.\n"
            "2. Usa tu folio y contraseña.\n"
            "3. Agrega notas o sube nuevos archivos."
        )
        response_data['options'] = [
            {'text': '🔍 Consultar ahora', 'value': 'menu_consultar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'faq_scope':
        cats = get_denuncia_categories()
        listing = "\n".join([f"• {c}" for c in cats])
        response_data['response'] = ("📋 **¿Qué se puede denunciar?**\n" + listing)
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'menu_guia':
        response_data['response'] = (
            "📘 **Guía de Denuncias y Recomendaciones**\n\n"
            "Este recurso te ayuda a reportar de manera efectiva y segura. "
            "Explora los temas para conocer tus derechos, entender el proceso y saber cómo aportar pruebas."
        )
        response_data['options'] = [
            {'text': '⚖️ Derechos', 'value': 'info_derechos'},
            {'text': '🔄 Proceso paso a paso', 'value': 'info_proceso'},
            {'text': '📂 Tips de Evidencia', 'value': 'info_evidencia'},
            {'text': '💡 Recomendaciones', 'value': 'info_recomendaciones'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'info_recomendaciones':
        response_data['response'] = (
            "💡 **Recomendaciones de Seguridad y Calidad**\n\n"
            "• **Protege tu Folio:** Es tu única llave de acceso. Guárdalo en un lugar seguro.\n"
            "• **Sé Detallado:** Entre más contexto des, más fácil será investigar.\n"
            "• **Usa un Equipo Seguro:** Si denuncias algo sensible, prefiere usar un dispositivo personal.\n"
            "• **Mantente Atento:** Revisa el portal periódicamente; podríamos pedirte más información."
        )
        response_data['options'] = [{'text': '🔙 Volver a Guía', 'value': 'menu_guia'}]

    elif detected_intent == 'menu_faq':
        response_data['response'] = "Estas son las preguntas más comunes:"
        response_data['options'] = [
            {'text': '¿Es anónimo?', 'value': 'faq_anonimato'},
            {'text': '¿Hay represalias?', 'value': 'faq_represalias'},
            {'text': 'Olvidé contraseña', 'value': 'faq_password'},
            {'text': '🔙 Menú', 'value': 'menu'}
        ]

    elif detected_intent == 'info_derechos':
        response_data['response'] = (
            "⚖️ **Tus Derechos y Garantías**\n\n"
            "Al utilizar este canal, la organización te garantiza:\n"
            "• **Confidencialidad Absoluta:** Tu identidad será protegida en todo momento.\n"
            "• **No Represalias:** Está prohibida cualquier acción en tu contra por denunciar de buena fe.\n"
            "• **Investigación Justa:** Tu caso será analizado por un comité ético imparcial.\n"
            "• **Transparencia:** Podrás consultar el estatus de tu caso siempre."
        )
        response_data['options'] = [{'text': '🔙 Volver a Guía', 'value': 'menu_guia'}]

    elif detected_intent == 'faq_denuncia_def':
        response_data['response'] = (
            "Definición de denuncia:\n\n" + knowledge_base['def_denuncia'] + "\n\n" + knowledge_base['cats_denuncia']
        )
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]
    elif detected_intent == 'faq_queja_def':
        response_data['response'] = (
            "Definición de queja:\n\n" + knowledge_base['def_queja'] + "\n\n" + knowledge_base['cats_queja']
        )
        response_data['options'] = [
            {'text': '📝 Ir a Denunciar', 'value': 'menu_denunciar'},
            {'text': '📘 Ver guía', 'value': 'menu_guia'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]
    elif detected_intent == 'faq_inquietud_def':
        response_data['response'] = (
            "Definición de inquietud:\n\n" + knowledge_base['def_inquietud'] + "\n\n" + knowledge_base['cats_inquietud']
        )
        response_data['options'] = [
            {'text': '📘 Ver guía', 'value': 'menu_guia'},
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]
    elif detected_intent == 'faq_categorias_denuncia':
        response_data['response'] = knowledge_base['cats_denuncia']
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]
    elif detected_intent == 'faq_categorias_queja':
        response_data['response'] = knowledge_base['cats_queja']
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]
    elif detected_intent == 'faq_categorias_inquietud':
        response_data['response'] = knowledge_base['cats_inquietud']
        response_data['options'] = [{'text': '🔙 Menú Principal', 'value': 'menu'}]

    elif detected_intent == 'site_navegacion':
        response_data['response'] = (
            "🧭 **Qué puedes hacer en este canal**\n"
            "• **¡Quiero denunciar!**: registrar una denuncia o una inquietud.\n"
            "• **Consultar denuncia**: ver tu estatus, el estatus del ticket y los mensajes del investigador.\n"
            "• **Guía de uso**: cómo llenar el formulario y cuándo es Inquietud o Denuncia.\n"
            "• **Preguntas frecuentes**: dudas sobre anonimato, contraseña y tiempos.\n"
            "• **Biblioteca GSI**: documentos, avisos de privacidad, infografías y novedades.\n\n"
            "¿Sobre cuál de estas secciones quieres orientación?"
        )
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '📘 Guía de uso', 'value': 'menu_guia'},
            {'text': '📚 Biblioteca GSI', 'value': 'menu_biblioteca'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'site_folio':
        response_data['response'] = (
            "🔖 **Tu folio y tu contraseña**\n"
            "Al enviar tu reporte el sistema genera un folio que **siempre inicia con GSI-** (por ejemplo, GSI-2026-0001), junto con una contraseña de consulta.\n"
            "• El folio es el identificador de tu ticket y con él consultas el estatus.\n"
            "• En el portal, el campo ya trae el prefijo GSI- para que solo escribas el consecutivo.\n"
            "• Guarda folio y contraseña: son tu única llave de acceso.\n"
            "• Si pierdes la contraseña de un reporte anónimo no se puede recuperar; tendrías que crear uno nuevo."
        )
        response_data['options'] = [
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'site_avisos_privacidad':
        response_data['response'] = (
            "🔒 **Avisos de privacidad**\n"
            "En la sección **Avisos y consentimientos** del formulario puedes leer y aceptar el aviso que corresponde a tu empresa:\n"
            "• Aviso de privacidad COMETRA\n"
            "• Aviso de privacidad GRUMER\n"
            "• Aviso de privacidad SEGURITEC\n"
            "• Aviso de privacidad SEPSA\n"
            "• Aviso de privacidad TAMEME\n"
            "• Aviso de privacidad TECNOVAL\n\n"
            "Al aceptar el aviso de tu empresa tu reporte queda registrado conforme al tratamiento de datos personales aplicable. También puedes consultarlos en la Biblioteca GSI."
        )
        response_data['options'] = [
            {'text': '🚨 Ir al formulario', 'value': 'menu_denunciar'},
            {'text': '📚 Biblioteca GSI', 'value': 'menu_biblioteca'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'site_datos_personales':
        response_data['response'] = (
            "📇 **Datos de contacto y del denunciado**\n"
            "• **Teléfono o Red**: solo números, hasta 10 dígitos.\n"
            "• **Número de empleado** del denunciante: solo números, hasta 10 dígitos.\n"
            "• **Matrícula del denunciado**: solo números, hasta 10 dígitos.\n\n"
            "El sistema no acepta letras ni símbolos en estos campos. Si eliges enviar tu reporte como **Anónimo**, no se solicitan tus datos personales."
        )
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'site_preguntas_adicionales':
        response_data['response'] = (
            "➕ **Preguntas adicionales**\n"
            "Primero el sistema te pregunta **si deseas contestarlas**:\n"
            "• **Sí, responder**: se despliegan las preguntas extra (si el hecho se repite, riesgo inmediato, reportes previos, medio de contacto, autorización para compartir detalles y notas de impacto).\n"
            "• **No por ahora**: se omiten y puedes enviar tu reporte directamente.\n\n"
            "Son opcionales; contestarlas ayuda a que la investigación sea más precisa."
        )
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '📘 Ver guía', 'value': 'menu_guia'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'site_app':
        response_data['response'] = (
            "📱 **Aplicación móvil**\n"
            "La app del canal permite:\n"
            "• Enviar una denuncia o inquietud.\n"
            "• Consultar tu folio y ver el **estatus del ticket**.\n"
            "• Mantener disponible el **chat con el investigador** en todo momento para agregar información.\n\n"
            "Usa el mismo folio y contraseña que en la versión web."
        )
        response_data['options'] = [
            {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    elif detected_intent == 'site_empresas':
        response_data['response'] = (
            "🏢 **Empresas que usan el canal**\n"
            "El canal atiende reportes de las seis empresas del grupo:\n"
            "• COMETRA\n• GRUMER\n• SEGURITEC\n• SEPSA\n• TAMEME\n• TECNOVAL\n\n"
            "Cada una cuenta con su propio aviso de privacidad, disponible en el formulario y en la Biblioteca GSI."
        )
        response_data['options'] = [
            {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
            {'text': '📚 Biblioteca GSI', 'value': 'menu_biblioteca'},
            {'text': '🔙 Menú Principal', 'value': 'menu'}
        ]

    else:
        time_kws = ['tiempo', 'dura', 'duracion', 'tarda', 'demora', 'horas', 'dias', 'investigacion']
        if any(kw in msg_norm for kw in time_kws):
            response_data['response'] = (
                "🔄 **Duración y etapas de una denuncia**\n\n"
                "• **Análisis inicial:** 24–48 horas para admitir a trámite.\n"
                "• **Investigación:** Varía según complejidad y disponibilidad de pruebas/testigos.\n"
                "• **Resolución:** Se toman medidas y se cierra el caso; puedes consultar avances con tu folio."
            )
            response_data['options'] = [
                {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
                {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
                {'text': '📘 Ver guía', 'value': 'menu_guia'},
                {'text': '🔙 Menú Principal', 'value': 'menu'}
            ]
    
        elif 'queja' in msg_norm:
             response_data['response'] = (
                "Veo que mencionas una **Queja**. Aquí tienes la definición oficial:\n\n" + 
                knowledge_base['def_queja'] + "\n\n" + 
                knowledge_base['cats_queja'] + 
                "\n\n¿Deseas registrar una?"
            )
             response_data['options'] = [
                {'text': '📝 Registrar Queja', 'value': 'menu_denunciar'},
                {'text': '🔙 Menú Principal', 'value': 'menu'}
            ]
        elif 'inquietud' in msg_norm:
             response_data['response'] = (
                "Sobre las **Inquietudes**:\n\n" + 
                knowledge_base['def_inquietud'] + "\n\n" + 
                knowledge_base['cats_inquietud'] + 
                "\n\n¿Te gustaría consultar la guía?"
            )
             response_data['options'] = [
                {'text': '📘 Ver guía', 'value': 'menu_guia'},
                {'text': '🔙 Menú Principal', 'value': 'menu'}
            ]
        elif 'denuncia' in msg_norm:
             response_data['response'] = (
                "Respecto a la **Denuncia**:\n\n" + 
                knowledge_base['def_denuncia'] + "\n\n" + 
                knowledge_base['cats_denuncia'] + 
                "\n\n¿Deseas realizar una?"
            )
             response_data['options'] = [
                {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
                {'text': '🔙 Menú Principal', 'value': 'menu'}
            ]

        else:
            cat_matches = classify_category(message)
            if cat_matches:
                listing = "\n".join([f"• {c}" for c in cat_matches])
                response_data['response'] = ("Según lo que describes, tu caso podría clasificarse como:\n\n" + listing + "\n\nSi deseas formalizar el reporte, usa 'Quiero denunciar'.")
                response_data['options'] = [
                    {'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'},
                    {'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'},
                    {'text': '📘 Ver guía', 'value': 'menu_guia'},
                    {'text': '🔙 Menú Principal', 'value': 'menu'}
                ]
            else:
                snippets = retrieve_snippets(message, k=2)
                if snippets:
                    snippet_text = "\n\n".join(s['snippet'] for s in snippets)
                    response_data['response'] = (
                        "Encontré esta información en nuestra guía que podría ayudarte:\n\n" + 
                        snippet_text
                    )
                    recommended = []
                    for s in snippets:
                        fn = s['file']
                        if 'enviar_denuncia' in fn or 'index' in fn:
                            recommended.append({'text': '🚨 Quiero denunciar', 'value': 'menu_denunciar'})
                        if 'consultar' in fn:
                            recommended.append({'text': '🔍 Consultar denuncia', 'value': 'menu_consultar'})
                        if 'guia' in fn:
                            recommended.append({'text': '📘 Ver guía', 'value': 'menu_guia'})
                        if 'biblioteca' in fn:
                            recommended.append({'text': '📚 Biblioteca', 'value': 'menu_biblioteca'})
                    
                    seen = set()
                    filtered = []
                    for o in recommended:
                        key = o['value']
                        if key not in seen:
                            seen.add(key)
                            filtered.append(o)
                    if not filtered:
                        filtered = main_menu[:3]
                        
                    response_data['options'] = filtered + [{'text': '🔙 Menú Principal', 'value': 'menu'}]
                else:
                    response_data['response'] = (
                        "No encontré una respuesta exacta para eso, pero puedo orientarte sobre estos temas del canal:\n\n"
                        "• Cómo usar cada sección del sitio\n"
                        "• Tu folio (inicia con GSI-) y tu contraseña\n"
                        "• Avisos de privacidad de las empresas\n"
                        "• Datos de contacto y del denunciado\n"
                        "• Preguntas adicionales del formulario\n"
                        "• Evidencia y formatos permitidos\n"
                        "• Estatus del ticket y mensajes del investigador\n"
                        "• Aplicación móvil\n\n"
                        "Elige una opción o reformula tu pregunta con otras palabras."
                    )
                    response_data['options'] = [
                        {'text': '🧭 Secciones del sitio', 'value': 'site_navegacion'},
                        {'text': '🔖 Folio y contraseña', 'value': 'site_folio'},
                        {'text': '🔒 Avisos de privacidad', 'value': 'site_avisos_privacidad'},
                        {'text': '📇 Datos de contacto', 'value': 'site_datos_personales'},
                        {'text': '➕ Preguntas adicionales', 'value': 'site_preguntas_adicionales'},
                        {'text': '📎 Evidencia', 'value': 'info_evidencia'},
                        {'text': '📱 App móvil', 'value': 'site_app'},
                        {'text': '🔙 Menú Principal', 'value': 'menu'}
                    ]
    try:
        url_map = {
            'menu_denunciar': reverse('denuncias:submit_complaint'),
            'menu_consultar': reverse('denuncias:lookup_complaint'),
            'menu_guia': reverse('denuncias:guide'),
            'menu_faq': reverse('denuncias:faq'),
            'menu_biblioteca': reverse('denuncias:updates')
        }
        if response_data.get('options'):
            for opt in response_data['options']:
                val = opt.get('value')
                if val in url_map:
                    opt['url'] = url_map[val]
    except Exception:
        pass

    if response_data.get('response'):
        response_data['response'] = polish_spanish(response_data['response'])
    mem = request.session.get('chatbot_memory', [])
    mem.append({'q': message, 'intent': detected_intent or 'unknown'})
    request.session['chatbot_memory'] = mem
    return JsonResponse(response_data)

def settings_view(request):
    return redirect('denuncias:admin_settings')

ISO_PROCEDURE_STEPS = [
    {'field': 'step_recepcion', 'n': 1, 'title': 'Recepción y registro',
     'desc': 'Toda denuncia, queja o inquietud se registra de forma trazable con folio, fecha y canal de entrada.',
     'ref': 'ISO 37301 · 8.4 Comunicación / 7.5 Información documentada'},
    {'field': 'step_admisibilidad', 'n': 2, 'title': 'Admisibilidad y triaje',
     'desc': 'Se evalúa si el asunto es competencia del sistema de cumplimiento y se clasifica por gravedad y riesgo.',
     'ref': 'ISO 37301 · 4.1 y 6.1 Enfoque basado en riesgos'},
    {'field': 'step_designacion', 'n': 3, 'title': 'Designación del equipo investigador',
     'desc': 'Se nombra al responsable o equipo con competencia, autoridad y recursos suficientes para investigar.',
     'ref': 'ISO 37301 · 5.3 Roles, responsabilidades y autoridades / 7.2 Competencia'},
    {'field': 'step_independencia', 'n': 4, 'title': 'Independencia y conflicto de interés',
     'desc': 'Se verifica la ausencia de conflicto de interés y la imparcialidad de quien investiga.',
     'ref': 'ISO 37301 · 5.1 Liderazgo y compromiso'},
    {'field': 'step_plan', 'n': 5, 'title': 'Plan de investigación documentado',
     'desc': 'Se define objetivo, alcance, metodología, actividades, plazos y fechas clave.',
     'ref': 'ISO 37301 · 7.5 Información documentada / 8.1 Planificación y control operacional'},
    {'field': 'step_evidencias', 'n': 6, 'title': 'Recolección y preservación de evidencia',
     'desc': 'Se obtienen, protegen y custodian las evidencias documentales, digitales y testimoniales.',
     'ref': 'ISO 37301 · 8.1 Control operacional'},
    {'field': 'step_analisis', 'n': 7, 'title': 'Análisis de evidencia y hallazgos',
     'desc': 'La evidencia se analiza y se documentan los hallazgos con su grado de confirmación y riesgo.',
     'ref': 'ISO 37301 · 9.1 Seguimiento, medición, análisis y evaluación'},
    {'field': 'step_causa_raiz', 'n': 8, 'title': 'Análisis de causa raíz',
     'desc': 'Se determina la causa raíz del incumplimiento para evitar su recurrencia.',
     'ref': 'ISO 37301 · 10.2 No conformidad y acción correctiva'},
    {'field': 'step_conclusion', 'n': 9, 'title': 'Conclusión de la investigación',
     'desc': 'Se emite la determinación fundada, parcialmente fundada, no fundada o no concluyente.',
     'ref': 'ISO 37301 · 8.4 / 9.1'},
    {'field': 'step_acciones', 'n': 10, 'title': 'Acciones correctivas y no represalia',
     'desc': 'Se definen acciones correctivas, disciplinarias y garantías de no represalia para el denunciante.',
     'ref': 'ISO 37301 · 10.1 Mejora / 10.2 Acción correctiva'},
    {'field': 'step_seguimiento', 'n': 11, 'title': 'Seguimiento y verificación de eficacia',
     'desc': 'Se verifica que las acciones implementadas sean eficaces y se monitorea el cierre.',
     'ref': 'ISO 37301 · 9.1 Seguimiento y medición / 10.2'},
    {'field': 'step_cierre', 'n': 12, 'title': 'Cierre y conservación de registros',
     'desc': 'El expediente se cierra y la información documentada se conserva con controles de confidencialidad.',
     'ref': 'ISO 37301 · 7.5 Información documentada'},
]

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_complaint_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    if not request.user.is_superuser and not is_delegador:
        if complaint.assigned_to != request.user:
            messages.error(request, 'No tienes permiso para ver esta denuncia.')
            return redirect('denuncias:admin_dashboard')

    plan, _ = InvestigationPlan.objects.get_or_create(complaint=complaint)
    report, _ = CaseReport.objects.get_or_create(complaint=complaint)
    procedure, _ = InvestigationProcedure.objects.get_or_create(complaint=complaint)
    try:
        procedure = apply_iso_protocol(complaint)
    except Exception:
        pass

    plan_form = InvestigationPlanForm(instance=plan)
    evidence_form = EvidenceItemForm()
    finding_form = FindingForm()
    report_form = CaseReportForm(instance=report)
    procedure_form = InvestigationProcedureForm(instance=procedure)

    iso_checklist = []
    for step in ISO_PROCEDURE_STEPS:
        iso_checklist.append({
            'n': step['n'],
            'title': step['title'],
            'desc': step['desc'],
            'ref': step['ref'],
            'field': procedure_form[step['field']],
            'checked': bool(getattr(procedure, step['field'])),
        })

    protocol_family = procedure.protocol_family or resolve_incident_family(complaint.category or '')
    protocol_family_label = FAMILY_LABELS.get(protocol_family, FAMILY_LABELS['general'])
    iso_extra_checklist = []
    base_count = len(ISO_PROCEDURE_STEPS)
    for idx, step in enumerate(procedure.extra_steps or [], start=1):
        checked = bool(step.get('done'))
        key = step.get('key', '')
        iso_extra_checklist.append({
            'n': base_count + idx,
            'key': key,
            'title': step.get('title', ''),
            'desc': step.get('desc', ''),
            'ref': step.get('ref', ''),
            'checked': checked,
            'field': format_html(
                '<input type="checkbox" name="extra_step_{}"{}>',
                key,
                ' checked' if checked else '',
            ),
        })

    if request.method == 'POST':
        if 'update_status' in request.POST and not is_delegador:
            form = ComplaintResponseForm(request.POST, instance=complaint)
            if form.is_valid():
                form.save()
                messages.success(request, 'Denuncia actualizada correctamente.')
                
                try:
                    ComplaintLog.objects.create(
                        complaint=complaint,
                        user=request.user,
                        action='status_change',
                        details=f"Estado: {complaint.get_status_display()}, Categoría: {complaint.get_category_display()}"
                    )
                except: pass
                return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)
        elif 'update_status' in request.POST and is_delegador:
            messages.error(request, 'El Delegador no puede modificar estados manualmente.')
            return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)
        
        elif 'accept' in request.POST and is_delegador and complaint.status == 'enviado':
            User = get_user_model()
            assign_user_id = (request.POST.get('assign_to') or '').strip()
            assign_area = (request.POST.get('assign_area') or '').strip()
            delegador_severity = (request.POST.get('delegador_severity') or '').strip()
            assignee = None
            if assign_user_id:
                try:
                    candidate = User.objects.filter(is_staff=True, is_active=True).get(id=assign_user_id)
                    assignee = candidate
                except User.DoesNotExist:
                    assignee = None
            if not assignee:
                qs = User.objects.filter(is_staff=True, is_active=True).exclude(username='Delegador')
                if assign_area:
                    qs = qs.filter(area=assign_area)
                assignee = qs.order_by('assignment_position', 'id').first()
            complaint.status = 'admitido'
            if delegador_severity in dict(Complaint.SEVERITY_CHOICES):
                complaint.severity = delegador_severity
            if assignee:
                complaint.assigned_to = assignee
            if assign_area:
                complaint.actor_area = assign_area
            complaint.save(update_fields=['status', 'assigned_to', 'actor_area', 'severity'])
            messages.success(request, 'Denuncia admitida y asignada para trámite.')
            try:
                ComplaintLog.objects.create(
                    complaint=complaint,
                    user=request.user,
                    action='delegador_accept',
                    details=f"Admitida y asignada a: {assignee.get_full_name() or assignee.username if assignee else 'sin asignar'}"
                )
            except: pass
            try:
                _notify_admin_assigned(request, complaint, assignee) if assignee else None
            except: pass
            return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)
        
        elif 'reject' in request.POST and is_delegador and complaint.status == 'enviado':
            reason = (request.POST.get('reject_reason') or '').strip()
            complaint.status = 'rechazado'
            complaint.save(update_fields=['status'])
            messages.success(request, 'Denuncia rechazada.')
            try:
                ComplaintLog.objects.create(
                    complaint=complaint,
                    user=request.user,
                    action='delegador_reject',
                    details=(reason or 'Sin motivo especificado')
                )
            except: pass
            return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)
        
        elif 'delegador_update_severity' in request.POST and is_delegador and complaint.status == 'enviado':
            new_sev = (request.POST.get('delegador_severity') or '').strip()
            if new_sev in dict(Complaint.SEVERITY_CHOICES):
                complaint.severity = new_sev
                complaint.save(update_fields=['severity'])
                messages.success(request, 'Gravedad actualizada por el Delegador.')
                try:
                    ComplaintLog.objects.create(
                        complaint=complaint,
                        user=request.user,
                        action='delegador_severity',
                        details=f"Gravedad establecida en: {dict(Complaint.SEVERITY_CHOICES).get(new_sev)}"
                    )
                except: pass
            else:
                messages.error(request, 'Gravedad inválida.')
            return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)
        
        elif 'assign_user' in request.POST and (request.user.is_superuser or is_delegador):
            user_id = request.POST.get('assigned_to')
            if user_id:
                User = get_user_model()
                try:
                    assignee = User.objects.get(id=user_id)
                    complaint.assigned_to = assignee
                    complaint.save()
                    messages.success(request, f'Reporte asignado a {assignee.get_full_name() or assignee.username}')
                    
                    try:
                        ComplaintLog.objects.create(
                            complaint=complaint,
                            user=request.user,
                            action='assignment',
                            details=f"Asignado a: {assignee.get_full_name() or assignee.username}"
                        )
                    except: pass
                except User.DoesNotExist:
                    messages.error(request, 'Usuario no encontrado.')
            return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

        elif 'submit_plan' in request.POST:
            plan_form = InvestigationPlanForm(request.POST, instance=plan)
            if plan_form.is_valid():
                plan_form.save()
                messages.success(request, 'Plan de investigación actualizado.')
                return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

        elif 'add_evidence' in request.POST:
            evidence_form = EvidenceItemForm(request.POST, request.FILES)
            if evidence_form.is_valid():
                ev = evidence_form.save(commit=False)
                ev.complaint = complaint
                ev.uploaded_by = request.user
                ev.save()
                build_preview(ev)
                messages.success(request, 'Evidencia agregada.')
                return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

        elif 'add_finding' in request.POST:
            finding_form = FindingForm(request.POST)
            if finding_form.is_valid():
                fi = finding_form.save(commit=False)
                fi.complaint = complaint
                fi.created_by = request.user
                fi.save()
                messages.success(request, 'Hallazgo registrado.')
                return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

        elif 'submit_report' in request.POST:
            report_form = CaseReportForm(request.POST, instance=report)
            if report_form.is_valid():
                report_form.save()
                messages.success(request, 'Informe del caso actualizado.')
                return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

        elif 'submit_procedure' in request.POST:
            procedure_form = InvestigationProcedureForm(request.POST, instance=procedure)
            if procedure_form.is_valid():
                procedure = procedure_form.save()
                updated_steps = []
                for step in (procedure.extra_steps or []):
                    item = dict(step)
                    item['done'] = ('extra_step_%s' % item.get('key', '')) in request.POST
                    updated_steps.append(item)
                procedure.extra_steps = updated_steps
                procedure.save(update_fields=['extra_steps'])
                messages.success(request, 'Procedimiento ISO 37301 actualizado.')
                return redirect('denuncias:admin_complaint_detail', complaint_id=complaint.id)

    chat_messages = ChatMessage.objects.filter(complaint=complaint).order_by('created_at')
    logs = ComplaintLog.objects.filter(complaint=complaint).order_by('-timestamp')
    reporter_notes = ReporterNote.objects.filter(complaint=complaint).order_by('-created_at')
    attachments = ComplaintAttachment.objects.filter(complaint=complaint)
    
    evidences = EvidenceItem.objects.filter(complaint=complaint).order_by('-obtained_at')
    findings = Finding.objects.filter(complaint=complaint).order_by('-created_at')
    
    response_form = ComplaintResponseForm(instance=complaint)
    chat_form = ChatMessageForm()
    
    User = get_user_model()
    assignable_users = User.objects.filter(is_staff=True, is_active=True).exclude(id=request.user.id)

    context = {
        'complaint': complaint,
        'chat_messages': chat_messages,
        'logs': logs,
        'reporter_notes': reporter_notes,
        'attachments': attachments,
        'response_form': response_form,
        'chat_form': chat_form,
        'assignable_users': assignable_users,
        'is_delegador': is_delegador,
        'severity_choices': Complaint.SEVERITY_CHOICES,
        'plan_form': plan_form,
        'evidence_form': evidence_form,
        'finding_form': finding_form,
        'report_form': report_form,
        'procedure': procedure,
        'procedure_form': procedure_form,
        'iso_checklist': iso_checklist,
        'iso_extra_checklist': iso_extra_checklist,
        'protocol_family_label': protocol_family_label,
        'evidences': evidences,
        'findings': findings,
    }
    return render(request, 'denuncias/complaint_detail.html', context)

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_settings(request):
    User = get_user_model()
    investigation_complaints = (
        Complaint.objects.select_related('assigned_to', 'investigation_plan', 'case_report')
        .prefetch_related('evidence_items', 'findings')
        .order_by('-created_at')
    )
    context = {
        'total_complaints': Complaint.objects.count(),
        'total_routes_tracked': PageViewStat.objects.count(),
        'total_superusers': User.objects.filter(is_superuser=True).count(),
        'staff_admins': User.objects.filter(is_staff=True, is_superuser=False).count(),
        'investigation_complaints': investigation_complaints,
    }
    return render(request, 'denuncias/admin_settings.html', context)

MONTH_NAMES_ES = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

def _local_dt(value):
    if value is None:
        return None
    return timezone.localtime(value) if timezone.is_aware(value) else value

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_sessions(request):
    User = get_user_model()
    users = list(User.objects.filter(is_staff=True).order_by('username').distinct())

    selected_user = None
    selected_user_id = (request.GET.get('user') or '').strip()
    if selected_user_id:
        try:
            selected_user = User.objects.get(id=int(selected_user_id), is_staff=True)
        except (User.DoesNotExist, ValueError, TypeError):
            selected_user = None

    today = timezone.localdate()
    month_param = (request.GET.get('month') or '').strip()
    try:
        year, month = (int(part) for part in month_param.split('-'))
        if not (1 <= month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        year, month = today.year, today.month

    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])

    all_month = list(
        UserSessionAudit.objects.select_related('user')
        .filter(login_at__date__gte=month_start, login_at__date__lte=month_end)
        .order_by('login_at')
    )
    scoped = [a for a in all_month if not selected_user or a.user_id == selected_user.id]

    day_map = {}
    total_seconds = 0
    open_sessions = 0
    for audit in scoped:
        local_login = _local_dt(audit.login_at)
        if not local_login:
            continue
        entry = day_map.setdefault(local_login.date(), {'count': 0, 'seconds': 0})
        entry['count'] += 1
        entry['seconds'] += audit.duration_seconds
        total_seconds += audit.duration_seconds
        if audit.is_active:
            open_sessions += 1

    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        row = []
        for day in week:
            info = day_map.get(day, {'count': 0, 'seconds': 0})
            row.append({
                'date': day,
                'in_month': day.month == month,
                'is_today': day == today,
                'count': info['count'],
                'duration': _format_duration(info['seconds']) if info['seconds'] else '',
            })
        weeks.append(row)

    closed_count = sum(1 for a in scoped if a.logout_at)
    avg_seconds = int(total_seconds / closed_count) if closed_count else 0

    per_user = {}
    for audit in all_month:
        key = audit.user_id
        bucket = per_user.setdefault(key, {'user': audit.user, 'count': 0, 'seconds': 0})
        bucket['count'] += 1
        bucket['seconds'] += audit.duration_seconds
    user_summary = sorted(per_user.values(), key=lambda r: r['seconds'], reverse=True)

    recent_qs = UserSessionAudit.objects.select_related('user')
    if selected_user:
        recent_qs = recent_qs.filter(user=selected_user)
    recent_rows = []
    for audit in recent_qs.order_by('-login_at')[:40]:
        recent_rows.append({
            'user': audit.user,
            'login_at': _local_dt(audit.login_at),
            'logout_at': _local_dt(audit.logout_at),
            'duration': _format_duration(audit.duration_seconds),
            'active': audit.is_active,
            'ip': audit.ip_address or '—',
        })

    prev_month = month_start - timedelta(days=1)
    next_month = month_end + timedelta(days=1)

    context = {
        'users': users,
        'selected_user': selected_user,
        'year': year,
        'month': month,
        'month_label': f"{MONTH_NAMES_ES[month].capitalize()} {year}",
        'prev_month': f'{prev_month.year}-{prev_month.month:02d}',
        'next_month': f'{next_month.year}-{next_month.month:02d}',
        'is_current_month': (year == today.year and month == today.month),
        'weekday_labels': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
        'weeks': weeks,
        'metrics': {
            'sessions': len(scoped),
            'total_time': _format_duration(total_seconds),
            'avg_time': _format_duration(avg_seconds),
            'active': open_sessions,
        },
        'user_summary': [
            {'user': r['user'], 'count': r['count'], 'time': _format_duration(r['seconds'])}
            for r in user_summary
        ],
        'recent_rows': recent_rows,
    }
    return render(request, 'denuncias/admin_sessions.html', context)

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_stats(request):
    label_map = {
        'home': 'Inicio',
        'submit_complaint': 'Enviar denuncia',
        'lookup_complaint': 'Consultar denuncia',
        'faq': 'Preguntas frecuentes',
        'guide': 'Guía',
        'updates': 'Actualizaciones',
        'dashboard': 'Dashboard',
        'delegador_queue': 'Panel Delegador',
    }
    stats = list(PageViewStat.objects.all().order_by('route_name'))
    page_metrics = [
        {'route_name': s.route_name, 'label': label_map.get(s.route_name, s.route_name), 'count': s.count, 'last_viewed': s.last_viewed}
        for s in stats
    ]
    monthly_metrics = _build_monthly_metrics()
    return render(
        request,
        'denuncias/admin_stats.html',
        {
            'page_metrics': page_metrics,
            'routes_count': len(page_metrics),
            'monthly_metrics': monthly_metrics,
        },
    )

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_export(request):
    base = Complaint.objects.all()
    denuncias_qs = base.filter(action_type='denuncia')

    categorias_counts = list(
        denuncias_qs.values('category').annotate(n=Count('id')).order_by('-n', 'category')
    )
    gravedad_counts = list(
        denuncias_qs.values('severity').annotate(n=Count('id')).order_by('-n', 'severity')
    )
    status_counts = list(
        denuncias_qs.values('status').annotate(n=Count('id')).order_by('-n', 'status')
    )

    seguimiento_rows = [
        {'label': '0', 'count': denuncias_qs.filter(lookup_count=0).count()},
        {'label': '1', 'count': denuncias_qs.filter(lookup_count=1).count()},
        {'label': '2-3', 'count': denuncias_qs.filter(lookup_count__gte=2, lookup_count__lte=3).count()},
        {'label': '4-5', 'count': denuncias_qs.filter(lookup_count__gte=4, lookup_count__lte=5).count()},
        {'label': '6+', 'count': denuncias_qs.filter(lookup_count__gte=6).count()},
    ]

    generales = list(denuncias_qs.order_by('-created_at')[:20])
    return render(
        request,
        'denuncias/admin_export.html',
        {
            'total_denuncias': denuncias_qs.count(),
            'categorias_counts': categorias_counts,
            'gravedad_counts': gravedad_counts,
            'status_counts': status_counts,
            'ge2_followups_total': denuncias_qs.filter(lookup_count__gte=2).count(),
            'seguimiento_rows': seguimiento_rows,
            'generales': generales,
        },
    )

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_dashboard')
def admin_roles(request):
    User = get_user_model()
    admins = User.objects.filter(is_staff=True).order_by(Case(When(is_superuser=True, then=0), default=1, output_field=IntegerField()), 'username')
    create_form = AdminRegistrationForm()
    return render(request, 'denuncias/admin_roles.html', {'admins': admins, 'create_form': create_form})

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_dashboard')
def admin_create_admin_user(request):
    if request.method != 'POST':
        return redirect('denuncias:admin_roles')
    form = AdminRegistrationForm(request.POST)
    if not form.is_valid():
        User = get_user_model()
        admins = User.objects.filter(is_staff=True).order_by(Case(When(is_superuser=True, then=0), default=1, output_field=IntegerField()), 'username')
        return render(request, 'denuncias/admin_roles.html', {'admins': admins, 'create_form': form})
    username = (form.cleaned_data.get('username') or '').strip()
    if username.lower() in {'superusuario', 'delegador'}:
        form.add_error('username', 'Este nombre de usuario está reservado.')
        User = get_user_model()
        admins = User.objects.filter(is_staff=True).order_by(Case(When(is_superuser=True, then=0), default=1, output_field=IntegerField()), 'username')
        return render(request, 'denuncias/admin_roles.html', {'admins': admins, 'create_form': form})
    user = form.save(commit=False)
    user.is_staff = True
    user.is_superuser = False
    user.is_active = True
    user.role = (form.cleaned_data.get('role') or '').strip()
    if hasattr(user, 'is_verified'):
        user.is_verified = True
        if hasattr(user, 'verification_code'):
            user.verification_code = None
        if hasattr(user, 'verification_code_expires'):
            user.verification_code_expires = None
    user.save()
    messages.success(request, f'Usuario creado: {user.username}')
    return redirect('denuncias:admin_roles')

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_rejected(request):
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    base_qs = Complaint.objects.select_related('assigned_to').filter(status='rechazado')
    if not request.user.is_superuser and not is_delegador:
        base_qs = base_qs.filter(assigned_to=request.user)

    by_area = list(
        base_qs.values('actor_area').annotate(n=Count('id')).order_by('-n', 'actor_area')
    )

    q = (request.GET.get('q') or '').strip()
    area = (request.GET.get('area') or '').strip()
    qs = base_qs
    if q:
        qs = qs.filter(
            Q(folio__icontains=q)
            | Q(status__icontains=q)
            | Q(actor_area__icontains=q)
            | Q(name__icontains=q)
            | Q(email__icontains=q)
        )
    if area:
        if area.lower() in {'sin área', 'sin area'}:
            qs = qs.filter(Q(actor_area__isnull=True) | Q(actor_area__exact=''))
        else:
            qs = qs.filter(actor_area=area)

    qs = qs.order_by('-updated_at', '-created_at')
    paginator = Paginator(qs, 25)
    try:
        page_number = int(request.GET.get('page') or 1)
    except Exception:
        page_number = 1
    page_obj = paginator.get_page(page_number)
    complaints = list(page_obj.object_list)
    return render(
        request,
        'denuncias/admin_rejected.html',
        {
            'page_obj': page_obj,
            'complaints': complaints,
            'by_area': by_area,
            'q': q,
            'area': area,
        },
    )

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_assignment(request):
    return render(request, 'denuncias/admin_assignment.html')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_metrics_config(request):
    stats = PageViewStat.objects.aggregate(total=Sum('count'), last=Max('last_viewed'))
    return render(
        request,
        'denuncias/admin_metrics_config.html',
        {
            'pageviewstat_total': stats.get('total') or 0,
            'pageviewstat_last': stats.get('last'),
            'pageviewlog_total': PageViewLog.objects.count(),
            'complaints_lookup_gt3': Complaint.objects.filter(lookup_count__gt=3).count(),
            'complaints_total': Complaint.objects.count(),
        },
    )

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_archive(request):
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    final_codes = ['resuelto', 'archivado', 'transferido']
    labels = dict(getattr(Complaint, 'STATUS_CHOICES', []))
    qs = Complaint.objects.select_related('assigned_to').filter(status__in=final_codes)
    if not request.user.is_superuser and not is_delegador:
        qs = qs.filter(assigned_to=request.user)
    complaints = list(qs.order_by('-updated_at')[:250])
    return render(
        request,
        'denuncias/admin_archive.html',
        {
            'complaints': complaints,
            'final_status': [labels.get(c, c) for c in final_codes],
        },
    )

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_cases(request):
    is_delegador = (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador')
    final_codes = {'resuelto', 'archivado', 'transferido', 'rechazado'}
    User = get_user_model()

    if request.user.is_superuser or is_delegador:
        admins = list(
            User.objects.filter(is_staff=True, is_active=True)
            .exclude(username='Delegador')
            .order_by('assignment_position', 'username')
        )
    else:
        admins = [request.user]

    admin_infos = []
    for admin in admins:
        qs = Complaint.objects.filter(assigned_to=admin).exclude(status__in=final_codes).order_by('-updated_at')
        admin_infos.append(
            {
                'user': admin,
                'count': qs.count(),
                'complaints': list(qs[:40]),
            }
        )

    admin_infos = [i for i in admin_infos if i['count'] > 0 or (request.user.is_superuser or is_delegador)]
    return render(request, 'denuncias/admin_cases.html', {'admin_infos': admin_infos})

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_recidivists(request):
    return render(request, 'denuncias/admin_recidivists.html')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_dashboard')
def admin_edit_user_profile(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'El superusuario está protegido.')
        return redirect('denuncias:admin_roles')
    return redirect('denuncias:user_profile_detail', user_id=user.id)

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_export_excel(request):
    messages.info(request, "Funcionalidad de exportación pendiente de restauración.")
    return redirect('denuncias:admin_export')

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_stats_export_excel(request):
    messages.info(request, "Funcionalidad de exportación pendiente de restauración.")
    return redirect('denuncias:admin_stats')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_distribute_areas(request):
    messages.info(request, "Distribución de áreas pendiente de restauración.")
    return redirect('denuncias:admin_assignment')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_login')
def admin_update_assignment_order(request):
    messages.info(request, "Actualización de orden pendiente de restauración.")
    return redirect('denuncias:admin_assignment')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_dashboard')
def admin_toggle_require_data_update(request, user_id):
    if request.method != 'POST':
        return redirect('denuncias:admin_roles')
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser or user.username == 'Delegador' or getattr(user, 'role', '') == 'Delegador':
        messages.error(request, 'Este usuario está protegido.')
        return redirect('denuncias:admin_roles')
    user.require_data_update = not bool(getattr(user, 'require_data_update', False))
    user.save(update_fields=['require_data_update'])
    messages.success(request, f'Actualización requerida: {"Sí" if user.require_data_update else "No"}')
    return redirect('denuncias:admin_roles')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_dashboard')
def admin_set_user_password(request, user_id):
    if request.method != 'POST':
        return redirect('denuncias:admin_roles')
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, 'El superusuario está protegido.')
        return redirect('denuncias:admin_roles')
    form = AdminSetUserPasswordForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'No se pudo actualizar la contraseña.')
        return redirect('denuncias:admin_roles')
    user.set_password(form.cleaned_data['password1'])
    user.save(update_fields=['password'])
    messages.success(request, f'Contraseña actualizada: {user.username}')
    return redirect('denuncias:admin_roles')

@user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url='denuncias:admin_dashboard')
def admin_toggle_user_active(request, user_id):
    if request.method != 'POST':
        return redirect('denuncias:admin_roles')
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser or user.username == 'Delegador' or getattr(user, 'role', '') == 'Delegador':
        messages.error(request, 'Este usuario está protegido.')
        return redirect('denuncias:admin_roles')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(request, f'Usuario {user.username}: {"Activo" if user.is_active else "Inactivo"}')
    return redirect('denuncias:admin_roles')

@user_passes_test(is_admin, login_url='denuncias:admin_login')
def admin_archive_pdf(request):
    messages.info(request, "PDF de archivo pendiente de restauración.")
    return redirect('denuncias:admin_archive')

def public_ticket_pdf(request, folio):
    folio = folio.upper()
    if not request.session.get(f'auth_folio_{folio}'):
        return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={folio}")
    
    if not (REPORTLAB_AVAILABLE and QRCODE_AVAILABLE):
        raise Http404("Funcionalidad no disponible")
    complaint = get_object_or_404(Complaint, folio=folio)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 50, "Comprobante de Registro")
    
    p.setFont("Helvetica", 12)
    y = height - 80
    p.drawString(50, y, f"Folio: {complaint.folio}")
    y -= 20
    p.drawString(50, y, f"Fecha: {complaint.created_at.strftime('%d/%m/%Y %H:%M')}")
    y -= 20
    p.drawString(50, y, f"Estado: {complaint.get_status_display()}")
    y -= 20
    
    if complaint.action_type == 'denuncia':
        p.drawString(50, y, f"Tipo: Denuncia")
    else:
        p.drawString(50, y, f"Tipo: Consulta/Inquietud")
    y -= 20
        
    p.drawString(50, y, f"Categoría: {complaint.get_category_display() or '-'}")
    y -= 40
    
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Conserve este comprobante y su contraseña para dar seguimiento a su reporte.")
    y -= 15
    p.drawString(50, y, "Puede consultar el estado ingresando su folio y contraseña en el portal.")
    y -= 40

    qr_url = request.build_absolute_uri(reverse('denuncias:lookup_complaint')) + f"?folio={complaint.folio}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    from reportlab.lib.utils import ImageReader
    p.drawImage(ImageReader(img_buffer), 50, y - 150, width=150, height=150)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'comprobante_{complaint.folio}.pdf')

def public_ticket_qr(request, folio):
    folio = folio.upper()
    if not request.session.get(f'auth_folio_{folio}'):
        return redirect(f"{reverse('denuncias:lookup_complaint')}?folio={folio}")

    if not QRCODE_AVAILABLE:
        raise Http404("Funcionalidad no disponible")
    complaint = get_object_or_404(Complaint, folio=folio)
    
    qr_url = request.build_absolute_uri(reverse('denuncias:lookup_complaint')) + f"?folio={complaint.folio}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return HttpResponse(buffer, content_type="image/png")

def delegador_queue(request):
    if not _is_verified_admin_user(request.user):
        return redirect('denuncias:admin_login')
    if not (getattr(request.user, 'role', '') == 'Delegador' or request.user.username == 'Delegador'):
        return redirect('denuncias:admin_dashboard')
    stat, _ = PageViewStat.objects.get_or_create(route_name='delegador_queue', defaults={'count': 0})
    PageViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1, last_viewed=timezone.now())
    try:
        PageViewLog.objects.create(route_name='delegador_queue')
    except Exception:
        pass
    complaints = Complaint.objects.filter(status='enviado', assigned_to=request.user).order_by('-created_at')
    total_pending = complaints.count()
    sin_area_pending = complaints.filter(actor_area__isnull=True).count() + complaints.filter(actor_area='').count()
    area_breakdown = []
    try:
        area_set = sorted({(a or '').strip() for a in complaints.values_list('actor_area', flat=True) if (a or '').strip()})
        for area in area_set:
            area_breakdown.append({'area': area, 'count': complaints.filter(actor_area=area).count()})
        if sin_area_pending:
            area_breakdown.append({'area': 'Sin área', 'count': sin_area_pending})
    except Exception:
        area_breakdown = []
    category_labels = dict(Complaint.CATEGORY_CHOICES)
    category_breakdown = [
        {
            'category': category_labels.get(row['category'], row['category']) if row['category'] else 'Sin categoría',
            'count': row['n'],
        }
        for row in complaints.values('category').annotate(n=Count('id')).order_by('-n', 'category')
    ]
    User = get_user_model()
    all_admins = User.objects.filter(is_staff=True, is_active=True).exclude(username='Delegador').order_by('assignment_position', 'id')
    all_areas = sorted({(u.area or '').strip() for u in all_admins if (u.area or '').strip()})
    return render(request, 'denuncias/delegador_dashboard.html', {
        'complaints': complaints,
        'total_pending': total_pending,
        'sin_area_pending': sin_area_pending,
        'area_breakdown': area_breakdown,
        'category_breakdown': category_breakdown,
        'all_admins': all_admins,
        'all_areas': all_areas,
    })

def user_profile(request, user_id=None):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('denuncias:admin_login')
    User = get_user_model()
    if user_id is None:
        target_user = request.user
        is_own_profile = True
    else:
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para consultar otros perfiles.')
            return redirect('denuncias:user_profile')
        target_user = get_object_or_404(User, id=user_id)
        is_own_profile = target_user.id == request.user.id

    can_edit_role = request.user.is_superuser and not target_user.is_superuser

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=target_user)
        if not can_edit_role:
            form.fields.pop('role', None)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            if is_own_profile:
                return redirect('denuncias:user_profile')
            return redirect('denuncias:user_profile_detail', user_id=target_user.id)
    else:
        form = UserProfileForm(instance=target_user)
        if not can_edit_role:
            form.fields.pop('role', None)

    return render(request, 'denuncias/user_profile.html', {
        'target_user': target_user,
        'profile_form': form,
        'is_own_profile': is_own_profile,
        'can_edit_role': can_edit_role,
    })
