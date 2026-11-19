package com.example.canaldedenunciasgsi.ui.screens.guide

import androidx.annotation.ArrayRes
import androidx.annotation.StringRes
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Assignment
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.automirrored.outlined.Rule
import androidx.compose.material.icons.outlined.Handshake
import androidx.compose.material.icons.outlined.Timeline
import androidx.compose.material.icons.outlined.TrackChanges
import androidx.compose.material.icons.outlined.Translate
import androidx.compose.material.icons.outlined.VerifiedUser
import androidx.compose.ui.graphics.vector.ImageVector
import com.example.canaldedenunciasgsi.R

/** Punto con título y descripción dentro de una sección. */
data class GuideEntry(
    @param:StringRes val titleRes: Int,
    @param:StringRes val bodyRes: Int
)

/** Grupo de viñetas con su propio subtítulo. */
data class GuideBulletGroup(
    @param:StringRes val titleRes: Int,
    @param:ArrayRes val itemsRes: Int,
    val isNegative: Boolean = false
)

/** Sección de la guía de uso. */
data class GuideSection(
    @param:StringRes val titleRes: Int,
    val icon: ImageVector,
    @param:StringRes val bodyRes: Int? = null,
    val entries: List<GuideEntry> = emptyList(),
    val bulletGroups: List<GuideBulletGroup> = emptyList()
)

/** Contenido completo de la Guía de uso. */
val guideSections: List<GuideSection> = listOf(
    GuideSection(
        titleRes = R.string.guide_intro_title,
        icon = Icons.AutoMirrored.Outlined.MenuBook,
        bodyRes = R.string.guide_intro_body,
        entries = listOf(
            GuideEntry(R.string.guide_intro_purpose_title, R.string.guide_intro_purpose_body),
            GuideEntry(R.string.guide_intro_scope_title, R.string.guide_intro_scope_body),
            GuideEntry(R.string.guide_intro_principles_title, R.string.guide_intro_principles_body)
        )
    ),
    GuideSection(
        titleRes = R.string.guide_rights_title,
        icon = Icons.Outlined.VerifiedUser,
        entries = listOf(
            GuideEntry(R.string.guide_rights_confidentiality_title, R.string.guide_rights_confidentiality_body),
            GuideEntry(R.string.guide_rights_protection_title, R.string.guide_rights_protection_body),
            GuideEntry(R.string.guide_rights_heard_title, R.string.guide_rights_heard_body)
        )
    ),
    GuideSection(
        titleRes = R.string.guide_commitments_title,
        icon = Icons.Outlined.Handshake,
        entries = listOf(
            GuideEntry(R.string.guide_commitments_impartiality_title, R.string.guide_commitments_impartiality_body),
            GuideEntry(R.string.guide_commitments_process_title, R.string.guide_commitments_process_body),
            GuideEntry(R.string.guide_commitments_transparency_title, R.string.guide_commitments_transparency_body)
        )
    ),
    GuideSection(
        titleRes = R.string.guide_what_title,
        icon = Icons.AutoMirrored.Outlined.Rule,
        bulletGroups = listOf(
            GuideBulletGroup(R.string.guide_what_yes_title, R.array.guide_what_yes_items),
            GuideBulletGroup(
                R.string.guide_what_no_title,
                R.array.guide_what_no_items,
                isNegative = true
            )
        )
    ),
    GuideSection(
        titleRes = R.string.guide_how_title,
        icon = Icons.AutoMirrored.Outlined.Assignment,
        bodyRes = R.string.guide_how_body,
        entries = listOf(
            GuideEntry(R.string.guide_how_step1_title, R.string.guide_how_step1_body),
            GuideEntry(R.string.guide_how_step2_title, R.string.guide_how_step2_body),
            GuideEntry(R.string.guide_how_step3_title, R.string.guide_how_step3_body),
            GuideEntry(R.string.guide_how_step4_title, R.string.guide_how_step4_body)
        )
    ),
    GuideSection(
        titleRes = R.string.guide_after_title,
        icon = Icons.Outlined.Timeline,
        bodyRes = R.string.guide_after_body,
        bulletGroups = listOf(
            GuideBulletGroup(R.string.guide_after_stages_title, R.array.guide_after_stages_items)
        )
    ),
    GuideSection(
        titleRes = R.string.guide_tracking_title,
        icon = Icons.Outlined.TrackChanges,
        entries = listOf(
            GuideEntry(R.string.guide_tracking_online_title, R.string.guide_tracking_online_body),
            GuideEntry(R.string.guide_tracking_updates_title, R.string.guide_tracking_updates_body),
            GuideEntry(R.string.guide_tracking_status_title, R.string.guide_tracking_status_body)
        )
    ),
    GuideSection(
        titleRes = R.string.guide_glossary_title,
        icon = Icons.Outlined.Translate,
        entries = listOf(
            GuideEntry(R.string.guide_glossary_report_title, R.string.guide_glossary_report_body),
            GuideEntry(R.string.guide_glossary_reporter_title, R.string.guide_glossary_reporter_body),
            GuideEntry(R.string.guide_glossary_confidentiality_title, R.string.guide_glossary_confidentiality_body),
            GuideEntry(R.string.guide_glossary_retaliation_title, R.string.guide_glossary_retaliation_body),
            GuideEntry(R.string.guide_glossary_due_process_title, R.string.guide_glossary_due_process_body),
            GuideEntry(R.string.guide_glossary_good_faith_title, R.string.guide_glossary_good_faith_body),
            GuideEntry(R.string.guide_glossary_code_title, R.string.guide_glossary_code_body)
        )
    )
)
