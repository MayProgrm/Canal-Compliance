package com.example.canaldedenunciasgsi.ui.screens.library

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.LibraryBooks
import androidx.compose.material.icons.filled.Campaign
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.NewReleases
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.components.LeadCard
import com.example.canaldedenunciasgsi.ui.components.RevealItem
import com.example.canaldedenunciasgsi.ui.components.SectionTitle
import com.example.canaldedenunciasgsi.ui.theme.CanalDeDenunciasGSITheme
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro

/**
 * Biblioteca GSI: documentos principales, infografías y anuncios,
 * y las actualizaciones recientes de la aplicación.
 */
@Composable
fun LibraryScreen(modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item(key = "lead", contentType = "header") {
            RevealItem {
                LeadCard(
                    title = stringResource(R.string.library_lead_title),
                    body = stringResource(R.string.library_lead_body),
                    icon = Icons.AutoMirrored.Filled.LibraryBooks
                )
            }
        }
        item(key = "docs-header", contentType = "header") {
            RevealItem {
                SectionHeader(
                    title = stringResource(R.string.library_docs_title),
                    subtitle = stringResource(R.string.library_docs_subtitle),
                    icon = Icons.Filled.Description
                )
            }
        }
        items(
            items = libraryDocuments,
            key = { it.titleRes },
            contentType = { "document" }
        ) { document ->
            RevealItem { DocumentCard(document = document) }
        }

        item(key = "infographics-header", contentType = "header") {
            RevealItem {
                SectionHeader(
                    title = stringResource(R.string.library_infographics_title),
                    subtitle = stringResource(R.string.library_infographics_subtitle),
                    icon = Icons.Filled.Campaign
                )
            }
        }
        item(key = "infographics-row", contentType = "carousel") {
            RevealItem { InfographicsRow() }
        }

        item(key = "updates-header", contentType = "header") {
            RevealItem {
                SectionHeader(
                    title = stringResource(R.string.library_updates_title),
                    subtitle = stringResource(R.string.library_updates_subtitle),
                    icon = Icons.Filled.NewReleases
                )
            }
        }
        items(
            items = libraryUpdates,
            key = { it.titleRes },
            contentType = { "update" }
        ) { update ->
            RevealItem { UpdateRow(update = update) }
        }

        item(key = "spacer", contentType = "spacer") {
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

/** Encabezado de sección con su descripción. */
@Composable
private fun SectionHeader(
    title: String,
    subtitle: String,
    icon: ImageVector,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(top = 6.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        SectionTitle(text = title, icon = icon)
        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
    }
}

/** Tarjeta de un documento principal. */
@Composable
private fun DocumentCard(
    document: LibraryDocument,
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
                    .background(document.accent.copy(alpha = 0.12f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = document.icon,
                    contentDescription = null,
                    tint = document.accent,
                    modifier = Modifier.size(22.dp)
                )
            }
            Spacer(modifier = Modifier.width(14.dp))
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(3.dp)
            ) {
                Text(
                    text = stringResource(document.titleRes),
                    style = MaterialTheme.typography.titleMedium,
                    color = GsiNegro
                )
                Text(
                    text = stringResource(document.bodyRes),
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }
        }
    }
}

/** Carrusel horizontal de infografías y anuncios. */
@Composable
private fun InfographicsRow(modifier: Modifier = Modifier) {
    LazyRow(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(
            items = libraryInfographics,
            key = { it.titleRes },
            contentType = { "infographic" }
        ) { infographic ->
            InfographicCard(infographic = infographic)
        }
    }
}

/** Tarjeta de una infografía o anuncio. */
@Composable
private fun InfographicCard(
    infographic: LibraryInfographic,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.width(220.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, GsiGrisBorde),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column {
            // Franja de color superior para dar apariencia de cartel.
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .background(infographic.accent)
            )
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(infographic.accent.copy(alpha = 0.12f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = infographic.icon,
                        contentDescription = null,
                        tint = infographic.accent,
                        modifier = Modifier.size(20.dp)
                    )
                }
                Text(
                    text = stringResource(infographic.titleRes),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = GsiNegro
                )
                Text(
                    text = stringResource(infographic.bodyRes),
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }
        }
    }
}

/** Fila de una actualización reciente de la aplicación. */
@Composable
private fun UpdateRow(
    update: LibraryUpdate,
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
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .background(GsiAzul285.copy(alpha = 0.12f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = updateIcon,
                    contentDescription = null,
                    tint = GsiAzul285,
                    modifier = Modifier.size(18.dp)
                )
            }
            Spacer(modifier = Modifier.width(14.dp))
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(3.dp)
            ) {
                Text(
                    text = stringResource(update.titleRes),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = GsiNegro
                )
                Text(
                    text = stringResource(update.bodyRes),
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun LibraryScreenPreview() {
    CanalDeDenunciasGSITheme {
        LibraryScreen()
    }
}
