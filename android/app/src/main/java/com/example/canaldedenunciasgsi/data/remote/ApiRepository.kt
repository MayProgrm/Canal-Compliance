package com.example.canaldedenunciasgsi.data.remote

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.ResponseBody
import okio.BufferedSink
import okio.source
import retrofit2.Response
import java.io.IOException

/**
 * Acceso a la API del canal. Traduce cada llamada a un [ApiResult] para que las
 * pantallas traten los errores sin manejar excepciones.
 *
 * La autenticación del denunciante viaja siempre como `folio` + `password`.
 */
object ApiRepository {

    /** Número máximo de adjuntos que acepta el servidor. */
    private const val MAX_ATTACHMENTS = 5

    private val gson = Gson()
    private val textMediaType = "text/plain".toMediaTypeOrNull()

    /** Envía una denuncia nueva con sus adjuntos (multipart). */
    suspend fun createComplaint(
        context: Context,
        fields: Map<String, String>,
        attachmentUris: List<Uri>,
    ): ApiResult<CreateComplaintResponse> = withContext(Dispatchers.IO) {
        val parts = fields.mapValues { (_, value) -> value.toRequestBody(textMediaType) }
        val files = attachmentUris.take(MAX_ATTACHMENTS).mapNotNull { uri ->
            buildFilePart(context, uri)
        }
        safeCall { RetrofitClient.service.createComplaint(parts, files) }
    }

    /** Consulta una denuncia por folio y contraseña. */
    suspend fun lookup(folio: String, password: String): ApiResult<LookupResponse> =
        withContext(Dispatchers.IO) {
            safeCall { RetrofitClient.service.lookupComplaint(LookupRequest(folio.trim().uppercase(), password)) }
        }

    /** Recupera la conversación del folio. */
    suspend fun getChat(folio: String, password: String): ApiResult<ChatListResponse> =
        withContext(Dispatchers.IO) {
            safeCall { RetrofitClient.service.getChat(LookupRequest(folio.trim().uppercase(), password)) }
        }

    /** Envía un mensaje del denunciante. */
    suspend fun sendChatMessage(folio: String, password: String, message: String): ApiResult<ChatMessageDto> =
        withContext(Dispatchers.IO) {
            safeCall { RetrofitClient.service.sendChatMessage(ChatSendRequest(folio, password, message)) }
        }

    /** Recupera la lista de adjuntos descargables del folio. */
    suspend fun getAttachments(folio: String, password: String): ApiResult<AttachmentsResponse> =
        withContext(Dispatchers.IO) {
            safeCall { RetrofitClient.service.getAttachments(LookupRequest(folio.trim().uppercase(), password)) }
        }

    /** Recupera los avisos de privacidad publicados por empresa. */
    suspend fun getPrivacyNotices(): ApiResult<List<PrivacyNoticeDto>> =
        withContext(Dispatchers.IO) {
            safeCall { RetrofitClient.service.getPrivacyNotices() }
        }

    /** Nombre visible de un archivo elegido por la persona. */
    fun attachmentDisplayName(context: Context, uri: Uri): String {
        val fromProvider = try {
            context.contentResolver
                .query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
                ?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                        if (index >= 0) cursor.getString(index) else null
                    } else {
                        null
                    }
                }
        } catch (e: Exception) {
            null
        }
        return fromProvider ?: uri.lastPathSegment?.substringAfterLast('/') ?: uri.toString()
    }

    private fun buildFilePart(context: Context, uri: Uri): MultipartBody.Part? = try {
        val mime = context.contentResolver.getType(uri) ?: "application/octet-stream"
        val name = attachmentDisplayName(context, uri)
        MultipartBody.Part.createFormData(
            "attachments",
            name,
            UriRequestBody(context, uri, mime.toMediaTypeOrNull()),
        )
    } catch (e: Exception) {
        null
    }

    private suspend fun <T> safeCall(call: suspend () -> Response<T>): ApiResult<T> = try {
        val response = call()
        if (response.isSuccessful) {
            val body = response.body()
            if (body != null) {
                ApiResult.Success(body)
            } else {
                ApiResult.Failure(ApiFailureKind.UNKNOWN, "El servidor no devolvió datos.")
            }
        } else {
            ApiResult.Failure(kindFor(response.code()), errorDetail(response.errorBody()))
        }
    } catch (e: IOException) {
        ApiResult.Failure(ApiFailureKind.NETWORK, e.message)
    } catch (e: Exception) {
        ApiResult.Failure(ApiFailureKind.UNKNOWN, e.message)
    }

    private fun kindFor(code: Int): ApiFailureKind = when (code) {
        404 -> ApiFailureKind.NOT_FOUND
        401, 403 -> ApiFailureKind.UNAUTHORIZED
        409, 410 -> ApiFailureKind.CONFLICT
        in 500..599 -> ApiFailureKind.SERVER
        else -> ApiFailureKind.UNKNOWN
    }

    private fun errorDetail(body: ResponseBody?): String? {
        val raw = try {
            body?.string()
        } catch (e: Exception) {
            null
        } ?: return null
        return try {
            val parsed = gson.fromJson(raw, ApiErrorResponse::class.java)
            parsed.detail ?: parsed.error
        } catch (e: Exception) {
            raw
        }
    }
}

/**
 * Cuerpo de la petición para un adjunto. El archivo se lee del `ContentResolver`
 * en el momento de enviarlo, sin cargarlo entero en memoria.
 */
private class UriRequestBody(
    private val context: Context,
    private val uri: Uri,
    private val mediaType: MediaType?,
) : RequestBody() {

    override fun contentType(): MediaType? = mediaType

    override fun contentLength(): Long = try {
        context.contentResolver.openAssetFileDescriptor(uri, "r")?.use { it.length } ?: -1L
    } catch (e: Exception) {
        -1L
    }

    override fun writeTo(sink: BufferedSink) {
        val input = context.contentResolver.openInputStream(uri)
        if (input != null) {
            input.source().use { sink.writeAll(it) }
        }
    }
}
