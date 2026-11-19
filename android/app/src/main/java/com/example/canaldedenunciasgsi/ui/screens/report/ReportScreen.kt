package com.example.canaldedenunciasgsi.ui.screens.report

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.PrivacyTip
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.data.remote.ApiRepository
import com.example.canaldedenunciasgsi.data.remote.ApiResult
import com.example.canaldedenunciasgsi.data.remote.RetrofitClient
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro

/** Etapas previas a mostrar el cuestionario. */
private enum class ReportStage { VERACITY, PRIVACY, FORM }

/**
 * Sección "¡Quiero denunciar!".
 *
 * Antes del cuestionario se deben aceptar dos avisos: la declaración de veracidad
 * y el aviso de privacidad. Si se cancela cualquiera de ellos, se regresa a la
 * página principal.
 */
@Composable
fun ReportScreen(
    onExit: () -> Unit,
    onSubmitted: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var stage by rememberSaveable { mutableStateOf(ReportStage.VERACITY) }
    var availableNotices by remember { mutableStateOf(privacyNotices) }
    // Avisos de privacidad que la persona abrió, requeridos por el servidor.
    var privacyOpened by rememberSaveable { mutableStateOf("") }

    LaunchedEffect(stage) {
        if (stage == ReportStage.PRIVACY) {
            when (val result = ApiRepository.getPrivacyNotices()) {
                is ApiResult.Success -> {
                    val loaded = result.data.map { PrivacyNotice(it.company, it.fileUrl) }
                    if (loaded.isNotEmpty()) availableNotices = loaded
                }
                is ApiResult.Failure -> Unit
            }
        }
    }

    when (stage) {
        ReportStage.VERACITY -> VeracityDialog(
            onCancel = onExit,
            onAccept = { stage = ReportStage.PRIVACY }
        )

        ReportStage.PRIVACY -> PrivacyDialog(
            notices = availableNotices,
            onCancel = onExit,
            onAccept = { opened ->
                privacyOpened = opened
                stage = ReportStage.FORM
            }
        )

        ReportStage.FORM -> ReportForm(
            onExit = onExit,
            onSubmitted = onSubmitted,
            privacyOpened = privacyOpened,
            modifier = modifier
        )
    }
}

/** Primera ventana: declaración de veracidad. */
@Composable
private fun VeracityDialog(
    onCancel: () -> Unit,
    onAccept: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onCancel,
        icon = {
            Icon(
                imageVector = Icons.AutoMirrored.Filled.FactCheck,
                contentDescription = null,
                tint = GsiAzul285
            )
        },
        title = {
            Text(
                text = stringResource(R.string.report_veracity_title),
                fontWeight = FontWeight.Bold,
                color = GsiAzul654
            )
        },
        text = {
            Text(
                text = stringResource(R.string.report_veracity_body),
                style = MaterialTheme.typography.bodyMedium,
                color = GsiNegro
            )
        },
        confirmButton = {
            Button(
                onClick = onAccept,
                colors = ButtonDefaults.buttonColors(
                    containerColor = GsiAzul285,
                    contentColor = Color.White
                )
            ) {
                Text(text = stringResource(R.string.report_accept_continue))
            }
        },
        dismissButton = {
            TextButton(onClick = onCancel) {
                Text(text = stringResource(R.string.report_cancel))
            }
        }
    )
}

/**
 * Segunda ventana: aviso de privacidad.
 * La persona debe abrir al menos un aviso y marcar la casilla de aceptación.
 */
@Composable
private fun PrivacyDialog(
    notices: List<PrivacyNotice>,
    onCancel: () -> Unit,
    onAccept: (String) -> Unit
) {
    var openedNotices by rememberSaveable { mutableStateOf(listOf<Int>()) }
    var accepted by rememberSaveable { mutableStateOf(false) }
    val context = LocalContext.current
    val fallbackPdfUrl = RetrofitClient.BASE_URL
        .removeSuffix("api/")
        .plus("static/PDFs/Aviso%20de%20privacidad.pdf")

    // Los nombres consultados se envían al servidor como constancia.
    val openedTitles = openedNotices.mapNotNull { notices.getOrNull(it)?.company }

    AlertDialog(
        onDismissRequest = onCancel,
        icon = {
            Icon(
                imageVector = Icons.Filled.PrivacyTip,
                contentDescription = null,
                tint = GsiAzul285
            )
        },
        title = {
            Text(
                text = stringResource(R.string.report_privacy_title),
                fontWeight = FontWeight.Bold,
                color = GsiAzul654
            )
        },
        text = {
            Column(
                modifier = Modifier
                    .heightIn(max = 380.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = stringResource(R.string.report_privacy_intro),
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
                notices.forEachIndexed { index, notice ->
                    NoticeRow(
                        title = "Aviso de privacidad ${notice.company}",
                        isRead = index in openedNotices,
                        onClick = {
                            val url = notice.fileUrl?.takeIf { it.isNotBlank() } ?: fallbackPdfUrl
                            try {
                                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                if (index !in openedNotices) {
                                    openedNotices = openedNotices + index
                                }
                            } catch (_: ActivityNotFoundException) {
                                Toast.makeText(
                                    context,
                                    R.string.report_privacy_viewer_missing,
                                    Toast.LENGTH_LONG
                                ).show()
                            }
                        }
                    )
                }
                HorizontalDivider(color = GsiGrisBorde)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(
                        checked = accepted,
                        onCheckedChange = { accepted = it },
                        enabled = openedNotices.isNotEmpty()
                    )
                    Text(
                        text = stringResource(R.string.report_privacy_check),
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (accepted) GsiNegro else GsiGrisTexto
                    )
                }
                if (openedNotices.isEmpty()) {
                    Text(
                        text = stringResource(R.string.report_privacy_hint),
                        style = MaterialTheme.typography.bodySmall,
                        color = GsiGrisTexto
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = { onAccept(openedTitles.joinToString(", ")) },
                enabled = accepted,
                colors = ButtonDefaults.buttonColors(
                    containerColor = GsiAzul285,
                    contentColor = Color.White
                )
            ) {
                Text(text = stringResource(R.string.report_accept))
            }
        },
        dismissButton = {
            TextButton(onClick = onCancel) {
                Text(text = stringResource(R.string.report_cancel))
            }
        }
    )
}

/** Fila de un aviso de privacidad dentro de la ventana. */
@Composable
private fun NoticeRow(
    title: String,
    isRead: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .background(GsiAzulClaro, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.PrivacyTip,
                contentDescription = null,
                tint = GsiAzul654,
                modifier = Modifier.size(19.dp)
            )
        }
        Text(
            text = title,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            color = GsiNegro,
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 12.dp)
        )
        Icon(
            imageVector = if (isRead) Icons.Filled.CheckCircle else Icons.Filled.Visibility,
            contentDescription = null,
            tint = if (isRead) GsiAzul285 else GsiGrisTexto,
            modifier = Modifier.size(20.dp)
        )
    }
}
