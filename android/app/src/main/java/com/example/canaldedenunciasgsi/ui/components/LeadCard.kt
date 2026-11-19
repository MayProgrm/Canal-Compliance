package com.example.canaldedenunciasgsi.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto

/**
 * Encabezado informativo reutilizable.
 *
 * Se usa como primer bloque de cada sección para que Página principal, Guía,
 * Preguntas frecuentes, Biblioteca y Consultar denuncia compartan la misma
 * jerarquía visual: icono, título y descripción sobre un fondo azul claro.
 */
@Composable
fun LeadCard(
    title: String,
    body: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(GsiAzulClaro, RoundedCornerShape(16.dp))
            .padding(18.dp),
        verticalAlignment = Alignment.Top
    ) {
        if (icon != null) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(Color.White, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = GsiAzul654,
                    modifier = Modifier.size(22.dp)
                )
            }
            Spacer(modifier = Modifier.width(14.dp))
        }
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = GsiAzul654
            )
            Text(
                text = body,
                style = MaterialTheme.typography.bodySmall,
                color = GsiGrisTexto
            )
        }
    }
}
