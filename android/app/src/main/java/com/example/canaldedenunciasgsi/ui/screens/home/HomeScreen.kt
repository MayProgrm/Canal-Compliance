package com.example.canaldedenunciasgsi.ui.screens.home

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.filled.Campaign
import androidx.compose.material.icons.filled.Category
import androidx.compose.material.icons.filled.Gavel
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.components.FloatingCircles
import com.example.canaldedenunciasgsi.ui.components.RevealItem
import com.example.canaldedenunciasgsi.ui.components.SectionTitle
import com.example.canaldedenunciasgsi.ui.components.pressScale
import com.example.canaldedenunciasgsi.ui.theme.CanalDeDenunciasGSITheme
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro
import com.example.canaldedenunciasgsi.ui.theme.GsiRojo

private data class HowItWorksStep(
    val titleRes: Int,
    val bodyRes: Int
)

private data class ReportType(
    val titleRes: Int,
    val bodyRes: Int,
    val icon: ImageVector,
    val accent: Color
)

/**
 * Página principal del Canal GSI.
 * Los bloques aparecen con un desvanecimiento a medida que se desplaza la pantalla.
 */
@Composable
fun HomeScreen(
    onReportClick: () -> Unit,
    onTrackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        item(key = "hero", contentType = "hero") {
            RevealItem {
                HeroSection(onReportClick = onReportClick, onTrackClick = onTrackClick)
            }
        }
        item(key = "confidentiality", contentType = "notice") {
            RevealItem { ConfidentialityNotice() }
        }
        item(key = "types", contentType = "section") {
            RevealItem { ReportTypesSection() }
        }
        item(key = "how", contentType = "section") {
            RevealItem { HowItWorksSection() }
        }
        item(key = "spacer", contentType = "spacer") {
            Spacer(modifier = Modifier.height(12.dp))
        }
    }
}

/** Encabezado principal con el mensaje del canal y los accesos rápidos. */
@Composable
private fun HeroSection(
    onReportClick: () -> Unit,
    onTrackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val reportInteraction = remember { MutableInteractionSource() }
    val trackInteraction = remember { MutableInteractionSource() }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(
                Brush.linearGradient(
                    colors = listOf(GsiAzul654, GsiAzul285)
                )
            )
    ) {
        // Adornos de profundidad en movimiento
        FloatingCircles()

        Column(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = stringResource(R.string.home_eyebrow),
                style = MaterialTheme.typography.labelSmall,
                letterSpacing = 1.6.sp,
                color = Color.White.copy(alpha = 0.78f)
            )
            Text(
                text = stringResource(R.string.home_title),
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White
            )
            Text(
                text = stringResource(R.string.home_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.9f)
            )
            Button(
                onClick = onReportClick,
                interactionSource = reportInteraction,
                modifier = Modifier
                    .fillMaxWidth()
                    .pressScale(reportInteraction),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.White,
                    contentColor = GsiAzul654
                )
            ) {
                Icon(
                    imageVector = Icons.Filled.Campaign,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = stringResource(R.string.home_cta_report),
                    style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.padding(start = 8.dp)
                )
            }
            OutlinedButton(
                onClick = onTrackClick,
                interactionSource = trackInteraction,
                modifier = Modifier
                    .fillMaxWidth()
                    .pressScale(trackInteraction),
                border = BorderStroke(1.dp, Color.White.copy(alpha = 0.7f)),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)
            ) {
                Icon(
                    imageVector = Icons.Filled.Search,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = stringResource(R.string.home_cta_track),
                    style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.padding(start = 8.dp)
                )
            }
        }
    }
}

@Composable
private fun ConfidentialityNotice(modifier: Modifier = Modifier) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(GsiAzulClaro)
            .padding(16.dp),
        verticalAlignment = Alignment.Top
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .background(Color.White, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.Lock,
                contentDescription = null,
                tint = GsiAzul654,
                modifier = Modifier.size(19.dp)
            )
        }
        Spacer(modifier = Modifier.width(14.dp))
        Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(
                text = stringResource(R.string.home_confidentiality_title),
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
                color = GsiAzul654
            )
            Text(
                text = stringResource(R.string.home_confidentiality_body),
                style = MaterialTheme.typography.bodySmall,
                color = GsiGrisTexto
            )
        }
    }
}

@Composable
private fun ReportTypesSection(modifier: Modifier = Modifier) {
    val types = listOf(
        ReportType(
            R.string.home_type_inquietud_title,
            R.string.home_type_inquietud_body,
            Icons.Filled.Lightbulb,
            GsiAzul654
        ),
        ReportType(
            R.string.home_type_denuncia_title,
            R.string.home_type_denuncia_body,
            Icons.Filled.Gavel,
            GsiRojo
        )
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        SectionTitle(
            text = stringResource(R.string.home_types_title),
            icon = Icons.Filled.Category
        )
        Spacer(modifier = Modifier.height(2.dp))
        types.forEach { type ->
            ReportTypeCard(type = type)
        }
    }
}

@Composable
private fun ReportTypeCard(
    type: ReportType,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, GsiGrisBorde),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .background(type.accent.copy(alpha = 0.12f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = type.icon,
                    contentDescription = null,
                    tint = type.accent,
                    modifier = Modifier.size(22.dp)
                )
            }
            Spacer(modifier = Modifier.width(14.dp))
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(3.dp)
            ) {
                Text(
                    text = stringResource(type.titleRes),
                    style = MaterialTheme.typography.titleMedium,
                    color = GsiNegro
                )
                Text(
                    text = stringResource(type.bodyRes),
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }
        }
    }
}

@Composable
private fun HowItWorksSection(modifier: Modifier = Modifier) {
    val steps = listOf(
        HowItWorksStep(R.string.home_how_1_title, R.string.home_how_1_body),
        HowItWorksStep(R.string.home_how_2_title, R.string.home_how_2_body),
        HowItWorksStep(R.string.home_how_3_title, R.string.home_how_3_body),
        HowItWorksStep(R.string.home_how_4_title, R.string.home_how_4_body)
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        SectionTitle(
            text = stringResource(R.string.home_how_title),
            icon = Icons.AutoMirrored.Filled.FactCheck
        )
        Spacer(modifier = Modifier.height(10.dp))
        steps.forEachIndexed { index, step ->
            StepItem(
                number = index + 1,
                titleRes = step.titleRes,
                bodyRes = step.bodyRes,
                isLast = index == steps.lastIndex
            )
        }
    }
}

@Composable
private fun StepItem(
    number: Int,
    titleRes: Int,
    bodyRes: Int,
    isLast: Boolean,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(IntrinsicSize.Min)
    ) {
        Column(
            modifier = Modifier.fillMaxHeight(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .background(GsiAzul654, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = number.toString(),
                    color = Color.White,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold
                )
            }
            if (!isLast) {
                Box(
                    modifier = Modifier
                        .width(2.dp)
                        .weight(1f)
                        .background(GsiGrisBorde)
                )
            }
        }
        Spacer(modifier = Modifier.width(14.dp))
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(bottom = if (isLast) 0.dp else 18.dp),
            verticalArrangement = Arrangement.spacedBy(3.dp)
        ) {
            Text(
                text = stringResource(titleRes),
                style = MaterialTheme.typography.titleMedium,
                color = GsiNegro,
                modifier = Modifier.padding(top = 5.dp)
            )
            Text(
                text = stringResource(bodyRes),
                style = MaterialTheme.typography.bodySmall,
                color = GsiGrisTexto
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun HomeScreenPreview() {
    CanalDeDenunciasGSITheme {
        HomeScreen(onReportClick = {}, onTrackClick = {})
    }
}
