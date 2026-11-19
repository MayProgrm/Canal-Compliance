package com.example.canaldedenunciasgsi.ui.screens.guide

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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringArrayResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.components.ExpandableCard
import com.example.canaldedenunciasgsi.ui.components.LeadCard
import com.example.canaldedenunciasgsi.ui.components.RevealItem
import com.example.canaldedenunciasgsi.ui.theme.CanalDeDenunciasGSITheme
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiRojo

/**
 * Guía de uso del Canal GSI.
 * Cada apartado se muestra como una tarjeta desplegable para evitar
 * que la información se vea aglomerada.
 */
@Composable
fun GuideScreen(modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item(key = "lead", contentType = "header") {
            RevealItem {
                LeadCard(
                    title = stringResource(R.string.guide_lead_title),
                    body = stringResource(R.string.guide_lead_body),
                    icon = Icons.AutoMirrored.Filled.MenuBook
                )
            }
        }
        items(
            items = guideSections,
            key = { it.titleRes },
            contentType = { "section" }
        ) { section ->
            RevealItem {
                GuideSectionAccordion(section = section)
            }
        }
        item(key = "spacer", contentType = "spacer") {
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

/** Apartado de la guía: título visible y contenido desplegable. */
@Composable
private fun GuideSectionAccordion(
    section: GuideSection,
    modifier: Modifier = Modifier
) {
    ExpandableCard(
        title = stringResource(section.titleRes),
        leadingIcon = section.icon,
        modifier = modifier
    ) {
        section.bodyRes?.let { bodyRes ->
            Text(
                text = stringResource(bodyRes),
                style = MaterialTheme.typography.bodySmall,
                color = GsiGrisTexto
            )
        }

        section.entries.forEach { entry ->
            GuideEntryRow(entry = entry)
        }

        section.bulletGroups.forEach { group ->
            GuideBulletGroupView(group = group)
        }
    }
}

/** Punto con título y descripción dentro de una sección. */
@Composable
private fun GuideEntryRow(
    entry: GuideEntry,
    modifier: Modifier = Modifier
) {
    Row(modifier = modifier.fillMaxWidth()) {
        Box(
            modifier = Modifier
                .padding(top = 3.dp)
                .size(width = 4.dp, height = 16.dp)
                .background(GsiAzul285, RoundedCornerShape(2.dp))
        )
        Spacer(modifier = Modifier.width(12.dp))
        Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(
                text = stringResource(entry.titleRes),
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
                color = GsiAzul654
            )
            Text(
                text = stringResource(entry.bodyRes),
                style = MaterialTheme.typography.bodySmall,
                color = GsiGrisTexto
            )
        }
    }
}

/** Grupo de viñetas con su propio subtítulo. */
@Composable
private fun GuideBulletGroupView(
    group: GuideBulletGroup,
    modifier: Modifier = Modifier
) {
    val accent = if (group.isNegative) GsiRojo else GsiAzul285
    val titleColor = if (group.isNegative) GsiRojo else GsiAzul654
    val items = stringArrayResource(group.itemsRes).toList()

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = stringResource(group.titleRes),
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.SemiBold,
            color = titleColor
        )
        items.forEach { item ->
            Row(modifier = Modifier.fillMaxWidth()) {
                Box(
                    modifier = Modifier
                        .padding(top = 7.dp)
                        .size(6.dp)
                        .background(accent, CircleShape)
                )
                Spacer(modifier = Modifier.width(10.dp))
                Text(
                    text = item,
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun GuideScreenPreview() {
    CanalDeDenunciasGSITheme {
        GuideScreen()
    }
}
