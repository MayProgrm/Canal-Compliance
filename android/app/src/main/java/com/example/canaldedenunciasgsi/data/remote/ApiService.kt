package com.example.canaldedenunciasgsi.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.PartMap

/**
 * Endpoints públicos del canal. La autenticación del denunciante se hace con
 * `folio` + `password` en cada petición (sin sesión ni cookies).
 */
interface ApiService {

    @Multipart
    @POST("complaints/")
    suspend fun createComplaint(
        @PartMap fields: Map<String, @JvmSuppressWildcards RequestBody>,
        @Part files: List<MultipartBody.Part>,
    ): Response<CreateComplaintResponse>

    @POST("complaints/lookup/")
    suspend fun lookupComplaint(
        @Body body: LookupRequest,
    ): Response<LookupResponse>

    /**
     * Recupera la conversación del folio. La contraseña viaja en el cuerpo
     * (nunca en la URL) para no exponerla en logs ni cabeceras Referer.
     */
    @POST("complaints/chat/")
    suspend fun getChat(
        @Body body: LookupRequest,
    ): Response<ChatListResponse>

    @POST("complaints/chat/")
    suspend fun sendChatMessage(
        @Body body: ChatSendRequest,
    ): Response<ChatMessageDto>

    /** Listado de adjuntos; la contraseña viaja en el cuerpo, no en la URL. */
    @POST("complaints/attachments/")
    suspend fun getAttachments(
        @Body body: LookupRequest,
    ): Response<AttachmentsResponse>

    @GET("privacy-notices/")
    suspend fun getPrivacyNotices(): Response<List<PrivacyNoticeDto>>
}
