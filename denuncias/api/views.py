import os

from django.core import signing
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from ..models import ChatMessage, Complaint, ComplaintAttachment, PrivacyNotice, ReporterNote
from ..services.complaints import (
    chat_enabled_for,
    get_complaint_for_reporter,
    persist_new_complaint,
    resolve_category,
)
from .serializers import (
    OPTIONAL_FIELDS,
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ComplaintCreateSerializer,
    ComplaintLookupResultSerializer,
    ComplaintLookupSerializer,
    PrivacyNoticeSerializer,
    ReporterNoteCreateSerializer,
    ReporterNoteSerializer,
)

ATTACHMENT_SALT = 'canalg.attachment'
ATTACHMENT_TOKEN_MAX_AGE = 3600


def _auth_error_response(error):
    if error == 'not_found':
        return Response({'error': 'not_found', 'detail': 'No se encontró ninguna denuncia con ese folio.'},
                        status=status.HTTP_404_NOT_FOUND)
    if error == 'password_required':
        return Response({'error': 'password_required', 'detail': 'Esta denuncia está protegida. Ingresa tu contraseña.'},
                        status=status.HTTP_401_UNAUTHORIZED)
    if error == 'invalid_password':
        return Response({'error': 'invalid_password', 'detail': 'Contraseña incorrecta.'},
                        status=status.HTTP_401_UNAUTHORIZED)
    return None


def _resolve_complaint(request):
    data = request.data
    payload = {'folio': data.get('folio')}
    if data.get('password') is not None:
        payload['password'] = data.get('password')
    serializer = ComplaintLookupSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    complaint, error = get_complaint_for_reporter(
        serializer.validated_data['folio'], serializer.validated_data.get('password')
    )
    if error:
        return None, _auth_error_response(error)
    return complaint, None


@api_view(['GET'])
def api_root(request):
    return Response({
        'service': 'CanalG API',
        'version': '1.1',
        'endpoints': {
            'create_complaint': request.build_absolute_uri(reverse('api:complaint-create')),
            'lookup_complaint': request.build_absolute_uri(reverse('api:complaint-lookup')),
            'chat': request.build_absolute_uri(reverse('api:complaint-chat')),
            'notes': request.build_absolute_uri(reverse('api:complaint-notes')),
            'attachments': request.build_absolute_uri(reverse('api:complaint-attachments')),
            'privacy_notices': request.build_absolute_uri(reverse('api:privacy-notices')),
        },
    })


@api_view(['GET'])
def privacy_notices(request):
    notices = PrivacyNotice.objects.filter(is_published=True).order_by('company')
    return Response(PrivacyNoticeSerializer(notices, many=True, context={'request': request}).data)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def complaint_create(request):
    serializer = ComplaintCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    complaint = Complaint(
        action_type=data.get('action_type') or 'denuncia',
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        reporter_matricula=data.get('reporter_matricula'),
        category=resolve_category(
            data.get('action_type'),
            data.get('category'),
            data.get('queja_category'),
            data.get('inquietud_category'),
        ),
        relationship=data.get('relationship'),
        incident_state=data.get('incident_state'),
        incident_branch=data.get('incident_branch'),
        incident_date=data.get('incident_date'),
        incident_time=data.get('incident_time'),
        knows_actor=data.get('knows_actor'),
        reporter_role=data.get('reporter_role'),
        has_witnesses=data.get('has_witnesses'),
        witnesses_count=data.get('witnesses_count'),
        witnesses_names=data.get('witnesses_names'),
        actor_name=data.get('actor_name'),
        actor_matricula=data.get('actor_matricula'),
        actor_area=data.get('actor_area'),
        description=data.get('description') or '',
    )
    optional = {key: (data.get(key) or '').strip() for key in OPTIONAL_FIELDS}
    persist_new_complaint(
        complaint,
        files=data.get('attachments'),
        request=request,
        optional=optional,
        password=data.get('password'),
        privacy_opened=(data.get('privacy_policies_opened') or '').strip(),
    )

    lookup_url = request.build_absolute_uri(reverse('denuncias:lookup_complaint')) + f'?folio={complaint.folio}'
    return Response({
        'folio': complaint.folio,
        'status': complaint.status,
        'status_display': complaint.get_status_display(),
        'severity': complaint.severity,
        'severity_display': complaint.get_severity_display(),
        'created_at': complaint.created_at,
        'lookup_url': lookup_url,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def complaint_lookup(request):
    serializer = ComplaintLookupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    complaint, error = get_complaint_for_reporter(
        serializer.validated_data['folio'],
        serializer.validated_data.get('password'),
    )
    if error:
        return _auth_error_response(error)
    return Response(ComplaintLookupResultSerializer(complaint, context={'request': request}).data)


@api_view(['POST'])
def complaint_chat(request):
    complaint, error_response = _resolve_complaint(request)
    if error_response:
        return error_response

    if request.data.get('message') is not None:
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not chat_enabled_for(complaint):
            return Response({'error': 'chat_disabled',
                             'detail': 'El chat no está habilitado para el estado actual de la denuncia.'},
                            status=status.HTTP_409_CONFLICT)
        message = ChatMessage.objects.create(
            complaint=complaint,
            sender='reporter',
            message=serializer.validated_data['message'],
        )
        return Response(ChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)

    messages = complaint.chat_messages.all().order_by('created_at')
    return Response({
        'folio': complaint.folio,
        'chat_enabled': chat_enabled_for(complaint),
        'messages': ChatMessageSerializer(messages, many=True).data,
    })


@api_view(['POST'])
def complaint_notes(request):
    complaint, error_response = _resolve_complaint(request)
    if error_response:
        return error_response

    if request.data.get('content') is not None:
        serializer = ReporterNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = ReporterNote.objects.create(
            complaint=complaint,
            content=serializer.validated_data['content'],
        )
        return Response(ReporterNoteSerializer(note).data, status=status.HTTP_201_CREATED)

    notes = complaint.reporter_notes.all().order_by('created_at')
    return Response({
        'folio': complaint.folio,
        'notes': ReporterNoteSerializer(notes, many=True).data,
    })


def _attachment_item(complaint, attachment_id, file_field, request):
    token = signing.dumps({'c': complaint.pk, 'a': str(attachment_id)}, salt=ATTACHMENT_SALT)
    download_url = request.build_absolute_uri(
        reverse('api:complaint-attachment-download', kwargs={'token': token})
    )
    try:
        size = file_field.size
    except Exception:
        size = None
    return {
        'id': str(attachment_id),
        'name': os.path.basename(file_field.name),
        'is_main': attachment_id == 'main',
        'size': size,
        'download_url': download_url,
    }


@api_view(['POST'])
def complaint_attachments(request):
    complaint, error_response = _resolve_complaint(request)
    if error_response:
        return error_response
    items = []
    if complaint.attachment:
        items.append(_attachment_item(complaint, 'main', complaint.attachment, request))
    for attachment in complaint.attachments.all().order_by('uploaded_at'):
        items.append(_attachment_item(complaint, attachment.pk, attachment.file, request))
    return Response({'folio': complaint.folio, 'attachments': items})


def complaint_attachment_download(request, token):
    try:
        payload = signing.loads(token, salt=ATTACHMENT_SALT, max_age=ATTACHMENT_TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        return JsonResponse({'error': 'expired', 'detail': 'El enlace de descarga expiró.'}, status=410)
    except signing.BadSignature:
        return JsonResponse({'error': 'invalid_token', 'detail': 'Enlace de descarga inválido.'}, status=403)

    complaint = get_object_or_404(Complaint, pk=payload.get('c'))
    attachment_id = str(payload.get('a'))
    if attachment_id == 'main':
        file_field = complaint.attachment
    else:
        attachment = get_object_or_404(ComplaintAttachment, pk=attachment_id, complaint=complaint)
        file_field = attachment.file
    if not file_field:
        raise Http404('No hay archivo')
    try:
        response = FileResponse(
            file_field.open('rb'),
            as_attachment=True,
            filename=os.path.basename(file_field.name),
        )
    except FileNotFoundError:
        raise Http404('El archivo físico no existe')
    return response
