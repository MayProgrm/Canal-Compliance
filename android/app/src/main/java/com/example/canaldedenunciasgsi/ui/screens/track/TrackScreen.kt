package com.example.canaldedenunciasgsi.ui.screens.track

import android.content.Intent
import android.net.Uri
import androidx.annotation.StringRes
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Chat
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Key
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PrivacyTip
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.SupportAgent
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.data.remote.ApiFailureKind
import com.example.canaldedenunciasgsi.data.remote.ApiRepository
import com.example.canaldedenunciasgsi.data.remote.ApiResult
import com.example.canaldedenunciasgsi.data.remote.AttachmentDto
import com.example.canaldedenunciasgsi.data.remote.ChatMessageDto
import com.example.canaldedenunciasgsi.data.remote.LookupResponse
import com.example.canaldedenunciasgsi.ui.components.LeadCard
import com.example.canaldedenunciasgsi.ui.components.Reveal
import com.example.canaldedenunciasgsi.ui.components.pressScale
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro
import com.example.canaldedenunciasgsi.ui.theme.GsiRojo
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Locale

private const val TRACK_FOLIO_PREFIX = "GSI-"

private fun folioSuffix(value: String): String =
    value.trim().uppercase().removePrefix(TRACK_FOLIO_PREFIX)
        .filter { it.isLetterOrDigit() }
        .take(16)

/** Intervalo del sondeo de la conversación (chat). */
private const val CHAT_POLL_INTERVAL_MS = 5000L

/** Error mostrado al denunciante durante la consulta. */
private data class TrackError(
    @param:StringRes val titleRes: Int,
    @param:StringRes val bodyRes: Int,
)

/**
 * Sección "Consultar denuncia".
 *
 * Con el folio y la contraseña definidos al enviar el reporte se consulta el
 * estado del caso en el servidor del canal. Cuando el estado lo permite se
 * habilita el chat con actualización automática y la descarga de adjuntos.
 */
@Composable
fun TrackScreen(initialFolio: String = "", modifier: Modifier = Modifier) {
    var folio by rememberSaveable { mutableStateOf(folioSuffix(initialFolio)) }
    var password by rememberSaveable { mutableStateOf("") }
    var error by remember { mutableStateOf<TrackError?>(null) }
    var record by remember { mutableStateOf<LookupResponse?>(null) }
    var isSearching by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()

    // Al llegar desde el comprobante se autorrellena el folio. Se hace en un
    // efecto para que también funcione cuando la pantalla ya existía (por
    // ejemplo, tras visitar la consulta desde el menú).
    LaunchedEffect(initialFolio) {
        val suffix = folioSuffix(initialFolio)
        if (suffix.isNotBlank() && suffix != folio) {
            folio = suffix
            record = null
        }
    }

    val runLookup: () -> Unit = {
        if (folio.isBlank() || password.isBlank()) {
            error = TrackError(R.string.track_error_title, R.string.track_error_body)
        } else {
            isSearching = true
            scope.launch {
                val normalized = "$TRACK_FOLIO_PREFIX${folio.trim().uppercase()}"
                when (val result = ApiRepository.lookup(normalized, password)) {
                    is ApiResult.Success -> record = result.data
                    is ApiResult.Failure -> error = result.toTrackError()
                }
                isSearching = false
            }
        }
    }

    // El formulario y el resultado se intercambian con una transición suave.
    AnimatedContent(
        targetState = record,
        modifier = modifier,
        transitionSpec = {
            if (targetState != null) {
                (
                    fadeIn(animationSpec = tween(durationMillis = 240)) +
                        slideInHorizontally(animationSpec = tween(durationMillis = 300)) { it / 8 }
                    ) togetherWith fadeOut(animationSpec = tween(durationMillis = 140))
            } else {
                fadeIn(animationSpec = tween(durationMillis = 240)) togetherWith
                    (
                        fadeOut(animationSpec = tween(durationMillis = 140)) +
                            slideOutHorizontally(animationSpec = tween(durationMillis = 300)) { it / 8 }
                        )
            }
        },
        label = "trackContent"
    ) { current ->
        if (current != null) {
            TrackResult(
                result = current,
                folio = "$TRACK_FOLIO_PREFIX${folio.trim().uppercase()}",
                password = password,
                isRefreshing = isSearching,
                onRefresh = runLookup,
                onNewQuery = {
                    record = null
                    folio = ""
                    password = ""
                }
            )
        } else {
            TrackForm(
                folio = folio,
                onFolioChange = { folio = it },
                password = password,
                onPasswordChange = { password = it },
                isSearching = isSearching,
                onSearch = runLookup
            )
        }
    }

    error?.let { current ->
        AlertDialog(
            onDismissRequest = { error = null },
            icon = {
                Icon(
                    imageVector = Icons.Filled.ErrorOutline,
                    contentDescription = null,
                    tint = GsiRojo
                )
            },
            title = {
                Text(
                    text = stringResource(current.titleRes),
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654
                )
            },
            text = {
                Text(
                    text = stringResource(current.bodyRes),
                    style = MaterialTheme.typography.bodyMedium,
                    color = GsiNegro
                )
            },
            confirmButton = {
                TextButton(onClick = { error = null }) {
                    Text(
                        text = stringResource(R.string.report_pending_ok),
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        )
    }
}

/** Traduce el fallo de la API al mensaje que ve el denunciante. */
private fun ApiResult.Failure.toTrackError(): TrackError = when (kind) {
    ApiFailureKind.NOT_FOUND -> TrackError(
        R.string.track_not_found_title,
        R.string.track_not_found_body
    )

    ApiFailureKind.UNAUTHORIZED -> TrackError(
        R.string.track_invalid_password_title,
        R.string.track_invalid_password_body
    )

    ApiFailureKind.NETWORK -> TrackError(
        R.string.track_network_title,
        R.string.track_network_body
    )

    else -> TrackError(
        R.string.track_server_title,
        R.string.track_server_body
    )
}

/** Formulario de consulta: folio y contraseña. */
@Composable
private fun TrackForm(
    folio: String,
    onFolioChange: (String) -> Unit,
    password: String,
    onPasswordChange: (String) -> Unit,
    isSearching: Boolean,
    onSearch: () -> Unit,
    modifier: Modifier = Modifier
) {
    var visible by rememberSaveable { mutableStateOf(false) }
    val searchInteraction = remember { MutableInteractionSource() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        LeadCard(
            title = stringResource(R.string.track_intro_title),
            body = stringResource(R.string.track_intro_body),
            icon = Icons.Filled.Search
        )

        OutlinedTextField(
            value = folio,
            onValueChange = { onFolioChange(folioSuffix(it)) },
            modifier = Modifier.fillMaxWidth(),
            label = { Text(text = stringResource(R.string.track_folio_label)) },
            placeholder = { Text(text = stringResource(R.string.track_folio_hint)) },
            singleLine = true,
            prefix = {
                Text(
                    text = TRACK_FOLIO_PREFIX,
                    color = GsiAzul654,
                    fontWeight = FontWeight.SemiBold
                )
            },
            leadingIcon = {
                Icon(
                    imageVector = Icons.Filled.Search,
                    contentDescription = null,
                    tint = GsiAzul654
                )
            },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text)
        )

        OutlinedTextField(
            value = password,
            onValueChange = onPasswordChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text(text = stringResource(R.string.track_password_label)) },
            singleLine = true,
            leadingIcon = {
                Icon(
                    imageVector = Icons.Filled.Lock,
                    contentDescription = null,
                    tint = GsiAzul654
                )
            },
            trailingIcon = {
                IconButton(onClick = { visible = !visible }) {
                    Icon(
                        imageVector = if (visible) {
                            Icons.Filled.VisibilityOff
                        } else {
                            Icons.Filled.Visibility
                        },
                        contentDescription = stringResource(
                            if (visible) {
                                R.string.report_password_hide
                            } else {
                                R.string.report_password_show
                            }
                        ),
                        tint = GsiGrisTexto
                    )
                }
            },
            visualTransformation = if (visible) {
                VisualTransformation.None
            } else {
                PasswordVisualTransformation()
            },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password)
        )

        Button(
            onClick = onSearch,
            enabled = !isSearching,
            interactionSource = searchInteraction,
            modifier = Modifier
                .fillMaxWidth()
                .pressScale(searchInteraction),
            colors = ButtonDefaults.buttonColors(
                containerColor = GsiAzul285,
                contentColor = Color.White
            )
        ) {
            if (isSearching) {
                CircularProgressIndicator(
                    modifier = Modifier.size(18.dp),
                    color = Color.White,
                    strokeWidth = 2.dp
                )
            } else {
                Icon(
                    imageVector = Icons.Filled.Search,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
            }
            Text(
                text = stringResource(
                    if (isSearching) R.string.track_searching else R.string.track_button
                ),
                style = MaterialTheme.typography.labelLarge,
                modifier = Modifier.padding(start = 8.dp)
            )
        }

        Text(
            text = stringResource(R.string.track_helper),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
    }
}

/** Resultado de la consulta con los datos del caso. */
@Composable
private fun TrackResult(
    result: LookupResponse,
    folio: String,
    password: String,
    isRefreshing: Boolean,
    onRefresh: () -> Unit,
    onNewQuery: () -> Unit,
    modifier: Modifier = Modifier
) {
    val identified = !result.reporterName.isNullOrBlank() ||
        !result.maskedEmail.isNullOrBlank() ||
        !result.maskedPhone.isNullOrBlank()

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        ResultHeader(
            statusLabel = result.statusDisplay ?: result.status.orEmpty(),
            folio = result.folio,
            isRefreshing = isRefreshing,
            onRefresh = onRefresh
        )

        Reveal(delayMillis = 60) {
            ResultSection(
                icon = Icons.Filled.Description,
                titleRes = R.string.track_result_title
            ) {
                InfoRow(R.string.track_folio, result.folio)
                InfoRow(
                    R.string.track_status,
                    result.statusDisplay ?: result.status.orEmpty()
                )
                InfoRow(R.string.track_sent_date, formatServerDate(result.createdAt))
                InfoRow(
                    R.string.track_action,
                    result.actionTypeDisplay ?: result.actionType.orEmpty()
                )
                InfoRow(
                    R.string.track_category,
                    result.categoryDisplay ?: result.category.orEmpty()
                )
            }
        }

        Reveal(delayMillis = 120) {
            ResultSection(
                icon = Icons.Filled.Schedule,
                titleRes = R.string.track_next_title
            ) {
                Text(
                    text = stringResource(nextStepRes(result.status)),
                    style = MaterialTheme.typography.bodyMedium,
                    color = GsiNegro
                )
            }
        }

        Reveal(delayMillis = 180) {
            ResultSection(
                icon = Icons.AutoMirrored.Filled.FactCheck,
                titleRes = R.string.track_response_title
            ) {
                Text(
                    text = result.response?.takeIf { it.isNotBlank() }
                        ?: stringResource(R.string.track_response_empty),
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (result.response.isNullOrBlank()) GsiGrisTexto else GsiNegro
                )
            }
        }

        Reveal(delayMillis = 240) {
            AttachmentsSection(folio = folio, password = password)
        }

        Reveal(delayMillis = 300) {
            ChatSection(
                folio = folio,
                password = password,
                canReply = result.chatEnabled
            )
        }

        Reveal(delayMillis = 360) {
            ResultSection(
                icon = Icons.Filled.PrivacyTip,
                titleRes = R.string.track_privacy_title
            ) {
                InfoRow(
                    labelRes = R.string.track_privacy_mode,
                    value = stringResource(
                        if (identified) {
                            R.string.track_privacy_identified
                        } else {
                            R.string.track_privacy_anonymous
                        }
                    )
                )
            }
        }

        Reveal(delayMillis = 420) {
            ResultSection(
                icon = Icons.Filled.SupportAgent,
                titleRes = R.string.track_contact_title
            ) {
                if (!identified) {
                    Text(
                        text = stringResource(R.string.track_contact_none),
                        style = MaterialTheme.typography.bodyMedium,
                        color = GsiGrisTexto
                    )
                } else {
                    InfoRow(R.string.track_contact_name, result.reporterName.orEmpty())
                    InfoRow(R.string.track_contact_email, result.maskedEmail.orEmpty())
                    InfoRow(R.string.track_contact_phone, result.maskedPhone.orEmpty())
                }
            }
        }

        Reveal(delayMillis = 480) {
            OutlinedButton(
                onClick = onNewQuery,
                modifier = Modifier.fillMaxWidth(),
                border = BorderStroke(1.dp, GsiAzul285),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = GsiAzul285)
            ) {
                Icon(
                    imageVector = Icons.Filled.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = stringResource(R.string.track_new_query),
                    style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.padding(start = 8.dp)
                )
            }
        }
    }
}

/** Adjuntos del folio, con enlace firmado de descarga. */
@Composable
private fun AttachmentsSection(
    folio: String,
    password: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var attachments by remember { mutableStateOf<List<AttachmentDto>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(folio, password) {
        when (val res = ApiRepository.getAttachments(folio, password)) {
            is ApiResult.Success -> attachments = res.data.attachments
            is ApiResult.Failure -> attachments = emptyList()
        }
        loading = false
    }

    ResultSection(
        icon = Icons.Filled.AttachFile,
        titleRes = R.string.track_files_title,
        modifier = modifier
    ) {
        when {
            loading -> CircularProgressIndicator(
                modifier = Modifier.size(22.dp),
                color = GsiAzul285,
                strokeWidth = 2.dp
            )

            attachments.isEmpty() -> Text(
                text = stringResource(R.string.track_files_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = GsiGrisTexto
            )

            else -> attachments.forEach { attachment ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(GsiGrisClaro, RoundedCornerShape(10.dp))
                        .padding(start = 12.dp, end = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Filled.Description,
                        contentDescription = null,
                        tint = GsiAzul654,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = attachment.name,
                        style = MaterialTheme.typography.bodySmall,
                        color = GsiNegro,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier
                            .weight(1f)
                            .padding(horizontal = 10.dp)
                    )
                    IconButton(
                        onClick = {
                            val url = attachment.downloadUrl ?: return@IconButton
                            runCatching {
                                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                            }
                        },
                        enabled = !attachment.downloadUrl.isNullOrBlank()
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Download,
                            contentDescription = stringResource(R.string.track_files_download),
                            tint = GsiAzul285
                        )
                    }
                }
            }
        }
    }
}

/** Conversación con el canal, con actualización automática por sondeo. */
@Composable
private fun ChatSection(
    folio: String,
    password: String,
    canReply: Boolean,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    var messages by remember { mutableStateOf<List<ChatMessageDto>>(emptyList()) }
    var input by rememberSaveable { mutableStateOf("") }
    var sending by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(false) }

    LaunchedEffect(folio, password) {
        while (true) {
            when (val res = ApiRepository.getChat(folio, password)) {
                is ApiResult.Success -> {
                    messages = res.data.messages
                    failed = false
                }

                is ApiResult.Failure -> failed = true
            }
            delay(CHAT_POLL_INTERVAL_MS)
        }
    }

    // Se muestran los mensajes del equipo aunque el denunciante no pueda
    // responder todavía. Si no hay conversación y no se puede responder, la
    // sección no se muestra.
    if (messages.isEmpty() && !canReply) {
        return
    }

    ResultSection(
        icon = Icons.AutoMirrored.Filled.Chat,
        titleRes = R.string.track_chat_title,
        modifier = modifier
    ) {
        if (messages.isEmpty()) {
            Text(
                text = stringResource(
                    if (failed) R.string.track_chat_error else R.string.track_chat_empty
                ),
                style = MaterialTheme.typography.bodyMedium,
                color = GsiGrisTexto
            )
        } else {
            messages.forEachIndexed { index, message ->
                if (index > 0) HorizontalDivider(color = GsiGrisBorde)
                ChatBubble(message = message)
            }
        }

        if (canReply) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = input,
                    onValueChange = { input = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text(text = stringResource(R.string.track_chat_placeholder)) },
                    singleLine = false,
                    maxLines = 4
                )
                IconButton(
                    onClick = {
                        val text = input.trim()
                        if (text.isEmpty() || sending) return@IconButton
                        sending = true
                        scope.launch {
                            when (val res = ApiRepository.sendChatMessage(folio, password, text)) {
                                is ApiResult.Success -> {
                                    messages = messages + res.data
                                    input = ""
                                }

                                is ApiResult.Failure -> failed = true
                            }
                            sending = false
                        }
                    },
                    enabled = input.isNotBlank() && !sending
                ) {
                if (sending) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = GsiAzul285,
                        strokeWidth = 2.dp
                    )
                } else {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.Send,
                        contentDescription = stringResource(R.string.track_chat_send),
                        tint = if (input.isNotBlank()) GsiAzul285 else GsiGrisBorde
                    )
                }
            }
            }
        }
    }
}

/** Burbuja de un mensaje del chat. */
@Composable
private fun ChatBubble(message: ChatMessageDto, modifier: Modifier = Modifier) {
    val fromReporter = message.sender == "reporter"

    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = if (fromReporter) Arrangement.End else Arrangement.Start
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth(0.86f)
                .background(
                    color = if (fromReporter) GsiAzulClaro else GsiGrisClaro,
                    shape = RoundedCornerShape(12.dp)
                )
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(3.dp)
        ) {
            Text(
                text = message.senderDisplay.orEmpty(),
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.SemiBold,
                color = GsiAzul654
            )
            Text(
                text = message.message,
                style = MaterialTheme.typography.bodyMedium,
                color = GsiNegro
            )
            Text(
                text = formatServerDateTime(message.createdAt),
                style = MaterialTheme.typography.labelSmall,
                color = GsiGrisTexto
            )
        }
    }
}

/** Encabezado del resultado: folio, estado actual y acción de actualizar. */
@Composable
private fun ResultHeader(
    statusLabel: String,
    folio: String,
    isRefreshing: Boolean,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier
) {
    val refreshInteraction = remember { MutableInteractionSource() }

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = GsiAzul654),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.Top
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    text = stringResource(R.string.track_status_title),
                    style = MaterialTheme.typography.labelMedium,
                    color = Color.White.copy(alpha = 0.85f)
                )
                Text(
                    text = statusLabel,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Filled.Key,
                        contentDescription = null,
                        tint = Color.White.copy(alpha = 0.85f),
                        modifier = Modifier.size(16.dp)
                    )
                    Text(
                        text = "${stringResource(R.string.track_folio)}: $folio",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White,
                        modifier = Modifier.padding(start = 6.dp)
                    )
                }
            }
            IconButton(
                onClick = onRefresh,
                enabled = !isRefreshing,
                interactionSource = refreshInteraction,
                modifier = Modifier.pressScale(refreshInteraction)
            ) {
                if (isRefreshing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = Color.White,
                        strokeWidth = 2.dp
                    )
                } else {
                    Icon(
                        imageVector = Icons.Filled.Refresh,
                        contentDescription = stringResource(R.string.track_refresh),
                        tint = Color.White
                    )
                }
            }
        }
    }
}

/** Bloque de resultado con título e icono. */
@Composable
private fun ResultSection(
    icon: ImageVector,
    @StringRes titleRes: Int,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, GsiGrisBorde),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(34.dp)
                        .background(GsiAzulClaro, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = GsiAzul654,
                        modifier = Modifier.size(19.dp)
                    )
                }
                Text(
                    text = stringResource(titleRes),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654,
                    modifier = Modifier.padding(start = 12.dp)
                )
            }
            content()
        }
    }
}

/** Fila de etiqueta y valor. */
@Composable
private fun InfoRow(labelRes: Int, value: String, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        Text(
            text = stringResource(labelRes),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto,
            modifier = Modifier.weight(1f)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Medium,
            color = GsiNegro,
            modifier = Modifier.weight(1f)
        )
    }
}

/** Texto de "qué sigue" según el estado del servidor. */
@StringRes
private fun nextStepRes(status: String?): Int = when (status) {
    "admitido", "transferido" -> R.string.track_next_review
    "investigacion", "info_adicional" -> R.string.track_next_investigation
    "resolucion" -> R.string.track_next_resolution
    "resuelto", "rechazado", "archivado" -> R.string.track_next_closed
    else -> R.string.track_next_received
}

/** Convierte una fecha ISO del servidor (aaaa-mm-dd…) a dd/mm/aaaa. */
private fun formatServerDate(value: String?): String {
    if (value.isNullOrBlank()) return ""
    val parts = value.substringBefore('T').substringBefore(' ').split('-')
    return if (parts.size == 3) "${parts[2]}/${parts[1]}/${parts[0]}" else value
}

/** Convierte una fecha y hora ISO del servidor a dd/mm/aaaa hh:mm. */
private fun formatServerDateTime(value: String?): String {
    if (value.isNullOrBlank()) return ""
    val clean = value.substringBefore('.').substringBefore('+').trimEnd('Z')
    val output = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
    listOf("yyyy-MM-dd'T'HH:mm:ss", "yyyy-MM-dd'T'HH:mm").forEach { pattern ->
        runCatching {
            return SimpleDateFormat(pattern, Locale.US).parse(clean)?.let { output.format(it) }.orEmpty()
        }
    }
    return value
}
