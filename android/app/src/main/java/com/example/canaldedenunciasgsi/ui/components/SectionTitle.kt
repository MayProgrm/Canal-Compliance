package com.example.canaldedenunciasgsi.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro

/**
 * Título de sección con barra de acento corporativa.
 *
 * Si se indica un [icon], se muestra dentro de un círculo azul claro a la
 * izquierda del texto, lo que da a cada sección la misma jerarquía visual.
 */
@Composable
fun SectionTitle(
    text: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (icon != null) {
            Box(
                modifier = Modifier
                    .size(30.dp)
                    .background(GsiAzulClaro, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = GsiAzul654,
                    modifier = Modifier.size(17.dp)
                )
            }
            Spacer(modifier = Modifier.width(10.dp))
        } else {
            Box(
                modifier = Modifier
                    .size(width = 4.dp, height = 22.dp)
                    .background(GsiAzul285, RoundedCornerShape(2.dp))
            )
            Spacer(modifier = Modifier.width(10.dp))
        }
        Text(
            text = text,
            style = MaterialTheme.typography.titleLarge,
            color = GsiNegro
        )
    }
}
