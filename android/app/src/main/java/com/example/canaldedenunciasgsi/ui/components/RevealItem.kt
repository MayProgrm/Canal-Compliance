package com.example.canaldedenunciasgsi.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.lazy.LazyItemScope
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer

/**
 * Bloque de una lista que aparece con un desvanecimiento la primera vez que se
 * muestra.
 *
 * El estado se guarda con [rememberSaveable], por lo que el efecto se reproduce
 * UNA sola vez por elemento: al volver a desplazarse sobre el mismo bloque ya no
 * se vuelve a animar. Además la animación se aplica con `graphicsLayer` (solo
 * alfa y traslación), lo que evita medir y recolocar el contenido en cada
 * fotograma y mantiene el desplazamiento fluido.
 *
 * Se añade `animateItem` para que, cuando un apartado se despliega y cambia la
 * altura de la lista, el resto de los bloques se desplacen con suavidad hasta su
 * nueva posición. La aparición y desaparición se dejan a cargo de `graphicsLayer`
 * (desvanecido propio), por lo que aquí se desactivan esas dos fases para no
 * duplicar el efecto.
 */
@Composable
fun LazyItemScope.RevealItem(
    content: @Composable () -> Unit
) {
    var revealed by rememberSaveable { mutableStateOf(false) }
    val progress by animateFloatAsState(
        targetValue = if (revealed) 1f else 0f,
        animationSpec = tween(durationMillis = 420),
        label = "revealItem"
    )

    LaunchedEffect(Unit) { revealed = true }

    Box(
        modifier = Modifier
            .animateItem(fadeInSpec = null, fadeOutSpec = null)
            .graphicsLayer {
                alpha = progress
                translationY = (1f - progress) * 26f
            }
    ) {
        content()
    }
}

/**
 * Igual que [RevealItem] pero para contenido dentro de un `Column` normal (por
 * ejemplo una pantalla con desplazamiento vertical). Reproduce el desvanecido
 * una sola vez y admite un retardo para escalonar la entrada de varios bloques.
 *
 * Al animar con `graphicsLayer` (alfa y traslación) el trabajo se resuelve en la
 * fase de dibujo, sin medir ni recolocar el contenido en cada fotograma.
 */
@Composable
fun Reveal(
    modifier: Modifier = Modifier,
    delayMillis: Int = 0,
    content: @Composable () -> Unit
) {
    var revealed by rememberSaveable { mutableStateOf(false) }
    val progress by animateFloatAsState(
        targetValue = if (revealed) 1f else 0f,
        animationSpec = tween(durationMillis = 420, delayMillis = delayMillis),
        label = "reveal"
    )

    LaunchedEffect(Unit) { revealed = true }

    Box(
        modifier = modifier.graphicsLayer {
            alpha = progress
            translationY = (1f - progress) * 26f
        }
    ) {
        content()
    }
}
