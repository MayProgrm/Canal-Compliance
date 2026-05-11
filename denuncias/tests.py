from django.test import TestCase
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from django.utils import timezone
from .forms import ComplaintForm
from .models import Complaint

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

class AttachmentNameSanitizationTests(TestCase):

    def test_attachment_filename_randomized(self):
        upload = SimpleUploadedFile('very_sensitive_name.pdf', b'%PDF-1.4\n...', content_type='application/pdf')
        c = Complaint.objects.create(description='Prueba adjunto', attachment=upload)
        self.assertTrue(c.attachment.name.startswith('attachments/'))
        self.assertFalse('very_sensitive_name' in c.attachment.name)
        self.assertTrue(c.attachment.name.endswith('.pdf'))

class LookupMaskingTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_lookup_masks_email_and_phone(self):
        c = Complaint.objects.create(description='Contenido', email='user@example.com', phone='5512345678')
        # Authenticate session for this folio by posting (no password required)
        post_url = reverse('lookup_complaint')
        resp = self.client.post(post_url, {'folio': c.folio})
        self.assertIn(resp.status_code, (200, 302))
        url = reverse('lookup_complaint') + f'?folio={c.folio}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'u***@example.com')
        self.assertContains(resp, '*** *** **78')

class RateLimitLoginTests(TestCase):

    def setUp(self):
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
            # Success uses PRG pattern -> redirect to submitted page
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.url, reverse('denuncias:complaint_submitted'))
        resp = self._post_valid_complaint()
        messages = [m.message for m in get_messages(resp.wsgi_request)]
        self.assertTrue(any(('límite de envíos' in m for m in messages)))
        self.assertContains(resp, 'Enviar un reporte', status_code=200)

class AdminResetComplaintsTests(TestCase):

    def setUp(self):
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
        resp = self.client.post(reverse('admin_reset_complaints'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Complaint.objects.count(), 0)

class AdminVerificationTests(TestCase):

    def setUp(self):
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
