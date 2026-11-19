package com.example.canaldedenunciasgsi.ui.components

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import kotlin.math.roundToInt

/**
 * Logotipo de la empresa usado en la barra superior y en el menú lateral.
 *
 * El recurso se decodifica UNA sola vez a su resolución nativa (sin reescalado
 * por densidad) y, a partir de él, se genera una versión reducida con un
 * promedio de área de alta calidad ajustada a los píxeles exactos que ocupará
 * en pantalla.
 *
 * Reducir el logotipo en la CPU con un filtro de área (en lugar de dejar que la
 * GPU lo reduzca con interpolación bilineal) es lo que elimina el aspecto
 * suavizado y los bordes poco definidos: al dibujarse prácticamente 1:1 con los
 * píxeles de la pantalla, las letras y trazos del logotipo se ven nítidos.
 *
 * Cada tamaño solicitado se calcula una sola vez y queda en caché.
 *
 * Para colocar el logo definitivo basta con reemplazar el recurso
 * `app/src/main/res/drawable-nodpi/logo_gsi` (PNG, JPG o XML). No hay que tocar código.
 */
@Composable
fun AppLogo(
    modifier: Modifier = Modifier,
    height: Dp = 36.dp
) {
    val context = LocalContext.current
    val density = LocalDensity.current

    // Píxeles enteros: evita el reescalado fraccionario, causa habitual de que
    // el logotipo se perciba borroso.
    val targetHeightPx = with(density) { height.toPx() }.roundToInt().coerceAtLeast(1)
    val image = remember(targetHeightPx) { logoBitmap(context.applicationContext, targetHeightPx) }

    if (image == null) return

    val width = with(density) { image.width.toDp() }
    val finalHeight = with(density) { image.height.toDp() }

    Image(
        bitmap = image,
        contentDescription = null,
        contentScale = ContentScale.FillBounds,
        filterQuality = FilterQuality.High,
        modifier = modifier
            .height(finalHeight)
            .width(width)
    )
}

/** Versiones reducidas del logotipo, indexadas por su altura en píxeles. */
private val logoCache = mutableMapOf<Int, ImageBitmap>()

/** Logotipo original decodificado a su resolución nativa. */
private var sourceLogo: Bitmap? = null

/**
 * Devuelve el logotipo ya reducido al tamaño exacto de dibujo indicado.
 * La primera vez se reduce con un filtro de área; después se reutiliza la caché.
 */
private fun logoBitmap(context: Context, targetHeightPx: Int): ImageBitmap? {
    logoCache[targetHeightPx]?.let { return it }

    val source = sourceLogo ?: decodeSourceLogo(context)?.also { sourceLogo = it } ?: return null

    val bitmap = if (targetHeightPx >= source.height) {
        source
    } else {
        val targetWidth = (targetHeightPx * source.width.toFloat() / source.height)
            .roundToInt()
            .coerceAtLeast(1)
        scaleDown(source, targetWidth, targetHeightPx)
    }

    val image = bitmap.asImageBitmap()
    logoCache[targetHeightPx] = image
    return image
}

/** Decodifica el logotipo conservando su resolución nativa. */
private fun decodeSourceLogo(context: Context): Bitmap? {
    val options = BitmapFactory.Options().apply {
        inScaled = false
        inPreferredConfig = Bitmap.Config.ARGB_8888
    }
    return BitmapFactory.decodeResource(context.resources, R.drawable.logo_gsi, options)
}

/**
 * Reduce el mapa de bits a [width]×[height] con un promedio de área.
 *
 * Se divide por mitades sucesivas (cada paso promedia bloques 2×2, lo que evita
 * el aliaseado) y solo el último ajuste, ya muy cercano al destino, usa el
 * escalado con interpolación.
 */
private fun scaleDown(source: Bitmap, width: Int, height: Int): Bitmap {
    var current = source
    var currentWidth = source.width
    var currentHeight = source.height

    while (currentWidth / 2 >= width && currentHeight / 2 >= height) {
        currentWidth /= 2
        currentHeight /= 2
        current = Bitmap.createScaledBitmap(current, currentWidth, currentHeight, true)
    }

    return if (currentWidth != width || currentHeight != height) {
        Bitmap.createScaledBitmap(current, width, height, true)
    } else {
        current
    }
}
