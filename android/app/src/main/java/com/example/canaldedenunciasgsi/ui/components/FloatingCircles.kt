package com.example.canaldedenunciasgsi.ui.components

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Círculos decorativos con un movimiento vertical continuo (arriba y abajo).
 * Debe usarse dentro del [BoxScope] de un contenedor con degradado y recortado.
 *
 * Los círculos se dibujan dentro de un contenedor `matchParentSize`, de modo que
 * NO alteran el tamaño del contenedor: solo lo decoran por detrás.
 *
 * Optimización clave: el valor animado se lee DENTRO del bloque `graphicsLayer`,
 * que se ejecuta en la fase de dibujo. De este modo la animación infinita no
 * provoca ni recomposición ni una nueva medición/colocación en cada fotograma:
 * solo se actualiza la transformación del propio círculo en la GPU. Esto es lo
 * que mantiene fluido el desplazamiento del resto de la pantalla, incluso en el
 * menú lateral, que permanece compuesto aunque esté cerrado.
 */
@Composable
fun BoxScope.FloatingCircles(
    travel: Dp = 16.dp,
    durationMillis: Int = 3200,
    primarySize: Dp = 180.dp,
    secondarySize: Dp = 130.dp
) {
    val transition = rememberInfiniteTransition(label = "floatingCircles")
    val progress = transition.animateFloat(
        initialValue = -1f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = durationMillis, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "floatingProgress"
    )

    Box(modifier = Modifier.matchParentSize()) {
        // Los círculos se desplazan en sentidos opuestos para dar sensación de profundidad.
        Box(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .graphicsLayer {
                    val shift = travel.toPx() * progress.value
                    translationX = 54.dp.toPx()
                    translationY = (-54).dp.toPx() + shift
                }
                .size(primarySize)
                .background(Color.White.copy(alpha = 0.08f), CircleShape)
        )
        Box(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .graphicsLayer {
                    val shift = travel.toPx() * progress.value
                    translationX = (-46).dp.toPx()
                    translationY = 60.dp.toPx() - shift
                }
                .size(secondarySize)
                .background(Color.White.copy(alpha = 0.07f), CircleShape)
        )
    }
}
