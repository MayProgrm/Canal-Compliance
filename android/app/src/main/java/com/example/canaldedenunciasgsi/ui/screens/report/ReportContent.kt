package com.example.canaldedenunciasgsi.ui.screens.report

import androidx.annotation.StringRes
import com.example.canaldedenunciasgsi.R

/** Aviso de privacidad que la persona debe leer y aceptar antes de iniciar su reporte. */
data class PrivacyNotice(
    val company: String,
    val fileUrl: String? = null
)

/** Respaldo local para que la pantalla siga disponible si falla la API. */
val privacyNotices = listOf(
    PrivacyNotice("COMETRA"),
    PrivacyNotice("GRUMER"),
    PrivacyNotice("SEGURITEC"),
    PrivacyNotice("SEPSA"),
    PrivacyNotice("TAMEME"),
    PrivacyNotice("TECNOVAL")
)

/** Opción seleccionable dentro del cuestionario. */
data class ReportOption(
    @param:StringRes val titleRes: Int,
    @param:StringRes val bodyRes: Int? = null
)

/** Acción que la persona desea realizar. */
val actionOptions = listOf(
    ReportOption(R.string.report_action_denuncia_title, R.string.report_action_denuncia_body),
    ReportOption(R.string.report_action_inquietud_title, R.string.report_action_inquietud_body)
)

/** Relación de la persona con la empresa. */
val relationOptions = listOf(
    ReportOption(R.string.report_relation_colaborador),
    ReportOption(R.string.report_relation_cliente),
    ReportOption(R.string.report_relation_proveedor)
)

/** Forma en que se desea enviar el reporte. */
val modeOptions = listOf(
    ReportOption(R.string.report_mode_anonymous_title, R.string.report_mode_anonymous_body),
    ReportOption(R.string.report_mode_identified_title, R.string.report_mode_identified_body)
)

/** Tipo de denuncia con los motivos que le corresponden. */
data class ReportCategory(
    @param:StringRes val titleRes: Int,
    val reasons: List<ReportOption>
)

/** Tipos de denuncia disponibles y sus motivos. */
val reportCategories = listOf(
    ReportCategory(
        R.string.report_category_harassment_title,
        listOf(
            ReportOption(R.string.report_reason_labor_harassment),
            ReportOption(R.string.report_reason_sexual_harassment),
            ReportOption(R.string.report_reason_discrimination),
            ReportOption(R.string.report_reason_labor_hostility),
            ReportOption(R.string.report_reason_sexual_hostility),
            ReportOption(R.string.report_reason_illegal_practices)
        )
    ),
    ReportCategory(
        R.string.report_category_conflicts_title,
        listOf(
            ReportOption(R.string.report_reason_conflict_of_interest),
            ReportOption(R.string.report_reason_internal_policy)
        )
    ),
    ReportCategory(
        R.string.report_category_data_title,
        listOf(
            ReportOption(R.string.report_reason_data_protection),
            ReportOption(R.string.report_reason_health_safety),
            ReportOption(R.string.report_reason_information_security)
        )
    ),
    ReportCategory(
        R.string.report_category_fraud_title,
        listOf(
            ReportOption(R.string.report_reason_money_laundering),
            ReportOption(R.string.report_reason_extortion),
            ReportOption(R.string.report_reason_embezzlement),
            ReportOption(R.string.report_reason_bribery),
            ReportOption(R.string.report_reason_asset_misuse),
            ReportOption(R.string.report_reason_fraud_corruption)
        )
    ),
    ReportCategory(
        R.string.report_category_competition_title,
        listOf(ReportOption(R.string.report_reason_competition_law))
    )
)

/** Respuestas de sí o no. */
val yesNoOptions = listOf(
    ReportOption(R.string.report_yes),
    ReportOption(R.string.report_no)
)

/** Participación de quien reporta en el hecho. */
val participationOptions = listOf(
    ReportOption(R.string.report_participation_knowledge),
    ReportOption(R.string.report_participation_witness),
    ReportOption(R.string.report_participation_victim)
)

/** Si el hecho ocurrió una sola vez o se repite. */
val recurrenceOptions = listOf(
    ReportOption(R.string.report_extra_recurrence_once),
    ReportOption(R.string.report_extra_recurrence_repeated)
)

/** Medio preferido para ser contactado. */
val contactPreferenceOptions = listOf(
    ReportOption(R.string.report_extra_contact_email),
    ReportOption(R.string.report_extra_contact_phone),
    ReportOption(R.string.report_extra_contact_any)
)
