from rest_framework import serializers
from django.templatetags.static import static
from django.core.exceptions import ValidationError

from ..models import ChatMessage, Complaint, PrivacyNotice, ReporterNote
from ..services.complaints import chat_enabled_for, mask_email, mask_phone
from ..services.uploads import validate_complaint_upload

OPTIONAL_FIELDS = [
    'recurrence',
    'recurrence_since',
    'immediate_risk',
    'previous_report',
    'previous_report_channel',
    'contact_preference',
    'share_permission',
    'impact_notes',
]


class PrivacyNoticeSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = PrivacyNotice
        fields = ['id', 'company', 'file', 'file_url', 'is_published', 'updated_at']

    def get_file_url(self, obj):
        url = obj.file.url if obj.file else static('PDFs/Aviso de privacidad.pdf')
        url = url.replace(' ', '%20')
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class ComplaintCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, max_length=128)
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)
    privacy_policies_opened = serializers.CharField(required=False, allow_blank=True, write_only=True)
    terms_accept = serializers.BooleanField(write_only=True)
    queja_category = serializers.CharField(required=False, allow_blank=True, write_only=True)
    inquietud_category = serializers.CharField(required=False, allow_blank=True, write_only=True)
    recurrence = serializers.CharField(required=False, allow_blank=True, write_only=True)
    recurrence_since = serializers.CharField(required=False, allow_blank=True, write_only=True)
    immediate_risk = serializers.CharField(required=False, allow_blank=True, write_only=True)
    previous_report = serializers.CharField(required=False, allow_blank=True, write_only=True)
    previous_report_channel = serializers.CharField(required=False, allow_blank=True, write_only=True)
    contact_preference = serializers.CharField(required=False, allow_blank=True, write_only=True)
    share_permission = serializers.CharField(required=False, allow_blank=True, write_only=True)
    impact_notes = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Complaint
        fields = [
            'action_type',
            'name', 'email', 'phone', 'reporter_matricula',
            'category', 'relationship', 'description',
            'incident_state', 'incident_branch', 'incident_date', 'incident_time',
            'knows_actor', 'reporter_role',
            'has_witnesses', 'witnesses_count', 'witnesses_names',
            'actor_name', 'actor_matricula', 'actor_area',
            'password', 'attachments', 'privacy_policies_opened',
            'terms_accept', 'queja_category', 'inquietud_category',
        ] + OPTIONAL_FIELDS

    def validate_description(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('La descripción es obligatoria.')
        return value

    def validate_phone(self, value):
        value = (value or '').strip()
        if not value:
            return value
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError('Teléfono o Red debe contener exactamente 10 dígitos.')
        return value

    def validate_reporter_matricula(self, value):
        value = (value or '').strip()
        if value and (not value.isdigit() or len(value) > 10):
            raise serializers.ValidationError('El número de empleado debe contener solo números y hasta 10 dígitos.')
        return value

    def validate_actor_matricula(self, value):
        value = (value or '').strip()
        if value and (not value.isdigit() or len(value) > 10):
            raise serializers.ValidationError('El número de empleado debe contener solo números y hasta 10 dígitos.')
        return value

    def validate_terms_accept(self, value):
        if value is not True:
            raise serializers.ValidationError('Debes confirmar que has leído y aceptas la Política de Privacidad.')
        return value

    def validate_attachments(self, value):
        attachments = list(value or [])
        if len(attachments) > 5:
            raise serializers.ValidationError('Máximo 5 archivos permitidos.')
        for uploaded_file in attachments:
            try:
                validate_complaint_upload(uploaded_file)
            except ValidationError as exc:
                raise serializers.ValidationError(exc.messages)
        return attachments

    def validate(self, attrs):
        if not (attrs.get('privacy_policies_opened') or '').strip():
            raise serializers.ValidationError({
                'privacy_policies_opened': 'Debes abrir una política de privacidad antes de enviar el reporte.'
            })
        return attrs


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_display = serializers.CharField(source='get_sender_display', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'sender_display', 'message', 'created_at']


class ReporterNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporterNote
        fields = ['id', 'content', 'created_at']


class ChatMessageCreateSerializer(serializers.Serializer):
    folio = serializers.CharField(max_length=20)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    message = serializers.CharField()

    def validate_folio(self, value):
        return (value or '').strip().upper()

    def validate_message(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('El mensaje no puede estar vacío.')
        return value


class ReporterNoteCreateSerializer(serializers.Serializer):
    folio = serializers.CharField(max_length=20)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    content = serializers.CharField()

    def validate_folio(self, value):
        return (value or '').strip().upper()

    def validate_content(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('La nota no puede estar vacía.')
        return value


class ComplaintLookupSerializer(serializers.Serializer):
    folio = serializers.CharField(max_length=20)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)

    def validate_folio(self, value):
        return (value or '').strip().upper()


class ComplaintLookupResultSerializer(serializers.ModelSerializer):

    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    chat_enabled = serializers.SerializerMethodField()
    masked_email = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            'folio', 'action_type', 'action_type_display',
            'status', 'status_display',
            'severity', 'severity_display',
            'category', 'category_display',
            'response', 'created_at', 'updated_at', 'lookup_count',
            'chat_enabled', 'masked_email', 'masked_phone', 'reporter_name',
        ]

    def get_chat_enabled(self, obj):
        return chat_enabled_for(obj)

    def get_masked_email(self, obj):
        return mask_email(obj.email)

    def get_masked_phone(self, obj):
        return mask_phone(obj.phone)

    def get_reporter_name(self, obj):
        reporter_name = (obj.name or '').strip()
        if not reporter_name:
            return None
        admin_display_name = None
        if obj.assigned_to:
            admin_display_name = obj.assigned_to.get_full_name() or obj.assigned_to.username
        if admin_display_name and reporter_name == admin_display_name.strip():
            return None
        return reporter_name
