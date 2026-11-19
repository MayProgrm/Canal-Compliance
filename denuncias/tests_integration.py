import json
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    ChatMessage,
    Complaint,
    ComplaintAttachment,
    ComplaintLog,
    EvidenceItem,
    PrivacyNotice,
    ReporterNote,
)
from .views import (
    REPORTLAB_AVAILABLE,
    _auto_assign_complaint_round_robin,
    _has_conflict_of_interest,
    is_actualizador,
    is_admin,
)


def make_staff(username, password='ValidPass123!', role='', **extra):
    User = get_user_model()
    return User.objects.create_user(
        username=username, password=password, is_staff=True, is_verified=True,
        role=role, **extra,
    )


def make_superuser(username='root', password='ValidPass123!'):
    user = get_user_model().objects.create_superuser(
        username=username, email=f'{username}@example.com', password=password,
    )
    user.is_verified = True
    user.save(update_fields=['is_verified'])
    return user


def make_delegador(username='Delegador', password='DelegadorPass123'):
    User = get_user_model()
    return User.objects.create_user(
        username=username, email='delegador@example.com', password=password,
        is_staff=True, is_verified=True, role='Delegador',
    )


class TemporaryMediaTestCase(TestCase):

    def setUp(self):
        super().setUp()
        from tempfile import TemporaryDirectory
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)


class ComplaintPayloadMixin:

    def denuncia_payload(self, **overrides):
        data = {
            'reporting_mode': 'anonimo',
            'action_type': 'denuncia',
            'category': 'Extorsión',
            'relationship': 'Colaborador',
            'incident_state': 'CDMX',
            'incident_branch': 'Matriz',
            'incident_date': '2024-01-01',
            'incident_time': '10:00',
            'knows_actor': 'False',
            'has_witnesses': 'False',
            'reporter_role': 'Testigo',
            'description': 'Descripción detallada del hecho denunciado de prueba.',
            'password': 'Passw0rd!23',
            'password_confirm': 'Passw0rd!23',
            'terms_accept': 'on',
            'privacy_policies_opened': 'COMETRA',
            'inc_state': 'CDMX',
            'inc_branch': 'Matriz',
            'inc_date': '2024-01-01',
            'inc_time': '10:00',
            'inc_knows_actor': 'false',
            'inc_role': 'Testigo',
            'inc_has_witness': 'false',
        }
        data.update(overrides)
        return data

    def inquietud_payload(self, **overrides):
        data = {
            'reporting_mode': 'anonimo',
            'action_type': 'inquietud',
            'inquietud_category': 'Conflictos de interés',
            'relationship': 'Colaborador',
            'description': 'Duda sobre la aplicación del Código de Ética.',
            'password': 'Passw0rd!23',
            'password_confirm': 'Passw0rd!23',
            'terms_accept': 'on',
            'privacy_policies_opened': 'SEPSA',
        }
        data.update(overrides)
        return data


class PublicPagesRenderTests(TestCase):

    def test_paginas_publicas_clave_responden_200(self):
        for name in (
            'denuncias:home',
            'denuncias:faq',
            'denuncias:guide',
            'denuncias:updates',
            'denuncias:submit_complaint',
            'denuncias:lookup_complaint',
        ):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_abrir_envio_precarga_avisos_de_privacidad(self):
        response = self.client.get(reverse('denuncias:submit_complaint'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PrivacyNotice.objects.filter(is_published=True).exists())


class ComplaintSubmissionTests(TemporaryMediaTestCase, ComplaintPayloadMixin):

    def setUp(self):
        super().setUp()
        cache.clear()
        self.delegador = make_delegador()

    def _submit(self, payload, attachments=None):
        data = dict(payload)
        if attachments is not None:
            data['attachments'] = attachments
        return self.client.post(reverse('denuncias:submit_complaint'), data)

    def test_envio_denuncia_persiste_cifra_password_y_asigna(self):
        response = self._submit(self.denuncia_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('denuncias:complaint_submitted'))

        complaint = Complaint.objects.get()
        self.assertTrue(complaint.folio.startswith('GSI-'))
        self.assertEqual(complaint.action_type, 'denuncia')
        self.assertEqual(complaint.category, 'Extorsión')
        self.assertEqual(complaint.incident_state, 'CDMX')
        self.assertNotEqual(complaint.password, 'Passw0rd!23')
        self.assertTrue(complaint.check_password('Passw0rd!23'))
        self.assertEqual(complaint.assigned_to, self.delegador)
        self.assertTrue(
            ComplaintLog.objects.filter(
                complaint=complaint, action='delegation_pending'
            ).exists()
        )

    def test_envio_conserva_folio_en_sesion_y_renderiza_comprobante(self):
        self._submit(self.denuncia_payload())
        complaint = Complaint.objects.get()
        self.assertEqual(self.client.session.get('last_folio'), complaint.folio)
        rendered = self.client.get(reverse('denuncias:complaint_submitted'))
        self.assertEqual(rendered.status_code, 200)
        self.assertContains(rendered, complaint.folio)

    def test_envio_inquietud_usa_su_categoria(self):
        response = self._submit(self.inquietud_payload())
        self.assertEqual(response.status_code, 302)
        complaint = Complaint.objects.get()
        self.assertEqual(complaint.action_type, 'inquietud')
        self.assertEqual(complaint.category, 'Conflictos de interés')

    def test_envio_con_evidencia_pdf_guarda_adjunto_anonimizado(self):
        upload = SimpleUploadedFile(
            'evidencia_original.pdf', b'%PDF-1.4\ncontenido de prueba',
            content_type='application/pdf',
        )
        response = self._submit(self.denuncia_payload(), attachments=[upload])
        self.assertEqual(response.status_code, 302)
        complaint = Complaint.objects.get()
        self.assertTrue(complaint.attachment)
        self.assertTrue(complaint.attachment.name.startswith('attachments/'))
        self.assertNotIn('evidencia_original', complaint.attachment.name)

    def test_envio_con_multiples_evidencias(self):
        first = SimpleUploadedFile('a.pdf', b'%PDF-1.4\nprimero', content_type='application/pdf')
        second = SimpleUploadedFile('b.png', b'\x89PNG\r\n\x1a\n' + b'x' * 16, content_type='image/png')
        response = self._submit(
            self.denuncia_payload(), attachments=[first, second]
        )
        self.assertEqual(response.status_code, 302)
        complaint = Complaint.objects.get()
        self.assertTrue(complaint.attachment)
        self.assertEqual(ComplaintAttachment.objects.filter(complaint=complaint).count(), 1)

    def test_envio_sin_aceptar_terminos_no_crea_reporte(self):
        payload = self.denuncia_payload()
        payload.pop('terms_accept')
        response = self._submit(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)
        self.assertContains(response, 'Debes confirmar')

    def test_envio_sin_abrir_politica_no_crea_reporte(self):
        payload = self.denuncia_payload()
        payload.pop('privacy_policies_opened')
        response = self._submit(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)
        self.assertContains(response, 'abrir una política de privacidad')

    def test_envio_con_evidencia_invalida_no_crea_reporte(self):
        upload = SimpleUploadedFile(
            'falso.pdf', b'ESTO NO ES UN PDF', content_type='application/pdf'
        )
        response = self._submit(self.denuncia_payload(), attachments=[upload])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)


class EvidenceDownloadTests(TemporaryMediaTestCase, ComplaintPayloadMixin):

    def setUp(self):
        super().setUp()
        cache.clear()
        self.delegador = make_delegador()
        upload = SimpleUploadedFile(
            'prueba.pdf', b'%PDF-1.4\ncontenido evidencia', content_type='application/pdf'
        )
        self.client.post(
            reverse('denuncias:submit_complaint'),
            dict(self.denuncia_payload(), attachments=[upload]),
        )
        self.complaint = Complaint.objects.get()
        self.folio = self.complaint.folio

    def test_denunciante_descarga_su_adjunto_con_sesion(self):
        url = reverse('denuncias:public_download_main_attachment', args=[self.folio])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_descarga_publica_sin_sesion_redirige_a_consulta(self):
        anonymous = Client()
        url = reverse('denuncias:public_download_main_attachment', args=[self.folio])
        response = anonymous.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('denuncias:lookup_complaint'), response.url)

    def test_superusuario_descarga_adjunto_y_queda_log(self):
        root = make_superuser()
        self.client.force_login(root)
        url = reverse('denuncias:admin_download_main_attachment', args=[self.complaint.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ComplaintLog.objects.filter(
                complaint=self.complaint, action='file_access'
            ).exists()
        )

    def test_analista_no_asignado_no_puede_descargar(self):
        analyst = make_staff('analista_sin_asignar')
        self.client.force_login(analyst)
        url = reverse('denuncias:admin_download_main_attachment', args=[self.complaint.id])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_analista_asignado_descarga_evidencia(self):
        analyst = make_staff('analista_asignado')
        self.complaint.assigned_to = analyst
        self.complaint.save(update_fields=['assigned_to'])
        evidence = EvidenceItem.objects.create(
            complaint=self.complaint, kind='Documento', description='Evidencia',
            file=SimpleUploadedFile('ev.pdf', b'%PDF-1.4\nx', content_type='application/pdf'),
        )
        self.client.force_login(analyst)
        url = reverse(
            'denuncias:admin_download_evidence',
            args=[self.complaint.id, evidence.id],
        )
        self.assertEqual(self.client.get(url).status_code, 200)


class ReporterLookupChatTests(TestCase):

    def setUp(self):
        cache.clear()
        self.complaint = Complaint.objects.create(
            description='Caso de consulta', email='user@example.com', phone='5512345678',
        )
        self.complaint.set_password('ClaveSegura1!')
        self.complaint.save(update_fields=['password'])

    def _authenticate(self):
        response = self.client.post(
            reverse('denuncias:lookup_complaint'),
            {'folio': self.complaint.folio, 'password': 'ClaveSegura1!'},
        )
        self.assertEqual(response.status_code, 302)
        return response

    def test_consulta_valida_abre_expediente_y_cuenta(self):
        self._authenticate()
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.lookup_count, 1)
        page = self.client.get(
            reverse('denuncias:lookup_complaint') + f'?folio={self.complaint.folio}'
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'u***@example.com')
        self.assertContains(page, '*** *** **78')

    def test_consulta_con_password_incorrecta_no_autentica(self):
        response = self.client.post(
            reverse('denuncias:lookup_complaint'),
            {'folio': self.complaint.folio, 'password': 'incorrecta'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contraseña incorrecta')
        self.assertNotIn(f'auth_folio_{self.complaint.folio}', self.client.session)

    def test_consulta_folio_inexistente_muestra_aviso(self):
        response = self.client.post(
            reverse('denuncias:lookup_complaint'),
            {'folio': 'GSI-NOEXIS', 'password': 'x'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontró')

    def test_chat_denunciante_requiere_sesion_autenticada(self):
        url = reverse('denuncias:submit_chat_message', args=[self.complaint.folio])
        response = self.client.post(url, {'message': 'hola'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_chat_denunciante_guarda_mensaje(self):
        self._authenticate()
        url = reverse('denuncias:submit_chat_message', args=[self.complaint.folio])
        response = self.client.post(url, {'message': 'Mensaje de seguimiento'})
        self.assertEqual(response.status_code, 302)
        message = ChatMessage.objects.get()
        self.assertEqual(message.sender, 'reporter')
        self.assertEqual(message.message, 'Mensaje de seguimiento')

    def test_nota_denunciante_se_persiste(self):
        self._authenticate()
        url = reverse('denuncias:add_reporter_note', args=[self.complaint.folio])
        response = self.client.post(url, {'content': 'Nota adicional'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReporterNote.objects.get().content, 'Nota adicional')

    def test_administrador_responde_en_chat(self):
        root = make_superuser()
        self.client.force_login(root)
        url = reverse('denuncias:admin_send_chat_message', args=[self.complaint.id])
        response = self.client.post(url, {'message': 'Respuesta del equipo'})
        self.assertEqual(response.status_code, 302)
        message = ChatMessage.objects.get()
        self.assertEqual(message.sender, 'admin')

    def test_comprobante_pdf_y_qr_disponibles_con_sesion(self):
        self._authenticate()
        qr = self.client.get(reverse('denuncias:public_ticket_qr', args=[self.complaint.folio]))
        self.assertEqual(qr.status_code, 200)
        pdf = self.client.get(reverse('denuncias:public_ticket_pdf', args=[self.complaint.folio]))
        if REPORTLAB_AVAILABLE:
            self.assertEqual(pdf.status_code, 200)
        else:
            self.assertEqual(pdf.status_code, 404)


class AdminRolePermissionTests(TestCase):

    def setUp(self):
        cache.clear()
        self.superuser = make_superuser('root')
        self.analista = make_staff('analista', role='')
        self.delegador = make_delegador()
        self.actualizador = make_staff('actualizador', role='actualizador')

    def _login(self, user):
        self.client.force_login(user)
        return self.client

    def test_reglas_de_rol(self):
        self.assertTrue(is_admin(self.analista))
        self.assertFalse(is_actualizador(self.analista))
        self.assertFalse(is_admin(self.actualizador))
        self.assertTrue(is_actualizador(self.actualizador))
        self.assertTrue(is_admin(self.delegador))
        self.assertTrue(is_admin(self.superuser))
        self.assertTrue(is_actualizador(self.superuser))

    def test_analista_accede_a_dashboard_y_no_a_roles(self):
        self._login(self.analista)
        self.assertEqual(self.client.get(reverse('denuncias:admin_dashboard')).status_code, 200)
        response = self.client.get(reverse('denuncias:admin_roles'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('denuncias:admin_dashboard')))

    def test_delegador_se_redirige_a_su_bandeja(self):
        self._login(self.delegador)
        response = self.client.get(reverse('denuncias:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('denuncias:delegador_queue'))
        self.assertEqual(self.client.get(reverse('denuncias:delegador_queue')).status_code, 200)

    def test_actualizador_accede_a_su_panel(self):
        self._login(self.actualizador)
        response = self.client.get(reverse('denuncias:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('denuncias:actualizador_dashboard'))
        self.assertEqual(
            self.client.get(reverse('denuncias:actualizador_dashboard')).status_code, 200
        )

    def test_superusuario_accede_a_secciones_privilegiadas(self):
        self._login(self.superuser)
        for name in (
            'denuncias:admin_dashboard',
            'denuncias:admin_roles',
            'denuncias:admin_settings',
            'denuncias:admin_sessions',
            'denuncias:admin_stats',
        ):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_anonimo_es_redirigido_al_login(self):
        response = self.client.get(reverse('denuncias:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('denuncias:admin_login'), response.url)


class AdminUserCreationTests(TestCase):

    def setUp(self):
        cache.clear()
        self.superuser = make_superuser('root')
        self.client.force_login(self.superuser)

    def _payload(self, **overrides):
        data = {
            'username': 'nuevo_analista',
            'email': 'nuevo@example.com',
            'first_name': 'Nuevo',
            'last_name': 'Analista',
            'phone_number': '5512345678',
            'role': '',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        }
        data.update(overrides)
        return data

    def test_superusuario_crea_analista_verificado(self):
        response = self.client.post(
            reverse('denuncias:admin_create_admin_user'), self._payload()
        )
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='nuevo_analista')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_verified)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('ClaveSegura123!'))

    def test_crea_actualizador_con_su_rol(self):
        self.client.post(
            reverse('denuncias:admin_create_admin_user'),
            self._payload(username='nuevo_actua', role='actualizador'),
        )
        user = get_user_model().objects.get(username='nuevo_actua')
        self.assertEqual(user.role, 'actualizador')
        self.assertTrue(is_actualizador(user))

    def test_username_reservado_es_rechazado(self):
        response = self.client.post(
            reverse('denuncias:admin_create_admin_user'),
            self._payload(username='Delegador'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='Delegador').exists())
        self.assertContains(response, 'reservado')

    def test_password_debil_es_rechazada(self):
        response = self.client.post(
            reverse('denuncias:admin_create_admin_user'),
            self._payload(password1='123', password2='123'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='nuevo_analista').exists())

    def test_no_superusuario_no_puede_crear_usuarios(self):
        self.client.force_login(make_staff('analista', role=''))
        response = self.client.post(
            reverse('denuncias:admin_create_admin_user'), self._payload()
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(get_user_model().objects.filter(username='nuevo_analista').exists())


class ReceptionAndDeliveryTests(TemporaryMediaTestCase, ComplaintPayloadMixin):

    def setUp(self):
        super().setUp()
        cache.clear()

    def test_asignacion_automatica_round_robin_alterna(self):
        make_staff('analista_1', assignment_position=1)
        make_staff('analista_2', assignment_position=2)
        complaint_a = Complaint.objects.create(description='Caso A')
        complaint_b = Complaint.objects.create(description='Caso B')

        _auto_assign_complaint_round_robin(complaint_a)
        _auto_assign_complaint_round_robin(complaint_b)

        complaint_a.refresh_from_db()
        complaint_b.refresh_from_db()
        self.assertIsNotNone(complaint_a.assigned_to)
        self.assertIsNotNone(complaint_b.assigned_to)
        self.assertNotEqual(complaint_a.assigned_to_id, complaint_b.assigned_to_id)
        self.assertEqual(
            ComplaintLog.objects.filter(action='auto_assign').count(), 2
        )

    def test_conflicto_de_interes_excluye_al_administrador(self):
        admin = make_staff('ana_lopez', first_name='Ana', last_name='Lopez')
        con_conflicto = Complaint.objects.create(description='x', actor_name='Ana Lopez')
        sin_conflicto = Complaint.objects.create(description='y', actor_name='Otro')
        self.assertTrue(_has_conflict_of_interest(admin, con_conflicto))
        self.assertFalse(_has_conflict_of_interest(admin, sin_conflicto))

    def test_delegador_admite_y_entrega_caso_a_analista(self):
        delegador = make_delegador()
        analyst = make_staff('analista_destino', role='')
        complaint = Complaint.objects.create(
            description='Caso por delegar', status='enviado', assigned_to=delegador,
        )
        self.client.force_login(delegador)
        response = self.client.post(
            reverse('denuncias:admin_complaint_detail', args=[complaint.id]),
            {'accept': '1', 'assign_to': str(analyst.id)},
        )
        self.assertEqual(response.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'admitido')
        self.assertEqual(complaint.assigned_to, analyst)
        self.assertTrue(
            ComplaintLog.objects.filter(
                complaint=complaint, action='delegador_accept'
            ).exists()
        )

    def test_delegador_no_puede_cambiar_estado_manualmente(self):
        delegador = make_delegador()
        complaint = Complaint.objects.create(
            description='Caso enviado', status='enviado', assigned_to=delegador,
        )
        self.client.force_login(delegador)
        self.client.post(
            reverse('denuncias:admin_complaint_detail', args=[complaint.id]),
            {'update_status': '1', 'status': 'resuelto'},
        )
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, 'enviado')


class DataPersistenceTests(TestCase):

    def test_complaint_guarda_password_hasheada(self):
        complaint = Complaint.objects.create(description='persistencia')
        complaint.set_password('Secreta123!')
        complaint.save(update_fields=['password'])
        stored = Complaint.objects.get(pk=complaint.pk)
        self.assertNotEqual(stored.password, 'Secreta123!')
        self.assertTrue(stored.check_password('Secreta123!'))

    def test_folio_generado_y_unico(self):
        first = Complaint.objects.create(description='primera')
        second = Complaint.objects.create(description='segunda')
        self.assertTrue(first.folio.startswith('GSI-'))
        self.assertNotEqual(first.folio, second.folio)

    def test_verificacion_de_codigo_de_admin(self):
        user = make_staff('verificable')
        user.is_verified = False
        user.save(update_fields=['is_verified'])
        code = user.generate_verification_code()
        self.assertEqual(len(code), 6)
        user.refresh_from_db()
        self.assertTrue(user.verification_code_expires > timezone.now())


class MobileAppAPIContractTests(TemporaryMediaTestCase):

    def setUp(self):
        super().setUp()
        cache.clear()

    def _create_via_api(self):
        return self.client.post(
            reverse('api:complaint-create'),
            data=json.dumps({
                'action_type': 'denuncia',
                'description': 'Reporte creado desde la app',
                'password': 'Passw0rd!23',
                'privacy_policies_opened': 'COMETRA',
                'terms_accept': True,
            }),
            content_type='application/json',
        )

    def test_api_root_lista_endpoints(self):
        response = self.client.get(reverse('api:root'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('endpoints', response.json())

    def test_api_crea_denuncia_y_devuelve_folio(self):
        response = self._create_via_api()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['folio'].startswith('GSI-'))
        self.assertTrue(Complaint.objects.filter(folio=response.json()['folio']).exists())

    def test_api_rechaza_sin_aceptar_terminos(self):
        response = self.client.post(
            reverse('api:complaint-create'),
            data=json.dumps({
                'description': 'x', 'password': 'Passw0rd!23',
                'privacy_policies_opened': 'COMETRA', 'terms_accept': False,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_api_consulta_exige_password_correcta(self):
        complaint = Complaint.objects.create(description='Caso API')
        complaint.set_password('Passw0rd!23')
        complaint.save(update_fields=['password'])

        missing = self.client.post(
            reverse('api:complaint-lookup'),
            data=json.dumps({'folio': complaint.folio}),
            content_type='application/json',
        )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(missing.json()['error'], 'password_required')

        ok = self.client.post(
            reverse('api:complaint-lookup'),
            data=json.dumps({'folio': complaint.folio, 'password': 'Passw0rd!23'}),
            content_type='application/json',
        )
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()['folio'], complaint.folio)

    def test_api_chat_crea_mensaje_del_denunciante(self):
        complaint = Complaint.objects.create(description='Caso chat')
        complaint.set_password('Passw0rd!23')
        complaint.save(update_fields=['password'])
        response = self.client.post(
            reverse('api:complaint-chat'),
            data=json.dumps({
                'folio': complaint.folio, 'password': 'Passw0rd!23',
                'message': 'Hola desde la app',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ChatMessage.objects.get().sender, 'reporter')

    def test_api_descarga_adjunto_firmado(self):
        upload = SimpleUploadedFile(
            'app.pdf', b'%PDF-1.4\napp', content_type='application/pdf'
        )
        complaint = Complaint.objects.create(description='Caso adjunto')
        complaint.attachment = upload
        complaint.set_password('Passw0rd!23')
        complaint.save()

        listing = self.client.post(
            reverse('api:complaint-attachments'),
            data=json.dumps({'folio': complaint.folio, 'password': 'Passw0rd!23'}),
            content_type='application/json',
        )
        self.assertEqual(listing.status_code, 200)
        download_url = listing.json()['attachments'][0]['download_url']
        path = urlparse(download_url).path
        self.assertEqual(self.client.get(path).status_code, 200)

    def test_api_token_de_descarga_invalido_es_rechazado(self):
        url = reverse('api:complaint-attachment-download', kwargs={'token': 'token-falso'})
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_api_aviso_de_privacidad_publicado(self):
        PrivacyNotice.objects.create(company='COMETRA', is_published=True)
        response = self.client.get(reverse('api:privacy-notices'))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 1)
