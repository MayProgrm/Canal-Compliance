package com.example.canaldedenunciasgsi.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = GsiAzul654,
    onPrimary = Color.White,
    primaryContainer = GsiAzul285,
    onPrimaryContainer = Color.White,
    secondary = GsiAzul285,
    onSecondary = Color.White,
    secondaryContainer = GsiAzulClaro,
    onSecondaryContainer = GsiAzul654,
    tertiary = GsiAzul654,
    onTertiary = Color.White,
    background = Color.White,
    onBackground = GsiNegro,
    surface = Color.White,
    onSurface = GsiNegro,
    surfaceVariant = GsiGrisClaro,
    onSurfaceVariant = GsiGrisTexto,
    outline = GsiGrisBorde,
    outlineVariant = GsiGrisClaro,
    error = Color(0xFFB3261E),
    onError = Color.White
)

/**
 * Tema corporativo de GSI.
 * Fondo blanco y textos en negro para garantizar el contraste en toda la app.
 */
@Composable
fun CanalDeDenunciasGSITheme(
    content: @Composable () -> Unit
) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            val insetsController = WindowCompat.getInsetsController(window, view)
            // Fondo claro: los iconos de las barras del sistema deben ser oscuros.
            insetsController.isAppearanceLightStatusBars = true
            insetsController.isAppearanceLightNavigationBars = true
        }
    }

    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        content = content
    )
}
