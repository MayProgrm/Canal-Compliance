package com.example.canaldedenunciasgsi.data.remote

/**
 * Traduce las opciones del cuestionario (índices de la interfaz) a los valores
 * que espera el servidor del canal.
 *
 * Los motivos usan exactamente los valores declarados en `Complaint.CATEGORY_CHOICES`
 * de Django, porque el serializer de alta valida ese campo contra esa lista.
 */
object ComplaintCatalog {

    /** Tipos de acción aceptados por el servidor. */
    private val ACTIONS = listOf("denuncia", "inquietud")

    /** Relación con la empresa. */
    private val RELATIONSHIPS = listOf("Colaborador", "Cliente", "Proveedor")

    /** Participación del denunciante en el hecho. */
    private val REPORTER_ROLES = listOf("Conocimiento", "Testigo", "Víctima")

    /** Preferencia de contacto. */
    private val CONTACT_PREFERENCES = listOf("email", "phone", "any")

    /** Motivos por categoría, en el mismo orden que el cuestionario. */
    private val REASONS = listOf(
        listOf(
            "Acoso laboral",
            "Acoso sexual",
            "Discriminación",
            "Hostigamiento laboral",
            "Hostigamiento sexual",
            "Prácticas laborales ilegales",
        ),
        listOf(
            "Conflictos de interés",
            "Violación de la política interna (Código de Ética)",
        ),
        listOf(
            "Incumplimiento de la normativa de Protección de Datos",
            "Incumplimientos graves de seguridad y salud laboral",
            "Violación de la seguridad de la información",
        ),
        listOf(
            "Blanqueo de capitales",
            "Extorsión",
            "Malversación o robo",
            "Soborno",
            "Uso indebido de activos/recursos de la empresa",
            "Fraude y corrupción",
        ),
        listOf(
            "Infracciones de derecho de la competencia",
        ),
    )

    fun actionType(index: Int): String = ACTIONS.getOrElse(index) { ACTIONS.first() }

    fun relationship(index: Int): String = RELATIONSHIPS.getOrElse(index) { RELATIONSHIPS.first() }

    fun reporterRole(index: Int): String = REPORTER_ROLES.getOrElse(index) { REPORTER_ROLES.first() }

    fun contactPreference(index: Int): String =
        CONTACT_PREFERENCES.getOrElse(index) { "any" }

    /** `si` / `no` para las preguntas de sí o no declaradas como texto. */
    fun yesNo(index: Int): String = if (index == 0) "si" else "no"

    /**
     * `true` / `false` para los campos booleanos del modelo (`knows_actor`,
     * `has_witnesses`). El serializer los valida como `BooleanField`, por lo que
     * no acepta `si` / `no`.
     */
    fun boolean(index: Int): String = if (index == 0) "true" else "false"

    /** `no` cuando el hecho fue único y `si` cuando se repite. */
    fun recurrence(index: Int): String = if (index == 1) "si" else "no"

    /** Motivo elegido, según la categoría y el motivo seleccionados. */
    fun reason(categoryIndex: Int, reasonIndex: Int): String {
        val reasons = REASONS.getOrElse(categoryIndex) { REASONS.first() }
        return reasons.getOrElse(reasonIndex) { reasons.first() }
    }
}
