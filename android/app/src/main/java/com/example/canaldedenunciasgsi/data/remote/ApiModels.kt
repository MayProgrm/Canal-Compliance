package com.example.canaldedenunciasgsi.data.remote

import com.google.gson.annotations.SerializedName

/** Respuesta del alta de una denuncia (`POST /api/complaints/`). */
data class CreateComplaintResponse(
    @SerializedName("folio") val folio: String,
    @SerializedName("status") val status: String? = null,
    @SerializedName("status_display") val statusDisplay: String? = null,
    @SerializedName("severity") val severity: String? = null,
    @SerializedName("severity_display") val severityDisplay: String? = null,
    @SerializedName("created_at") val createdAt: String? = null,
)

/** Cuerpo de la consulta por folio (`POST /api/complaints/lookup/`). */
data class LookupRequest(
    @SerializedName("folio") val folio: String,
    @SerializedName("password") val password: String?,
)

/** Datos que el canal devuelve al denunciante tras validar folio y contraseña. */
data class LookupResponse(
    @SerializedName("folio") val folio: String,
    @SerializedName("action_type") val actionType: String? = null,
    @SerializedName("action_type_display") val actionTypeDisplay: String? = null,
    @SerializedName("status") val status: String? = null,
    @SerializedName("status_display") val statusDisplay: String? = null,
    @SerializedName("severity") val severity: String? = null,
    @SerializedName("severity_display") val severityDisplay: String? = null,
    @SerializedName("category") val category: String? = null,
    @SerializedName("category_display") val categoryDisplay: String? = null,
    @SerializedName("response") val response: String? = null,
    @SerializedName("created_at") val createdAt: String? = null,
    @SerializedName("updated_at") val updatedAt: String? = null,
    @SerializedName("chat_enabled") val chatEnabled: Boolean = false,
    @SerializedName("masked_email") val maskedEmail: String? = null,
    @SerializedName("masked_phone") val maskedPhone: String? = null,
    @SerializedName("reporter_name") val reporterName: String? = null,
)

/** Mensaje del chat entre el denunciante y el canal. */
data class ChatMessageDto(
    @SerializedName("id") val id: Long,
    @SerializedName("sender") val sender: String? = null,
    @SerializedName("sender_display") val senderDisplay: String? = null,
    @SerializedName("message") val message: String = "",
    @SerializedName("created_at") val createdAt: String? = null,
)

/** Conversación completa del folio (`POST /api/complaints/chat/`). */
data class ChatListResponse(
    @SerializedName("folio") val folio: String? = null,
    @SerializedName("chat_enabled") val chatEnabled: Boolean = false,
    @SerializedName("messages") val messages: List<ChatMessageDto> = emptyList(),
)

/** Cuerpo para enviar un mensaje (`POST /api/complaints/chat/`). */
data class ChatSendRequest(
    @SerializedName("folio") val folio: String,
    @SerializedName("password") val password: String?,
    @SerializedName("message") val message: String,
)

/** Adjunto disponible para descarga. */
data class AttachmentDto(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String = "",
    @SerializedName("is_main") val isMain: Boolean = false,
    @SerializedName("size") val size: Long? = null,
    @SerializedName("download_url") val downloadUrl: String? = null,
)

/** Listado de adjuntos del folio (`POST /api/complaints/attachments/`). */
data class AttachmentsResponse(
    @SerializedName("folio") val folio: String? = null,
    @SerializedName("attachments") val attachments: List<AttachmentDto> = emptyList(),
)

/** Aviso de privacidad publicado para una empresa. */
data class PrivacyNoticeDto(
    @SerializedName("id") val id: Long,
    @SerializedName("company") val company: String,
    @SerializedName("file_url") val fileUrl: String? = null,
)

/** Error controlado devuelto por la API (`{error, detail}`). */
data class ApiErrorResponse(
    @SerializedName("error") val error: String? = null,
    @SerializedName("detail") val detail: String? = null,
)
