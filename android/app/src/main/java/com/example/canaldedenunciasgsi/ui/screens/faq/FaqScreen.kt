package com.example.canaldedenunciasgsi.ui.screens.faq

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.HelpOutline
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.components.ExpandableCard
import com.example.canaldedenunciasgsi.ui.components.LeadCard
import com.example.canaldedenunciasgsi.ui.components.RevealItem
import com.example.canaldedenunciasgsi.ui.theme.CanalDeDenunciasGSITheme
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto

/**
 * Preguntas frecuentes sobre el uso del canal.
 * Cada pregunta se despliega al tocarla para mostrar su respuesta.
 */
@Composable
fun FaqScreen(modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item(key = "lead", contentType = "header") {
            RevealItem {
                LeadCard(
                    title = stringResource(R.string.faq_intro_title),
                    body = stringResource(R.string.faq_intro_body),
                    icon = Icons.AutoMirrored.Filled.HelpOutline
                )
            }
        }
        items(
            items = faqItems,
            key = { it.questionRes },
            contentType = { "question" }
        ) { item ->
            RevealItem {
                ExpandableCard(title = stringResource(item.questionRes)) {
                    Text(
                        text = stringResource(item.answerRes),
                        style = MaterialTheme.typography.bodyMedium,
                        color = GsiGrisTexto
                    )
                }
            }
        }
        item(key = "spacer", contentType = "spacer") {
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun FaqScreenPreview() {
    CanalDeDenunciasGSITheme {
        FaqScreen()
    }
}
