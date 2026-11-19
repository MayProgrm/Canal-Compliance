package com.example.canaldedenunciasgsi.ui.screens.report

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color as AndroidColor
import android.graphics.Paint
import android.print.PrintManager
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.NoteAdd
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Print
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
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
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.print.PrintHelper
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.data.ReportRepository
import com.example.canaldedenunciasgsi.ui.components.QrCode
import com.example.canaldedenunciasgsi.ui.components.Reveal
import com.example.canaldedenunciasgsi.ui.components.drawQrOnCanvas
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro
import kotlinx.coroutines.launch

/**
 * Pantalla que confirma el envío del reporte. Muestra el folio generado, un
 * código QR como comprobante, las opciones para guardar o imprimir, el
 * recordatorio de resguardo y los pasos que siguen.
 */
@Composable
fun ReportSuccessScreen(
    folio: String,
    onGoHome: () -> Unit,
    onTrack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val record = remember(folio) { ReportRepository.findByFolio(context, folio) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val copiedMessage = stringResource(R.string.report_success_folio_copied)
    val clipboardLabel = stringResource(R.string.track_folio)

    // Copia el folio al portapapeles y muestra la confirmación.
    val onCopyFolio: () -> Unit = {
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.setPrimaryClip(ClipData.newPlainText(clipboardLabel, folio))
        scope.launch { snackbarHostState.showSnackbar(copiedMessage) }
    }

    val folioLabel = stringResource(R.string.track_folio)
    val dateLabel = stringResource(R.string.track_sent_date)
    val actionLabel = stringResource(R.string.track_action)
    val categoryLabel = stringResource(R.string.track_category)
    val reasonLabel = stringResource(R.string.track_reason)

    val action = record?.let { stringResource(it.actionRes) }.orEmpty()
    val category = record?.let { stringResource(it.categoryRes) }.orEmpty()
    val reason = record?.let { stringResource(it.reasonRes) }.orEmpty()
    val date = record?.createdAt.orEmpty()

    val receiptTitle = stringResource(R.string.report_success_receipt_title)
    val reminderTitle = stringResource(R.string.report_success_reminder_title)
    val reminderBody = stringResource(R.string.report_success_reminder_body)
    val qrCaption = stringResource(R.string.report_success_qr_caption)
    val appName = stringResource(R.string.app_name)

    val infoRows = listOfNotNull(
        dateLabel to date,
        actionLabel to action,
        categoryLabel to category,
        reasonLabel to reason
    ).filter { it.second.isNotBlank() }

    val qrContent = buildList {
        add(receiptTitle)
        add("$folioLabel: $folio")
        infoRows.forEach { (label, value) -> add("$label: $value") }
    }.joinToString("\n")

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp)
        ) {
            SuccessHeader(appName = appName)

            Reveal(delayMillis = 80) {
                ReceiptCard(
                    folio = folio,
                    folioLabel = folioLabel,
                    title = receiptTitle,
                    appName = appName,
                    rows = infoRows,
                    qrContent = qrContent,
                    qrCaption = qrCaption,
                    onCopyFolio = onCopyFolio
                )
            }

            Reveal(delayMillis = 160) {
                ReminderCard(title = reminderTitle, body = reminderBody)
            }

            Reveal(delayMillis = 220) {
                NextStepsCard()
            }

            Reveal(
                delayMillis = 280,
                modifier = Modifier.fillMaxWidth()
            ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(
                    onClick = {
                        val noteText = buildNoteText(
                            context = context,
                            title = receiptTitle,
                            folio = folio,
                            rows = infoRows,
                            reminder = reminderBody
                        )
                        val intent = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(
                                Intent.EXTRA_SUBJECT,
                                context.getString(R.string.report_success_note_subject, folio)
                            )
                            putExtra(Intent.EXTRA_TEXT, noteText)
                        }
                        context.startActivity(
                            Intent.createChooser(
                                intent,
                                context.getString(R.string.report_success_save_note)
                            )
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = GsiAzul285,
                        contentColor = Color.White
                    )
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.NoteAdd,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = stringResource(R.string.report_success_save_note),
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.padding(start = 8.dp)
                    )
                }

                OutlinedButton(
                    onClick = {
                        val bitmap = buildReceiptBitmap(
                            context = context,
                            title = receiptTitle,
                            appName = appName,
                            folio = folio,
                            folioLabel = folioLabel,
                            rows = infoRows,
                            qrContent = qrContent,
                            qrCaption = qrCaption,
                            reminder = reminderBody
                        )
                        val printManager =
                            context.getSystemService(Context.PRINT_SERVICE) as PrintManager
                        val helper = PrintHelper(context).apply {
                            scaleMode = PrintHelper.SCALE_MODE_FIT
                        }
                        helper.printBitmap("$receiptTitle $folio", bitmap)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    border = BorderStroke(1.dp, GsiAzul285),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = GsiAzul285)
                ) {
                    Icon(
                        imageVector = Icons.Filled.Print,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = stringResource(R.string.report_success_print),
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.padding(start = 8.dp)
                    )
                }

                OutlinedButton(
                    onClick = onTrack,
                    modifier = Modifier.fillMaxWidth(),
                    border = BorderStroke(1.dp, GsiAzul285),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = GsiAzul285)
                ) {
                    Icon(
                        imageVector = Icons.Filled.Search,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = stringResource(R.string.report_success_track),
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.padding(start = 8.dp)
                    )
                }

                Button(
                    onClick = onGoHome,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = GsiAzul654,
                        contentColor = Color.White
                    )
                ) {
                    Icon(
                        imageVector = Icons.Filled.Home,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = stringResource(R.string.report_back_home),
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.padding(start = 8.dp)
                    )
                }
            }
            }
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(16.dp)
        )
    }
}

/** Encabezado de confirmación del envío. */
@Composable
private fun SuccessHeader(appName: String, modifier: Modifier = Modifier) {
    var shown by rememberSaveable { mutableStateOf(false) }
    val progress by animateFloatAsState(
        targetValue = if (shown) 1f else 0f,
        animationSpec = spring(
            dampingRatio = Spring.DampingRatioMediumBouncy,
            stiffness = Spring.StiffnessLow
        ),
        label = "successBadge"
    )
    LaunchedEffect(Unit) { shown = true }

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Box(
            modifier = Modifier
                .size(78.dp)
                .graphicsLayer {
                    scaleX = progress
                    scaleY = progress
                    alpha = progress
                }
                .background(GsiAzulClaro, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.CheckCircle,
                contentDescription = null,
                tint = GsiAzul285,
                modifier = Modifier.size(48.dp)
            )
        }
        Text(
            text = stringResource(R.string.report_success_title),
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = GsiAzul654,
            textAlign = TextAlign.Center
        )
        Text(
            text = stringResource(R.string.report_success_body, appName),
            style = MaterialTheme.typography.bodyMedium,
            color = GsiGrisTexto,
            textAlign = TextAlign.Center
        )
    }
}

/** Comprobante con el folio, los datos generales y el código QR. */
@Composable
private fun ReceiptCard(
    folio: String,
    folioLabel: String,
    title: String,
    appName: String,
    rows: List<Pair<String, String>>,
    qrContent: String,
    qrCaption: String,
    onCopyFolio: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, GsiGrisBorde),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654
                )
                Text(
                    text = appName,
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }

            HorizontalDivider(color = GsiGrisBorde)

            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = folioLabel.uppercase(),
                    style = MaterialTheme.typography.labelMedium,
                    color = GsiGrisTexto
                )
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(GsiAzulClaro, RoundedCornerShape(14.dp))
                        .clickable { onCopyFolio() }
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = folio,
                        fontSize = 30.sp,
                        fontWeight = FontWeight.Bold,
                        color = GsiAzul285,
                        letterSpacing = 1.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f, fill = false)
                    )
                    Icon(
                        imageVector = Icons.Filled.ContentCopy,
                        contentDescription = stringResource(R.string.report_success_copy_folio),
                        tint = GsiAzul654,
                        modifier = Modifier
                            .padding(start = 12.dp)
                            .size(22.dp)
                    )
                }
                Text(
                    text = stringResource(R.string.report_success_folio_hint),
                    style = MaterialTheme.typography.labelSmall,
                    color = GsiGrisTexto
                )
            }

            if (rows.isNotEmpty()) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    rows.forEach { (label, value) ->
                        Row(modifier = Modifier.fillMaxWidth()) {
                            Text(
                                text = label,
                                style = MaterialTheme.typography.bodySmall,
                                color = GsiGrisTexto,
                                modifier = Modifier.weight(1f)
                            )
                            Text(
                                text = value,
                                style = MaterialTheme.typography.bodySmall,
                                fontWeight = FontWeight.Medium,
                                color = GsiNegro,
                                textAlign = TextAlign.End,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }

            HorizontalDivider(color = GsiGrisBorde)

            QrCode(
                content = qrContent,
                modifier = Modifier
                    .size(190.dp)
                    .background(Color.White, RoundedCornerShape(8.dp))
                    .padding(8.dp)
            )
            Text(
                text = qrCaption,
                style = MaterialTheme.typography.bodySmall,
                color = GsiGrisTexto,
                textAlign = TextAlign.Center
            )
        }
    }
}

/** Recordatorio sobre la importancia de conservar el folio. */
@Composable
private fun ReminderCard(
    title: String,
    body: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Color(0xFFFFF4E5), RoundedCornerShape(16.dp))
            .padding(16.dp)
    ) {
        Icon(
            imageVector = Icons.Filled.WarningAmber,
            contentDescription = null,
            tint = Color(0xFFB26A00),
            modifier = Modifier.size(24.dp)
        )
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(start = 12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF8A4B00)
            )
            Text(
                text = body,
                style = MaterialTheme.typography.bodySmall,
                color = GsiNegro
            )
        }
    }
}

/** Pasos que siguen después de enviar el reporte. */
@Composable
private fun NextStepsCard(modifier: Modifier = Modifier) {
    val steps = listOf(
        R.string.report_success_next_1,
        R.string.report_success_next_2,
        R.string.report_success_next_3,
        R.string.report_success_next_4
    )

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(GsiAzulClaro, RoundedCornerShape(16.dp))
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = stringResource(R.string.report_success_next_title),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = GsiAzul654
        )
        steps.forEachIndexed { index, stepRes ->
            Row(verticalAlignment = Alignment.Top) {
                Box(
                    modifier = Modifier
                        .size(26.dp)
                        .background(GsiAzul654, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = (index + 1).toString(),
                        color = Color.White,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                Text(
                    text = stringResource(stepRes),
                    style = MaterialTheme.typography.bodyMedium,
                    color = GsiNegro,
                    modifier = Modifier
                        .weight(1f)
                        .padding(start = 12.dp)
                )
            }
        }
    }
}

/** Texto del comprobante que se comparte al guardarlo como nota. */
private fun buildNoteText(
    context: Context,
    title: String,
    folio: String,
    rows: List<Pair<String, String>>,
    reminder: String
): String = buildString {
    appendLine(title)
    appendLine(context.getString(R.string.track_folio) + ": " + folio)
    rows.forEach { (label, value) -> appendLine("$label: $value") }
    appendLine()
    appendLine(reminder)
    append(context.getString(R.string.report_success_track))
}

/** Dibuja el comprobante en un mapa de bits para enviarlo a imprimir. */
private fun buildReceiptBitmap(
    context: Context,
    title: String,
    appName: String,
    folio: String,
    folioLabel: String,
    rows: List<Pair<String, String>>,
    qrContent: String,
    qrCaption: String,
    reminder: String
): Bitmap {
    val width = 1080
    val padding = 72f
    val contentWidth = width - padding * 2

    val titlePaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 46f
        color = AndroidColor.rgb(0x00, 0x3A, 0x70)
        isFakeBoldText = true
    }
    val subtitlePaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 30f
        color = AndroidColor.rgb(0x4B, 0x55, 0x63)
    }
    val folioLabelPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 28f
        color = AndroidColor.rgb(0x4B, 0x55, 0x63)
    }
    val folioPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 64f
        color = AndroidColor.rgb(0x00, 0x72, 0xCE)
        isFakeBoldText = true
    }
    val rowPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 30f
        color = AndroidColor.BLACK
    }
    val captionPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 26f
        color = AndroidColor.rgb(0x4B, 0x55, 0x63)
    }
    val reminderPaint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 30f
        color = AndroidColor.BLACK
    }
    val dividerPaint = Paint().apply {
        color = AndroidColor.rgb(0xD0, 0xD5, 0xDD)
        strokeWidth = 2f
    }

    val fullBitmap = Bitmap.createBitmap(width, 2400, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(fullBitmap)
    canvas.drawColor(AndroidColor.WHITE)
    var y = padding

    canvas.drawText(title, padding, y + titlePaint.textSize, titlePaint)
    y += titlePaint.textSize + 12f
    canvas.drawText(appName, padding, y + subtitlePaint.textSize, subtitlePaint)
    y += subtitlePaint.textSize + 24f

    canvas.drawLine(padding, y, width - padding, y, dividerPaint)
    y += 34f

    canvas.drawText(folioLabel.uppercase(), padding, y + folioLabelPaint.textSize, folioLabelPaint)
    y += folioLabelPaint.textSize + 10f
    canvas.drawText(folio, padding, y + folioPaint.textSize, folioPaint)
    y += folioPaint.textSize + 30f

    rows.forEach { (label, value) ->
        canvas.drawText("$label:", padding, y + rowPaint.textSize, rowPaint)
        canvas.drawText(value, padding + 340f, y + rowPaint.textSize, rowPaint)
        y += rowPaint.textSize + 18f
    }

    y += 16f
    canvas.drawLine(padding, y, width - padding, y, dividerPaint)
    y += 34f

    val qrSize = 360f
    val qrLeft = (width - qrSize) / 2f
    drawQrOnCanvas(canvas, qrContent, qrLeft, y, qrSize)
    y += qrSize + 20f

    val captionLayout = StaticLayout.Builder
        .obtain(qrCaption, 0, qrCaption.length, captionPaint, contentWidth.toInt())
        .setAlignment(Layout.Alignment.ALIGN_CENTER)
        .build()
    canvas.save()
    canvas.translate(padding, y)
    captionLayout.draw(canvas)
    canvas.restore()
    y += captionLayout.height + 30f

    canvas.drawLine(padding, y, width - padding, y, dividerPaint)
    y += 34f

    val reminderLayout = StaticLayout.Builder
        .obtain(reminder, 0, reminder.length, reminderPaint, contentWidth.toInt())
        .setAlignment(Layout.Alignment.ALIGN_NORMAL)
        .build()
    canvas.save()
    canvas.translate(padding, y)
    reminderLayout.draw(canvas)
    canvas.restore()
    y += reminderLayout.height + padding

    val height = y.toInt().coerceIn(1, fullBitmap.height)
    return Bitmap.createBitmap(fullBitmap, 0, 0, width, height)
}
