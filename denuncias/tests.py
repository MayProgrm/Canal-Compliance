import json
import re
from pathlib import Path

from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from django.utils import timezone
from django.conf import settings
from tempfile import TemporaryDirectory
from .forms import AdminLoginForm, ComplaintForm
from .models import Complaint
from .api.serializers import ComplaintCreateSerializer
from .views import _client_ip


class TemporaryMediaTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)


class ComplaintAPIUploadValidationTests(TestCase):

    def _serializer(self, upload):
        return ComplaintCreateSerializer(data={
            'description': 'Prueba de carga',
            'password': 'clave temporal',
            'privacy_policies_opened': 'aviso abierto',
            'terms_accept': True,
            'attachments': [upload],
        })

    def test_api_rejects_html_attachment(self):
        upload = SimpleUploadedFile(
            'payload.html',
            b'<script>alert(1)</script>',
            content_type='text/html',
        )
        serializer = self._serializer(upload)
        self.assertFalse(serializer.is_valid())
        self.assertIn('attachments', serializer.errors)

    def test_api_rejects_oversized_attachment(self):
        upload = SimpleUploadedFile(
            'large.pdf',
            b'%PDF-' + b'x' * settings.MAX_UPLOAD_SIZE,
            content_type='application/pdf',
        )
        serializer = self._serializer(upload)
        self.assertFalse(serializer.is_valid())
        self.assertIn('attachments', serializer.errors)


class LocalAdminLoginCsrfFallbackTests(TestCase):

    def setUp(self):
        cache.clear()

    def _post_login(self, origin='null', token_override=None):
        client = Client(enforce_csrf_checks=True)
        path = '/denuncias/admin/login/'
        host = '127.0.0.1:8000'
        page = client.get(path, HTTP_HOST=host)
        token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            page.content.decode(),
        ).group(1)
        response = client.post(
            path,
            {
                'csrfmiddlewaretoken': token_override or token,
                'username': '__diagnostico_invalido__',
                'password': 'no-validar',
            },
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
        )
        return response

    @override_settings(DEBUG=True)
    def test_local_null_origin_passes_when_csrf_token_is_valid(self):
        response = self._post_login()
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            AdminLoginForm.GENERIC_LOGIN_ERROR,
        )

    @override_settings(DEBUG=True)
    def test_local_null_origin_still_rejects_invalid_csrf_token(self):
        response = self._post_login(token_override='token-invalido')
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_null_origin_remains_rejected_outside_debug(self):
        response = self._post_login()
        self.assertEqual(response.status_code, 403)


class AttachmentValidationTests(TestCase):

    def test_valid_pdf_signature_passes(self):
        pdf_content = b'%PDF-1.4\n%...'
        upload = SimpleUploadedFile('test.pdf', pdf_content, content_type='application/pdf')
        form = ComplaintForm(data={
            'description': 'Denuncia PDF',
            'relationship': 'Colaborador',
            'reporting_mode': 'anonimo',
            'action_type': 'denuncia',
            'category': 'Extorsión',
            'incident_state': 'CDMX',
            'incident_branch': 'Matriz',
            'incident_date': '2023-01-01',
            'incident_time': '12:00',
            'knows_actor': 'False',
            'has_witnesses': 'False',
            'reporter_role': 'Testigo',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
        }, files={'attachment': upload})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_pdf_signature_fails(self):
        bad_pdf = b'NOTPDFCONTENT'
        upload = SimpleUploadedFile('bad.pdf', bad_pdf, content_type='application/pdf')
        form = ComplaintForm(data={
            'description': 'Denuncia PDF',
            'relationship': 'Colaborador',
            'reporting_mode': 'anonimo',
            'action_type': 'denuncia',
            'category': 'Extorsión',
            'incident_state': 'CDMX',
            'incident_branch': 'Matriz',
            'incident_date': '2023-01-01',
            'incident_time': '12:00',
            'knows_actor': 'False',
            'has_witnesses': 'False',
            'reporter_role': 'Testigo',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
        }, files={'attachment': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('El contenido no coincide con un PDF válido.', form.errors.get('attachment', [''])[0])

    def test_valid_png_signature_passes(self):
        png_header = b'\x89PNG\r\n\x1a\n' + b'0' * 32
        upload = SimpleUploadedFile('img.png', png_header, content_type='image/png')
        form = ComplaintForm(data={
            'description': 'Denuncia imagen',
            'relationship': 'Colaborador',
            'reporting_mode': 'anonimo',
            'action_type': 'denuncia',
            'category': 'Extorsión',
            'incident_state': 'CDMX',
            'incident_branch': 'Matriz',
            'incident_date': '2023-01-01',
            'incident_time': '12:00',
            'knows_actor': 'False',
            'has_witnesses': 'False',
            'reporter_role': 'Testigo',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
        }, files={'attachment': upload})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_docx_signature_fails(self):
        not_zip = b'RANDOMBYTESNOTZIP'
        upload = SimpleUploadedFile('file.docx', not_zip, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        form = ComplaintForm(data={
            'description': 'Denuncia docx',
            'relationship': 'Colaborador',
            'reporting_mode': 'anonimo',
            'action_type': 'denuncia',
            'category': 'Extorsión',
            'incident_state': 'CDMX',
            'incident_branch': 'Matriz',
            'incident_date': '2023-01-01',
            'incident_time': '12:00',
            'knows_actor': 'False',
            'has_witnesses': 'False',
            'reporter_role': 'Testigo',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
        }, files={'attachment': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('archivo Office válido', form.errors.get('attachment', [''])[0])

class AttachmentNameSanitizationTests(TemporaryMediaTestCase):

    def test_attachment_filename_randomized(self):
        upload = SimpleUploadedFile('very_sensitive_name.pdf', b'%PDF-1.4\n...', content_type='application/pdf')
        c = Complaint.objects.create(description='Prueba adjunto', attachment=upload)
        self.assertTrue(c.attachment.name.startswith('attachments/'))
        self.assertFalse('very_sensitive_name' in c.attachment.name)
        self.assertTrue(c.attachment.name.endswith('.pdf'))

class LookupMaskingTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_lookup_masks_email_and_phone(self):
        c = Complaint.objects.create(description='Contenido', email='user@example.com', phone='5512345678')
        c.set_password('clave-segura')
        c.save(update_fields=['password'])
        post_url = reverse('lookup_complaint')
        resp = self.client.post(post_url, {'folio': c.folio, 'password': 'clave-segura'})
        self.assertIn(resp.status_code, (200, 302))
        url = reverse('lookup_complaint') + f'?folio={c.folio}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'u***@example.com')
        self.assertContains(resp, '*** *** **78')

class RateLimitLoginTests(TestCase):

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(username='admin', email='admin@example.com', password='pass12345')
        self.user.is_staff = True
        self.user.is_verified = True
        self.user.save()
        self.client = Client()

    def test_login_rate_limit_blocks_after_five_failed(self):
        url = reverse('admin_login')
        for _ in range(5):
            resp = self.client.post(url, {'username': 'admin', 'password': 'wrong'})
            self.assertEqual(resp.status_code, 200)
        resp = self.client.post(url, {'username': 'admin', 'password': 'wrong'})
        messages = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any(('Demasiados intentos' in m for m in messages)))

    def test_login_success_resets_attempts(self):
        url = reverse('admin_login')
        self.client.post(url, {'username': 'admin', 'password': 'wrong'})
        resp = self.client.post(url, {'username': 'admin', 'password': 'pass12345'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_dashboard'))
        self.assertEqual(self.client.session.get('login_attempts', []), [])

class RateLimitSubmitComplaintTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client = Client()

    def _post_valid_complaint(self):
        data = {
            'description': 'Contenido de prueba',
            'relationship': 'Colaborador',
            'reporting_mode': 'anonimo',
            'action_type': 'denuncia',
            'category': 'Extorsión',
            'incident_state': 'CDMX',
            'incident_branch': 'Matriz',
            'incident_date': '2023-01-01',
            'incident_time': '12:00',
            'knows_actor': 'False',
            'has_witnesses': 'False',
            'reporter_role': 'Testigo',
            'password': 'pass12345',
            'password_confirm': 'pass12345',
            'terms_accept': 'on',
            'privacy_policies_opened': 'Política de privacidad Empresa 1',
        }
        return self.client.post(reverse('submit_complaint'), data)

    def test_submit_rate_limit_blocks_after_three(self):
        for _ in range(3):
            resp = self._post_valid_complaint()
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.url, reverse('denuncias:complaint_submitted'))
        resp = self._post_valid_complaint()
        messages = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any(('límite de envíos' in m for m in messages)))
        self.assertContains(resp, 'Enviar reporte', status_code=429)

class AdminResetComplaintsTests(TemporaryMediaTestCase):

    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.superuser = User.objects.create_superuser('root', 'root@example.com', 'Admin12345')
        self.client = Client()
        self.client.login(username='root', password='Admin12345')

    def test_reset_requires_post(self):
        resp = self.client.get(reverse('admin_reset_complaints'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_dashboard'))

    @override_settings(DEBUG=False)
    def test_reset_blocks_in_production(self):
        c = Complaint.objects.create(description='Prueba', name='N', email='e@example.com')
        resp = self.client.post(reverse('admin_reset_complaints'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_dashboard'))
        self.assertEqual(Complaint.objects.count(), 1)

    @override_settings(DEBUG=True)
    def test_reset_deletes_complaints_in_debug(self):
        upload = SimpleUploadedFile('file.txt', b'contenido', content_type='text/plain')
        c = Complaint.objects.create(description='Prueba', name='N', email='e@example.com', attachment=upload)
        self.assertEqual(Complaint.objects.count(), 1)
        resp = self.client.post(reverse('admin_reset_complaints'), {
            'confirm': 'CONFIRMAR',
            'admin_password': 'Admin12345',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Complaint.objects.count(), 0)

    @override_settings(DEBUG=True)
    def test_reset_requires_confirmation_and_password(self):
        Complaint.objects.create(description='Prueba', name='N', email='e@example.com')
        resp = self.client.post(reverse('admin_reset_complaints'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Complaint.objects.count(), 1)

    @override_settings(DEBUG=True)
    def test_reset_post_requires_csrf_token(self):
        complaint = Complaint.objects.create(description='Prueba', name='N', email='e@example.com')
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.superuser)
        resp = client.post(reverse('admin_reset_complaints'), {
            'confirm': 'CONFIRMAR',
            'admin_password': 'Admin12345',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Complaint.objects.filter(pk=complaint.pk).exists())

class AdminVerificationTests(TestCase):

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user('jefe', 'jefe@example.com', 'Segura123')
        self.user.is_staff = True
        self.user.is_verified = False
        self.user.save()
        self.client = Client()

    def test_valid_code_verifies_and_logs_in(self):
        code = self.user.generate_verification_code()
        url = reverse('admin_verify', args=[self.user.id])
        resp = self.client.post(url, {'code': code})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_dashboard'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    @override_settings(DEBUG=True, ADMIN_DEV_BYPASS=True)
    def test_debug_does_not_bypass_verification_code(self):
        self.user.verification_code = '123456'
        self.user.verification_code_expires = timezone.now() + timezone.timedelta(minutes=10)
        self.user.save()
        resp = self.client.post(
            reverse('admin_verify', args=[self.user.id]),
            {'code': '000000'},
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)
        self.assertNotIn('_auth_user_id', self.client.session)

class AdminDashboardViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('admin_user', 'admin_user@example.com', 'AdminPass123')
        self.user.is_staff = True
        self.user.is_verified = True
        self.user.save()
        self.client = Client()
        self.client.login(username='admin_user', password='AdminPass123')

    def test_admin_dashboard_access(self):
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('status_cards', resp.context)
        self.assertIn('mini_cards', resp.context)
        self.assertIn('denuncias', resp.context)
        self.assertIn('consultas', resp.context)

class AdminRoleLoginFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def _assert_role_login(
        self,
        username,
        role,
        destination,
        login_identifier=None,
        email='',
    ):
        user = get_user_model().objects.create_user(
            username=username,
            email=email,
            password='ValidPass123!',
            role=role,
            is_staff=True,
            is_verified=True,
        )
        response = self.client.post(
            reverse('denuncias:admin_login'),
            {
                'username': login_identifier or username,
                'password': 'ValidPass123!',
            },
        )
        self.assertRedirects(
            response,
            reverse(destination),
            fetch_redirect_response=False,
        )
        panel_response = self.client.get(response.url)
        self.assertEqual(panel_response.status_code, 200)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_actualizador_can_login_and_open_own_panel(self):
        self._assert_role_login(
            'Actua',
            'Actualizador',
            'denuncias:actualizador_dashboard',
            login_identifier='actua',
        )

    def test_delegador_can_login_and_open_own_panel(self):
        self._assert_role_login(
            'Delegador',
            'Delegador',
            'denuncias:delegador_queue',
            login_identifier='delegador@example.com',
            email='delegador@example.com',
        )


class AdminLoginGenericErrorTests(TestCase):
    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.staff_user = User.objects.create_user(
            username='staff_login_test',
            password='ValidPass123!',
            is_staff=True,
            is_verified=True,
        )
        User.objects.create_user(
            username='public_login_test',
            password='ValidPass123!',
        )
        User.objects.create_user(
            username='unverified_admin_test',
            password='ValidPass123!',
            is_staff=True,
            is_verified=False,
        )
        self.client = Client()

    def test_unknown_wrong_password_and_nonstaff_use_same_error(self):
        attempts = (
            ('missing_login_test', 'AnyPass123!'),
            ('staff_login_test', 'WrongPass123!'),
            ('public_login_test', 'ValidPass123!'),
            ('unverified_admin_test', 'ValidPass123!'),
        )
        form_errors = []
        for username, password in attempts:
            response = self.client.post(
                reverse('denuncias:admin_login'),
                {'username': username, 'password': password},
            )
            self.assertEqual(response.status_code, 200)
            form = response.context['form']
            self.assertEqual(
                form['password'].errors,
                [AdminLoginForm.GENERIC_LOGIN_ERROR],
            )
            self.assertFalse(form['username'].errors)
            form_errors.append(form.errors.as_json())

        self.assertEqual(form_errors[0], form_errors[1])
        self.assertEqual(form_errors[1], form_errors[2])
        self.assertEqual(form_errors[2], form_errors[3])

    def test_unverified_staff_cannot_open_admin_panels_directly(self):
        user = get_user_model().objects.get(username='unverified_admin_test')
        user.role = 'Delegador'
        user.save(update_fields=['role'])
        self.client.force_login(user)

        for panel in (
            'denuncias:admin_dashboard',
            'denuncias:delegador_queue',
        ):
            response = self.client.get(reverse(panel))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('denuncias:admin_login')))


class DelegadorPanelViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('Delegador', 'delegador@example.com', 'Delegador123')
        self.user.is_staff = True
        self.user.is_verified = True
        setattr(self.user, 'role', 'Delegador')
        self.user.save()
        self.client = Client()
        self.client.login(username='Delegador', password='Delegador123')

    def test_delegador_redirect_from_admin_dashboard(self):
        resp = self.client.get(reverse('denuncias:admin_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('denuncias:delegador_queue'))

    def test_delegador_queue_access(self):
        resp = self.client.get(reverse('denuncias:delegador_queue'))
        self.assertEqual(resp.status_code, 200)


class SecurityHardeningTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_chatbot_widget_no_usa_innerhtml_con_datos_dinamicos(self):
        template = Path(settings.BASE_DIR) / 'templates' / 'denuncias' / 'chatbot_widget.html'
        content = template.read_text(encoding='utf-8')
        self.assertIn('renderMessageContent', content)
        self.assertNotIn('div.innerHTML = html', content)

    def test_csp_usa_nonce_y_no_unsafe_inline_en_scripts(self):
        response = self.client.get(reverse('denuncias:home'))
        csp = response.headers.get('Content-Security-Policy', '')
        script_src = csp.split('script-src', 1)[1].split(';', 1)[0]
        self.assertIn("'nonce-", script_src)
        self.assertNotIn('unsafe-inline', script_src)
        nonce = csp.split("'nonce-", 1)[1].split("'", 1)[0]
        self.assertTrue(nonce)
        self.assertIn(f'nonce="{nonce}"', response.content.decode('utf-8'))

    def test_csp_nonce_es_unico_por_peticion(self):
        first = self.client.get(reverse('denuncias:home')).headers.get('Content-Security-Policy', '')
        second = self.client.get(reverse('denuncias:home')).headers.get('Content-Security-Policy', '')
        self.assertNotEqual(first, second)

    def test_chatbot_rechaza_post_sin_token_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse('denuncias:public_chatbot'),
            data=json.dumps({'message': 'hola', 'init': True}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_chatbot_acepta_token_csrf_valido(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse('denuncias:home'))
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        response = client.post(
            reverse('denuncias:public_chatbot'),
            data=json.dumps({'message': 'hola', 'init': True}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('response', response.json())

    def test_login_legacy_exige_usuario_verificado_y_mensaje_generico(self):
        user = get_user_model().objects.create_user(
            username='staff_no_verificado',
            password='ValidPass123!',
            is_staff=True,
            is_verified=False,
        )
        response = self.client.post(
            reverse('denuncias:login'),
            {'username': user.username, 'password': 'ValidPass123!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, AdminLoginForm.GENERIC_LOGIN_ERROR)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(USE_X_FORWARDED_FOR=False)
    def test_client_ip_ignora_xff_falsificado_por_defecto(self):
        request = RequestFactory().get(
            '/', REMOTE_ADDR='10.0.0.5', HTTP_X_FORWARDED_FOR='1.2.3.4'
        )
        self.assertEqual(_client_ip(request), '10.0.0.5')

    @override_settings(USE_X_FORWARDED_FOR=True, TRUSTED_PROXY_COUNT=1)
    def test_client_ip_usa_ultimo_salto_de_proxy_confiable(self):
        request = RequestFactory().get(
            '/', REMOTE_ADDR='10.0.0.5',
            HTTP_X_FORWARDED_FOR='1.2.3.4, 203.0.113.9',
        )
        self.assertEqual(_client_ip(request), '203.0.113.9')

    def test_api_chat_no_acepta_get(self):
        self.assertEqual(
            self.client.get(reverse('api:complaint-chat')).status_code, 405
        )

    def test_api_attachments_no_acepta_get(self):
        self.assertEqual(
            self.client.get(reverse('api:complaint-attachments')).status_code, 405
        )

    def test_api_chat_ignora_password_en_query_string(self):
        complaint = Complaint.objects.create(folio='GSI-SEC001', description='prueba')
        complaint.set_password('ClaveSegura1!')
        complaint.save()
        response = self.client.post(
            reverse('api:complaint-chat') + '?password=ClaveSegura1!',
            data=json.dumps({'folio': 'GSI-SEC001'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get('error'), 'password_required')

    def test_actualizador_no_puede_descargar_adjuntos_admin(self):
        user = get_user_model().objects.create_user(
            username='actualizador_dl',
            password='ValidPass123!',
            is_staff=True,
            is_verified=True,
        )
        user.role = 'Actualizador'
        user.save(update_fields=['role'])
        self.client.force_login(user)
        url = reverse('denuncias:admin_download_attachment', args=[1, 1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_chatbot_limita_peticiones_por_ip(self):
        url = reverse('denuncias:public_chatbot')
        payload = json.dumps({'message': 'hola'})
        status_codes = [
            self.client.post(url, data=payload, content_type='application/json').status_code
            for _ in range(31)
        ]
        self.assertIn(403, status_codes)
