package com.example.canaldedenunciasgsi

import com.example.canaldedenunciasgsi.data.remote.ApiErrorResponse
import com.example.canaldedenunciasgsi.data.remote.AttachmentsResponse
import com.example.canaldedenunciasgsi.data.remote.ChatListResponse
import com.example.canaldedenunciasgsi.data.remote.CreateComplaintResponse
import com.example.canaldedenunciasgsi.data.remote.LookupResponse
import com.example.canaldedenunciasgsi.data.remote.PrivacyNoticeDto
import com.google.gson.Gson
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Deserializa con Gson las mismas respuestas que entrega el servidor del canal
 * para confirmar que el contrato (nombres de campos) sigue siendo válido.
 */
class ApiModelsTest {

    private val gson = Gson()

    @Test
    fun createComplaintResponse_parsesServerJson() {
        val json = """
            {
              "folio": "DEN-2026-000123",
              "status": "nuevo",
              "status_display": "Nuevo",
              "severity": "media",
              "severity_display": "Media",
              "created_at": "2026-11-19T10:15:00Z"
            }
        """.trimIndent()

        val response = gson.fromJson(json, CreateComplaintResponse::class.java)

        assertEquals("DEN-2026-000123", response.folio)
        assertEquals("nuevo", response.status)
        assertEquals("Nuevo", response.statusDisplay)
        assertEquals("media", response.severity)
        assertEquals("Media", response.severityDisplay)
        assertEquals("2026-11-19T10:15:00Z", response.createdAt)
    }

    @Test
    fun createComplaintResponse_usesDefaultsForMissingOptionalFields() {
        val json = """{ "folio": "DEN-2026-000999" }"""

        val response = gson.fromJson(json, CreateComplaintResponse::class.java)

        assertEquals("DEN-2026-000999", response.folio)
        assertNull(response.status)
        assertNull(response.statusDisplay)
    }

    @Test
    fun lookupResponse_parsesMaskedContactAndChatFlag() {
        val json = """
            {
              "folio": "DEN-2026-000123",
              "action_type": "denuncia",
              "action_type_display": "Denuncia",
              "status": "en_revision",
              "status_display": "En revisión",
              "severity": "alta",
              "severity_display": "Alta",
              "category": "Fraude y corrupción",
              "category_display": "Fraude y corrupción",
              "response": "Se está revisando el caso.",
              "created_at": "2026-11-19T10:15:00Z",
              "updated_at": "2026-11-19T12:00:00Z",
              "chat_enabled": true,
              "masked_email": "j***z@example.com",
              "masked_phone": "******1234",
              "reporter_name": "Juan Pérez"
            }
        """.trimIndent()

        val response = gson.fromJson(json, LookupResponse::class.java)

        assertEquals("DEN-2026-000123", response.folio)
        assertEquals("denuncia", response.actionType)
        assertEquals("Denuncia", response.actionTypeDisplay)
        assertEquals("en_revision", response.status)
        assertEquals("En revisión", response.statusDisplay)
        assertEquals("alta", response.severity)
        assertTrue(response.chatEnabled)
        assertEquals("j***z@example.com", response.maskedEmail)
        assertEquals("******1234", response.maskedPhone)
        assertEquals("Juan Pérez", response.reporterName)
    }

    @Test
    fun lookupResponse_defaultsChatDisabledWhenFieldAbsent() {
        val json = """{ "folio": "DEN-2026-000124" }"""

        val response = gson.fromJson(json, LookupResponse::class.java)

        assertFalse(response.chatEnabled)
        assertNull(response.maskedEmail)
        assertNull(response.maskedPhone)
    }

    @Test
    fun chatListResponse_parsesNestedMessages() {
        val json = """
            {
              "folio": "DEN-2026-000123",
              "chat_enabled": true,
              "messages": [
                {"id": 1, "sender": "reporter", "sender_display": "Denunciante", "message": "Hola", "created_at": "2026-11-19T10:20:00Z"},
                {"id": 2, "sender": "admin", "sender_display": "Canal", "message": "Recibido", "created_at": "2026-11-19T10:25:00Z"}
              ]
            }
        """.trimIndent()

        val response = gson.fromJson(json, ChatListResponse::class.java)

        assertEquals("DEN-2026-000123", response.folio)
        assertTrue(response.chatEnabled)
        assertEquals(2, response.messages.size)
        assertEquals("reporter", response.messages[0].sender)
        assertEquals("Hola", response.messages[0].message)
        assertEquals("admin", response.messages[1].sender)
        assertEquals("Recibido", response.messages[1].message)
    }

    @Test
    fun chatListResponse_defaultsToEmptyMessagesWhenAbsent() {
        val json = """{ "folio": "DEN-2026-000123", "chat_enabled": false }"""

        val response = gson.fromJson(json, ChatListResponse::class.java)

        assertFalse(response.chatEnabled)
        assertTrue(response.messages.isEmpty())
    }

    @Test
    fun attachmentsResponse_parsesAttachmentList() {
        val json = """
            {
              "folio": "DEN-2026-000123",
              "attachments": [
                {"id": "a1", "name": "evidencia.pdf", "is_main": true, "size": 2048, "download_url": "https://canal.example/api/attachments/a1/"},
                {"id": "a2", "name": "foto.png", "is_main": false, "size": 512, "download_url": "https://canal.example/api/attachments/a2/"}
              ]
            }
        """.trimIndent()

        val response = gson.fromJson(json, AttachmentsResponse::class.java)

        assertEquals(2, response.attachments.size)
        assertEquals("a1", response.attachments[0].id)
        assertEquals("evidencia.pdf", response.attachments[0].name)
        assertTrue(response.attachments[0].isMain)
        assertEquals(2048L, response.attachments[0].size)
        assertFalse(response.attachments[1].isMain)
    }

    @Test
    fun privacyNoticeDto_parsesNotice() {
        val json = """{ "id": 5, "company": "COMETRA", "file_url": "https://canal.example/media/aviso.pdf" }"""

        val notice = gson.fromJson(json, PrivacyNoticeDto::class.java)

        assertEquals(5L, notice.id)
        assertEquals("COMETRA", notice.company)
        assertEquals("https://canal.example/media/aviso.pdf", notice.fileUrl)
    }

    @Test
    fun apiErrorResponse_parsesErrorEnvelope() {
        val json = """{ "error": "invalid_credentials", "detail": "El folio o la contraseña no son correctos." }"""

        val error = gson.fromJson(json, ApiErrorResponse::class.java)

        assertEquals("invalid_credentials", error.error)
        assertEquals("El folio o la contraseña no son correctos.", error.detail)
    }
}
