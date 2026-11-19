from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings
import os
from .models import CustomUser, Complaint, ChatMessage, ReporterNote, InvestigationPlan, EvidenceItem, Finding, CaseReport, ResourceItem, PrivacyNotice, InvestigationProcedure
from io import BytesIO

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):

    def to_python(self, data):
        if data in (None, '', [], ()):
            return []
        if isinstance(data, (list, tuple)):
            files = []
            for item in data:
                if item in (None, ''):
                    continue
                if hasattr(item, 'name'):
                    files.append(item)
                else:
                    raise ValidationError(self.error_messages.get('invalid', 'Archivo inválido'), code='invalid')
            return files
        if hasattr(data, 'name'):
            return [data]
        raise ValidationError(self.error_messages.get('invalid', 'Archivo inválido'), code='invalid')

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='Nombre', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}))
    last_name = forms.CharField(label='Apellidos', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}))
    email = forms.EmailField(label='Correo', required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}))
    phone_number = forms.CharField(label='Teléfono', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}))
    company = forms.CharField(label='Empresa', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}))
    role = forms.CharField(label='Rol', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Puesto o rol'}))
    area = forms.CharField(label='Área', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Área'}))
    branch = forms.CharField(label='Sucursal', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sucursal'}))
    matricula = forms.CharField(label='Matrícula', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula'}))
    employment_start = forms.DateField(label='Fecha de ingreso', required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    employment_end = forms.DateField(label='Fecha de egreso', required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'company', 'role', 'area', 'branch', 'matricula', 'employment_start', 'employment_end']

class StyledPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

class ComplaintForm(forms.ModelForm):
    attachments = MultipleFileField(required=False, widget=MultiFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.txt,.rtf,.odt,.ods,.odp,.xls,.xlsx,.ppt,.pptx', 'multiple': True}), help_text='Puedes subir múltiples archivos. Formatos permitidos: PDF, DOC, DOCX, JPG, JPEG, PNG, GIF, TXT, RTF, ODT, ODS, ODP, XLS, XLSX, PPT, PPTX. Tamaño máximo por archivo: 10MB.')
    reporting_mode = forms.ChoiceField(required=False, choices=[('', 'Selecciona...'), ('anonimo', 'Anónimo'), ('con_datos', 'Con mis datos')], widget=forms.Select(attrs={'class': 'form-select'}))
    action_type = forms.ChoiceField(required=False, label='¿Qué acción vas a realizar?', choices=[('', 'Selecciona...'), ('denuncia', 'Realizar una denuncia'), ('inquietud', 'Realizar una inquietud')], widget=forms.Select(attrs={'class': 'form-select'}))
    company_role = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Puesto en la empresa', 'pattern': '^[A-Za-zÁÉÍÓÚáéíóúÜüÑñ\\s]+$', 'title': 'Solo letras y espacios (se permiten acentos)'}))
    category = forms.ChoiceField(required=False, choices=[
        ('', 'Selecciona...'),
        ('Acoso y discriminación', [
            ('Acoso laboral (mobbing)', 'Acoso laboral (mobbing)'),
            ('Acoso sexual', 'Acoso sexual'),
            ('Discriminación', 'Discriminación'),
            ('Hostigamiento laboral', 'Hostigamiento laboral'),
            ('Hostigamiento sexual', 'Hostigamiento sexual'),
            ('Prácticas laborales ilegales', 'Prácticas laborales ilegales (Inquietud del Sistema de Gestión de Cumplimiento)')
        ]),
        ('Conflictos y ética', [
            ('Conflictos de interés', 'Conflictos de interés'),
            ('Violación de la política interna (Código de Ética)', 'Violación de la política interna (Código de Ética)')
        ]),
        ('Datos y seguridad', [
            ('Incumplimiento de la normativa de protección de datos', 'Incumplimiento de la normativa de Protección de Datos'),
            ('Incumplimientos graves de seguridad y salud laboral', 'Incumplimientos graves de Seguridad y Salud Laboral'),
            ('Violación de la seguridad de la información', 'Violación de la Seguridad de la Información')
        ]),
        ('Fraude y cumplimiento', [
            ('Blanqueo de capitales', 'Blanqueo de capitales'),
            ('Extorsión', 'Extorsión'),
            ('Malversación o robo', 'Malversación o robo'),
            ('Soborno', 'Soborno'),
            ('Uso indebido de activos/recursos de la empresa', 'Uso indebido de activos/recursos de la empresa'),
            ('Fraude y corrupción', 'Fraude y corrupción')
        ]),
        ('Competencia', [
            ('Infracciones de derecho de la competencia', 'Infracciones de Derecho de la Competencia')
        ])
    ], widget=forms.Select(attrs={'class': 'form-select'}))
    inquietud_category = forms.ChoiceField(required=False, label='Tipo de inquietud', choices=[
        ('', 'Selecciona...'),
        ('Conflictos de interés', 'Conflictos de interés'),
        ('Interpretación normativa', 'Interpretación normativa'),
        ('Violación de la política interna (Código de Ética)', 'Violación de la política interna (Código de Ética)'),
        ('Situaciones ambiguas', 'Situaciones ambiguas')
    ], widget=forms.Select(attrs={'class': 'form-select'}))
    recurrence = forms.ChoiceField(required=False, label='¿El hecho fue único o se repite?', choices=[('', 'Selecciona...'), ('no', 'Fue único'), ('si', 'Se repite'), ('no_seguro', 'No estoy seguro')], widget=forms.Select(attrs={'class': 'form-select'}))
    recurrence_since = forms.CharField(required=False, label='Si se repite, ¿desde cuándo ocurre?', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Desde hace 3 meses / Desde julio'}))
    immediate_risk = forms.ChoiceField(required=False, label='¿Existe algún riesgo inmediato para ti u otra persona?', choices=[('', 'Selecciona...'), ('si', 'Sí, hay riesgo inmediato'), ('no', 'No'), ('no_seguro', 'No estoy seguro')], widget=forms.Select(attrs={'class': 'form-select'}))
    previous_report = forms.ChoiceField(required=False, label='¿Lo has reportado antes dentro de la empresa?', choices=[('', 'Selecciona...'), ('si', 'Sí'), ('no', 'No')], widget=forms.Select(attrs={'class': 'form-select'}))
    previous_report_channel = forms.CharField(required=False, label='Si lo reportaste, ¿por dónde?', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. RH, jefe directo, línea ética, correo, etc.'}))
    contact_preference = forms.ChoiceField(required=False, label='Preferencia para contactarte', choices=[('', 'Selecciona...'), ('email', 'Correo electrónico'), ('phone', 'Teléfono'), ('whatsapp', 'Contactar por WhatsApp'), ('any', 'Cualquier medio')], widget=forms.Select(attrs={'class': 'form-select'}))
    share_permission = forms.ChoiceField(required=False, label='¿Autorizas compartir detalles con RRHH/Comité para investigar?', choices=[('', 'Selecciona...'), ('si', 'Sí, autorizo'), ('no', 'Prefiero que no')], widget=forms.Select(attrs={'class': 'form-select'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña para consultar tu denuncia', 'autocomplete': 'new-password'}), label='Contraseña')
    password_confirm = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirma tu contraseña', 'autocomplete': 'new-password'}), label='Confirmar contraseña')
    impact_notes = forms.CharField(required=False, label='Notas sobre el impacto (opcional)', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'style': 'min-height: 96px;', 'placeholder': 'Si quieres, comparte cómo te afectó (emocional, laboral, etc.)'}))

    class Meta:
        model = Complaint
        fields = ['action_type', 'name', 'email', 'phone', 'reporter_matricula', 'category', 'relationship', 'incident_date', 'incident_time', 'incident_state', 'incident_branch', 'knows_actor', 'reporter_role', 'actor_name', 'actor_matricula', 'actor_area', 'has_witnesses', 'witnesses_count', 'witnesses_names', 'description', 'attachment']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan Pérez', 'pattern': '^[A-Za-zÁÉÍÓÚáéíóúÜüÑñ\\s]+$', 'title': 'Solo letras y espacios (se permiten acentos)'}), 'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}), 'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 5512345678', 'type': 'tel', 'inputmode': 'numeric', 'maxlength': '10', 'autocomplete': 'off'}), 'category': forms.Select(attrs={'class': 'form-select'}), 'reporter_matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de empleado', 'inputmode': 'numeric', 'maxlength': '10', 'autocomplete': 'off'}), 'relationship': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Selecciona...'), ('Colaborador', 'Colaborador'), ('Cliente', 'Cliente'), ('Proveedor', 'Proveedor')]), 'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min': '1980-01-01', 'max': '2150-12-31'}), 'incident_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), 'incident_state': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Selecciona...')]), 'incident_branch': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Selecciona...')]), 'knows_actor': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Selecciona...'), (True, 'Sí'), (False, 'No')]), 'reporter_role': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Selecciona...'), ('Testigo', 'Testigo'), ('Víctima', 'Víctima'), ('Conocimiento', 'Conocimiento')]), 'actor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del denunciado'}), 'actor_matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de empleado del denunciado', 'inputmode': 'numeric', 'maxlength': '10', 'autocomplete': 'off'}), 'actor_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Área de trabajo'}), 'has_witnesses': forms.Select(attrs={'class': 'form-select'}, choices=[('', 'Selecciona...'), (True, 'Sí'), (False, 'No')]), 'witnesses_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Ej. 2'}), 'witnesses_names': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'min-height: 84px;', 'placeholder': 'Nombres de testigos (opcional)'}), 'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 12, 'style': 'min-height: 240px;', 'placeholder': 'Describe los detalles del hecho. Entre más detalles proporciones más fácil será el seguimiento adecuado.'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].widget.attrs.update({
            'type': 'tel',
            'inputmode': 'numeric',
            'maxlength': '10',
            'placeholder': 'Ingresa 10 dígitos',
        })
        self.fields['description'].widget.attrs['placeholder'] = 'Describe los detalles del hecho con la mayor claridad posible.'
        state_choices = [
            ('', 'Selecciona...'),
            ('CDMX', 'Ciudad de México'), ('Edomex', 'Estado de México'), ('Jalisco', 'Jalisco'),
            ('Nuevo León', 'Nuevo León'), ('Puebla', 'Puebla'), ('Veracruz', 'Veracruz'),
            ('Guerrero', 'Guerrero'), ('Querétaro', 'Querétaro'), ('Chihuahua', 'Chihuahua'),
        ]
        branch_choices = [
            ('', 'Selecciona...'),
            ('Matriz', 'Matriz'), ('Norte', 'Sucursal Norte'), ('Sur', 'Sucursal Sur'),
            ('Centro', 'Sucursal Centro'), ('Occidente', 'Sucursal Occidente')
        ]
        try:
            self.fields['incident_state'].widget.choices = state_choices
            self.fields['incident_branch'].widget.choices = branch_choices
        except Exception:
            pass

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not phone:
            return phone
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError('Teléfono o Red debe contener exactamente 10 dígitos.')
        return phone

    def clean_company_role(self):
        role = (self.cleaned_data.get('company_role') or '').strip()
        if not role:
            return role
        import re
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÜüÑñ\s]+$', role):
            raise ValidationError('El puesto solo debe contener letras y espacios (se permiten acentos).')
        return role

    def clean_attachments(self):
        files = self.cleaned_data.get('attachments') or []
        if not files:
            return None
        if len(files) > 5:
            raise ValidationError('Máximo 5 archivos permitidos.')
        allowed_exts = set(getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', []))
        max_size = int(getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024))
        img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        doc_zip_exts = {'.docx', '.xlsx', '.pptx'}
        for f in files:
            if getattr(f, 'size', 0) > max_size:
                raise ValidationError(f'El archivo "{f.name}" es demasiado grande. Máximo: {max_size // (1024 * 1024)}MB')
            ext = os.path.splitext(f.name)[1].lower()
            if allowed_exts and ext not in allowed_exts:
                raise ValidationError(f"Tipo de archivo no permitido: {ext}. Permitidas: {', '.join(sorted(allowed_exts))}")
            try:
                head = f.read(16)
                f.seek(0)
            except Exception:
                head = b''

            def startswith(b):
                return head.startswith(b)
            is_pdf = startswith(b'%PDF')
            is_png = startswith(b'\x89PNG\r\n\x1a\n')
            is_jpg = startswith(b'\xff\xd8')
            is_gif = startswith(b'GIF87a') or startswith(b'GIF89a')
            is_riff = startswith(b'RIFF') and (len(head) >= 12 and head[8:12] == b'WEBP')
            is_zip = startswith(b'PK\x03\x04') or startswith(b'PK\x05\x06')
            is_doc_cf = startswith(b'\xd0\xcf\x11\xe0')
            if ext == '.pdf' and (not is_pdf):
                raise ValidationError(f'El contenido de "{f.name}" no coincide con un PDF válido.')
            if ext in img_exts and (not (is_png or is_jpg or is_gif or is_riff)):
                raise ValidationError(f'El contenido de "{f.name}" no coincide con una imagen válida.')
            if ext in doc_zip_exts and (not is_zip):
                raise ValidationError(f'El contenido de "{f.name}" no coincide con un archivo Office válido.')
            if ext == '.doc' and (not is_doc_cf):
                raise ValidationError(f'El contenido de "{f.name}" no coincide con un archivo .doc válido.')
        return files

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > settings.MAX_UPLOAD_SIZE:
                raise ValidationError(f'El archivo es demasiado grande. Tamaño máximo: {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB')
            ext = os.path.splitext(attachment.name)[1].lower()
            if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
                raise ValidationError(f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}")
            try:
                head = attachment.read(16)
                attachment.seek(0)
            except Exception:
                head = b''

            def startswith(b):
                return head.startswith(b)
            is_pdf = startswith(b'%PDF')
            is_png = startswith(b'\x89PNG\r\n\x1a\n')
            is_jpg = startswith(b'\xff\xd8')
            is_gif = startswith(b'GIF87a') or startswith(b'GIF89a')
            is_riff = startswith(b'RIFF') and (len(head) >= 12 and head[8:12] == b'WEBP')
            is_zip = startswith(b'PK\x03\x04') or startswith(b'PK\x05\x06')
            is_doc_cf = startswith(b'\xd0\xcf\x11\xe0')
            img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
            doc_zip_exts = {'.docx', '.xlsx', '.pptx'}
            if ext == '.pdf' and (not is_pdf):
                raise ValidationError('El contenido no coincide con un PDF válido.')
            if ext in img_exts and (not (is_png or is_jpg or is_gif or is_riff)):
                raise ValidationError('El contenido no coincide con una imagen válida.')
            if ext in doc_zip_exts and (not is_zip):
                raise ValidationError('El contenido no coincide con un archivo Office válido.')
            if ext == '.doc' and (not is_doc_cf):
                raise ValidationError('El contenido no coincide con un archivo .doc válido.')
        return attachment

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            return name
        import re
        if not re.match('^[A-Za-zÁÉÍÓÚáéíóúÜüÑñ\\s]+$', name):
            raise ValidationError('El nombre solo debe contener letras y espacios (se permiten acentos).')
        return name

    def clean_reporter_matricula(self):
        matricula = (self.cleaned_data.get('reporter_matricula') or '').strip()
        if not matricula:
            return matricula
        if not matricula.isdigit() or len(matricula) > 10:
            raise ValidationError('El número de empleado debe contener solo números y hasta 10 dígitos.')
        return matricula

    def clean_actor_matricula(self):
        matricula = (self.cleaned_data.get('actor_matricula') or '').strip()
        if not matricula:
            return matricula
        if not matricula.isdigit() or len(matricula) > 10:
            raise ValidationError('El número de empleado debe contener solo números y hasta 10 dígitos.')
        return matricula

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        
        mode = (cleaned.get('reporting_mode') or '').strip()
        relationship = (cleaned.get('relationship') or '').strip()
        category = (cleaned.get('category') or '').strip()
        action_type = (cleaned.get('action_type') or '').strip()

        if not relationship:
            self.add_error('relationship', 'Este campo es obligatorio.')
        if not action_type:
            self.add_error('action_type', 'Este campo es obligatorio.')
        if not mode:
            self.add_error('reporting_mode', 'Este campo es obligatorio.')

        if action_type == 'inquietud':
            val = cleaned.get('inquietud_category')
            if not val:
                self.add_error('inquietud_category', 'Este campo es obligatorio.')
            else:
                cleaned['category'] = val
        elif action_type == 'denuncia':
            if not category:
                self.add_error('category', 'Este campo es obligatorio.')

        if action_type == 'denuncia':
            for field in ['incident_state', 'incident_branch', 'incident_date', 'incident_time']:
                val = cleaned.get(field)
                if isinstance(val, str):
                    val = val.strip()
                if not val:
                    self.add_error(field, 'Este campo es obligatorio.')
            
            bool_fields = ['knows_actor', 'has_witnesses']
            opt_fields = ['reporter_role']
            for field in bool_fields:
                val = cleaned.get(field)
                if val is None or (isinstance(val, str) and val.strip() == ''):
                    self.add_error(field, 'Este campo es obligatorio.')
            for field in opt_fields:
                val = cleaned.get(field)
                if isinstance(val, str):
                    val = val.strip()
                if not val:
                    self.add_error(field, 'Este campo es obligatorio.')

        if mode == 'con_datos':
            required_fields = ['name', 'email', 'phone', 'company_role']
            if relationship == 'Colaborador':
                required_fields.append('reporter_matricula')
            for field in required_fields:
                val = cleaned.get(field)
                if isinstance(val, str):
                    val = val.strip()
                if not val:
                    self.add_error(field, 'Este campo es obligatorio cuando seleccionas "Con mis datos".')
        return cleaned

class ComplaintLookupForm(forms.Form):
    folio = forms.CharField(max_length=20, initial='GSI-', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GSI-ABC123', 'maxlength': '20', 'autocomplete': 'off', 'required': True}), label='Folio de la denuncia')
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña', 'required': True}), label='Contraseña')

    def clean_folio(self):
        folio = (self.cleaned_data.get('folio') or '').strip().upper()
        if not folio.startswith('GSI-'):
            folio = f'GSI-{folio}'
        if folio == 'GSI-':
            raise ValidationError('Ingresa los caracteres de tu folio después de GSI-.')
        return folio

class AdminRegistrationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('', 'Analista'),
        ('Delegador', 'Delegador'),
        ('actualizador', 'Actualizador'),
    ]
    email = forms.EmailField(required=True, label='Correo', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico corporativo'}))
    first_name = forms.CharField(max_length=30, required=True, label='Nombre', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}))
    last_name = forms.CharField(max_length=30, required=True, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}))
    phone_number = forms.CharField(max_length=15, required=False, label='Teléfono (opcional)', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de teléfono (opcional)'}))
    role = forms.ChoiceField(required=False, label='Rol', choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})

class ResourceItemForm(forms.ModelForm):

    class Meta:
        model = ResourceItem
        fields = ['kind', 'title', 'description', 'file', 'published_on', 'sort_order', 'is_published']
        labels = {
            'kind': 'Tipo',
            'title': 'Título',
            'description': 'Descripción',
            'file': 'Archivo',
            'published_on': 'Fecha',
            'sort_order': 'Orden',
            'is_published': 'Publicado',
        }
        widgets = {
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'min-height: 84px;', 'placeholder': 'Descripción (opcional)'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'published_on': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PrivacyNoticeForm(forms.ModelForm):

    class Meta:
        model = PrivacyNotice
        fields = ['company', 'file', 'is_published']
        labels = {'company': 'Empresa', 'file': 'PDF', 'is_published': 'Publicado'}
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminLoginForm(forms.Form):
    GENERIC_LOGIN_ERROR = (
        'No fue posible iniciar sesión. Verifica tus credenciales o el acceso autorizado.'
    )
    username = forms.CharField(strip=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}))
    password = forms.CharField(strip=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        space_issue = False
        if username is not None and (username != username.strip() or ' ' in username):
            space_issue = True
        if password is not None and password != password.strip():
            space_issue = True
        if space_issue:
            self.add_error('password', self.GENERIC_LOGIN_ERROR)
            return self.cleaned_data
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                username_matches = CustomUser.objects.filter(
                    username__iexact=username,
                    is_active=True,
                )
                email_matches = CustomUser.objects.filter(
                    email__iexact=username,
                    is_active=True,
                )
                if username_matches.count() == 1:
                    candidate_username = username_matches.first().get_username()
                    user = authenticate(
                        username=candidate_username,
                        password=password,
                    )
                elif email_matches.count() == 1:
                    candidate_username = email_matches.first().get_username()
                    user = authenticate(
                        username=candidate_username,
                        password=password,
                    )
            if not user:
                self.add_error('password', self.GENERIC_LOGIN_ERROR)
            elif not getattr(user, 'is_staff', False) or not (
                getattr(user, 'is_verified', False)
                or (
                    getattr(settings, 'DEBUG', False)
                    and getattr(settings, 'ADMIN_DEV_BYPASS', False)
                )
            ):
                self.add_error('password', self.GENERIC_LOGIN_ERROR)
            else:
                self.cleaned_data['username'] = user.get_username()
        return self.cleaned_data

class AdminSetUserPasswordForm(forms.Form):
    password1 = forms.CharField(label='Nueva contraseña', strip=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'}))
    password2 = forms.CharField(label='Confirmar contraseña', strip=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
            return cleaned
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                self.add_error('password1', e.messages)
        return cleaned

class VerificationCodeForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': '000000', 'style': 'letter-spacing: 0.5em; font-size: 1.5em;'}), label='Código de verificación')

class ComplaintResponseForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = ['status', 'severity', 'response']
        widgets = {'status': forms.Select(attrs={'class': 'form-control'}), 'severity': forms.Select(attrs={'class': 'form-control'}), 'response': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escribe la respuesta para el denunciante...', 'rows': 4})}

class ChatMessageForm(forms.ModelForm):

    class Meta:
        model = ChatMessage
        fields = ['message']
        labels = {'message': 'Mensaje'}
        widgets = {'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escribe tu mensaje…', 'rows': 3})}

class ReporterNoteForm(forms.ModelForm):

    class Meta:
        model = ReporterNote
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Agrega una nota relevante…', 'rows': 3})}
    recurrence = forms.ChoiceField(required=False, label='¿Ha ocurrido más de una vez?', choices=[('', 'Selecciona...'), ('si', 'Sí'), ('no', 'No')], widget=forms.Select(attrs={'class': 'form-select'}))
    recurrence_since = forms.CharField(required=False, label='¿Desde cuándo sucede?', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Desde agosto 2025'}))
    immediate_risk = forms.ChoiceField(required=False, label='¿Sientes riesgo inmediato?', choices=[('', 'Selecciona...'), ('si', 'Sí'), ('no', 'No')], widget=forms.Select(attrs={'class': 'form-select'}))
    previous_report = forms.ChoiceField(required=False, label='¿Lo has reportado antes?', choices=[('', 'Selecciona...'), ('si', 'Sí'), ('no', 'No')], widget=forms.Select(attrs={'class': 'form-select'}))
    previous_report_channel = forms.CharField(required=False, label='¿A quién o por qué medio?', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. RRHH, jefe directo, línea de ayuda'}))
    contact_preference = forms.ChoiceField(required=False, label='Preferencia de contacto', choices=[('', 'Selecciona...'), ('email', 'Correo electrónico'), ('phone', 'Celular'), ('no_contact', 'No contactar por ahora')], widget=forms.Select(attrs={'class': 'form-select'}))
    share_permission = forms.ChoiceField(required=False, label='¿Autorizas compartir tu relato con RRHH para investigar?', choices=[('', 'Selecciona...'), ('si', 'Sí'), ('no', 'No')], widget=forms.Select(attrs={'class': 'form-select'}))
    impact_notes = forms.CharField(required=False, label='Impacto en ti (opcional)', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Cómo te afectó emocional o laboralmente'}))

class InvestigationPlanForm(forms.ModelForm):

    class Meta:
        model = InvestigationPlan
        fields = ['objective', 'scope', 'activities', 'key_dates', 'deadline', 'responsible']
        widgets = {
            'objective': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'activities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'key_dates': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'responsible': forms.TextInput(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
        }

class EvidenceItemForm(forms.ModelForm):

    class Meta:
        model = EvidenceItem
        fields = ['kind', 'description', 'obtained_at', 'obtained_by', 'related_fact', 'file']
        widgets = {
            'kind': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento, imagen, audio, etc.', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'obtained_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'obtained_by': forms.TextInput(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'related_fact': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
        }

class FindingForm(forms.ModelForm):

    class Meta:
        model = Finding
        fields = ['code', 'description', 'evidence_refs', 'confirmation', 'risk', 'policy_ref']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'H001', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'evidence_refs': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. E-05, E-07', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'confirmation': forms.Select(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'risk': forms.Select(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'policy_ref': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
        }

class CaseReportForm(forms.ModelForm):

    class Meta:
        model = CaseReport
        fields = ['case_summary', 'case_id', 'start_date', 'end_date', 'complaint_type', 'investigated_facts', 'methodology', 'main_findings', 'conclusion', 'recommendations']
        widgets = {
            'case_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'case_id': forms.TextInput(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'complaint_type': forms.TextInput(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'investigated_facts': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'methodology': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'main_findings': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'conclusion': forms.Select(attrs={'class': 'form-control', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
        }

class InvestigationProcedureForm(forms.ModelForm):

    class Meta:
        model = InvestigationProcedure
        fields = InvestigationProcedure.STEP_FIELDS + ['compliance_owner', 'notes']
        widgets = {
            'compliance_owner': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del responsable de cumplimiento', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones sobre el procedimiento aplicado', 'style': 'width:100%; padding:.55rem .75rem; border:1px solid #e6eef8; border-radius:10px; font-size:.95rem;'}),
        }
        labels = {f: InvestigationProcedure._meta.get_field(f).verbose_name for f in InvestigationProcedure.STEP_FIELDS}

