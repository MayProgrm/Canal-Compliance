package com.example.canaldedenunciasgsi.ui.components

import android.graphics.Canvas as AndroidCanvas
import android.graphics.Color as AndroidColor
import android.graphics.Paint
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel
import com.google.zxing.qrcode.encoder.ByteMatrix
import com.google.zxing.qrcode.encoder.Encoder

/** Módulos de margen en blanco que rodean el código (zona de silencio). */
private const val QUIET_ZONE = 2

/**
 * Código QR generado a partir del texto indicado.
 * Se dibuja como módulos, por lo que se mantiene nítido en cualquier tamaño.
 */
@Composable
fun QrCode(
    content: String,
    modifier: Modifier = Modifier,
    darkColor: Color = Color.Black
) {
    val matrix = remember(content) { encodeQr(content) }

    Canvas(modifier = modifier) {
        val qr = matrix ?: return@Canvas
        val modules = qr.width + QUIET_ZONE * 2
        val cell = size.minDimension / modules
        val startX = (size.width - cell * modules) / 2f
        val startY = (size.height - cell * modules) / 2f

        for (y in 0 until qr.height) {
            for (x in 0 until qr.width) {
                if (qr.get(x, y).toInt() == 1) {
                    drawRect(
                        color = darkColor,
                        topLeft = Offset(
                            startX + (x + QUIET_ZONE) * cell,
                            startY + (y + QUIET_ZONE) * cell
                        ),
                        size = Size(cell + 0.6f, cell + 0.6f)
                    )
                }
            }
        }
    }
}

/** Dibuja el código QR sobre un lienzo de Android; se usa al imprimir el comprobante. */
fun drawQrOnCanvas(
    canvas: AndroidCanvas,
    content: String,
    left: Float,
    top: Float,
    sizePx: Float,
    color: Int = AndroidColor.BLACK
) {
    val qr = encodeQr(content) ?: return
    val modules = qr.width + QUIET_ZONE * 2
    val cell = sizePx / modules
    val paint = Paint().apply {
        this.color = color
        style = Paint.Style.FILL
    }

    for (y in 0 until qr.height) {
        for (x in 0 until qr.width) {
            if (qr.get(x, y).toInt() == 1) {
                val px = left + (x + QUIET_ZONE) * cell
                val py = top + (y + QUIET_ZONE) * cell
                canvas.drawRect(px, py, px + cell + 0.6f, py + cell + 0.6f, paint)
            }
        }
    }
}

/** Codifica el texto en una matriz de módulos; devuelve null si no es posible. */
private fun encodeQr(content: String): ByteMatrix? = runCatching {
    val hints = mapOf(
        EncodeHintType.ERROR_CORRECTION to ErrorCorrectionLevel.M,
        EncodeHintType.MARGIN to 0
    )
    Encoder.encode(content, ErrorCorrectionLevel.M, hints).matrix
}.getOrNull()
