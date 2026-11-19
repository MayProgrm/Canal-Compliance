package com.example.canaldedenunciasgsi.ui.screens.library

import androidx.annotation.StringRes
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Rule
import androidx.compose.material.icons.filled.Balance
import androidx.compose.material.icons.filled.Campaign
import androidx.compose.material.icons.filled.EditNote
import androidx.compose.material.icons.filled.Policy
import androidx.compose.material.icons.filled.PrivacyTip
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Shield
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiRojo

/** Documento principal de la biblioteca. */
data class LibraryDocument(
    @param:StringRes val titleRes: Int,
    @param:StringRes val bodyRes: Int,
    val icon: ImageVector,
    val accent: Color
)

/** Infografía o anuncio de difusión. */
data class LibraryInfographic(
    @param:StringRes val titleRes: Int,
    @param:StringRes val bodyRes: Int,
    val icon: ImageVector,
    val accent: Color
)

/** Novedad o mejora de la aplicación. */
data class LibraryUpdate(
    @param:StringRes val titleRes: Int,
    @param:StringRes val bodyRes: Int
)

/** Documentos principales del canal. */
val libraryDocuments: List<LibraryDocument> = listOf(
    LibraryDocument(
        R.string.library_doc_classification_title,
        R.string.library_doc_classification_body,
        Icons.AutoMirrored.Filled.Rule,
        GsiAzul654
    ),
    LibraryDocument(
        R.string.library_doc_ethics_title,
        R.string.library_doc_ethics_body,
        Icons.Filled.Balance,
        GsiAzul285
    ),
    LibraryDocument(
        R.string.library_doc_policies_title,
        R.string.library_doc_policies_body,
        Icons.Filled.Policy,
        GsiAzul654
    ),
    LibraryDocument(
        R.string.library_doc_privacy_title,
        R.string.library_doc_privacy_body,
        Icons.Filled.PrivacyTip,
        GsiAzul285
    )
)

/** Infografías y anuncios vigentes. */
val libraryInfographics: List<LibraryInfographic> = listOf(
    LibraryInfographic(
        R.string.library_info_report_title,
        R.string.library_info_report_body,
        Icons.Filled.EditNote,
        GsiAzul285
    ),
    LibraryInfographic(
        R.string.library_info_retaliation_title,
        R.string.library_info_retaliation_body,
        Icons.Filled.Shield,
        GsiRojo
    ),
    LibraryInfographic(
        R.string.library_info_confidentiality_title,
        R.string.library_info_confidentiality_body,
        Icons.Filled.PrivacyTip,
        GsiAzul654
    ),
    LibraryInfographic(
        R.string.library_info_campaign_title,
        R.string.library_info_campaign_body,
        Icons.Filled.Campaign,
        GsiAzul285
    )
)

/** Actualizaciones recientes de la aplicación. */
val libraryUpdates: List<LibraryUpdate> = listOf(
    LibraryUpdate(R.string.library_update_1_title, R.string.library_update_1_body),
    LibraryUpdate(R.string.library_update_2_title, R.string.library_update_2_body),
    LibraryUpdate(R.string.library_update_3_title, R.string.library_update_3_body),
    LibraryUpdate(R.string.library_update_4_title, R.string.library_update_4_body)
)

/** Icono usado para las novedades. */
val updateIcon: ImageVector = Icons.Filled.Refresh
