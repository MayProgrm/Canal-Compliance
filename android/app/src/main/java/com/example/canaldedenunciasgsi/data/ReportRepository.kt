package com.example.canaldedenunciasgsi.data

import android.content.Context
import androidx.annotation.StringRes
import com.example.canaldedenunciasgsi.R
import org.json.JSONArray
import org.json.JSONObject
import java.util.Random

/** Estado del reporte dentro del proceso de atención. */
enum class ReportStatus(
    @param:StringRes val labelRes: Int,
    @param:StringRes val nextStepRes: Int
) {
    RECEIVED(R.string.track_status_received, R.string.track_next_received),
    REVIEW(R.string.track_status_review, R.string.track_next_review),
    INVESTIGATION(R.string.track_status_investigation, R.string.track_next_investigation),
    RESOLUTION(R.string.track_status_resolution, R.string.track_next_resolution),
    CLOSED(R.string.track_status_closed, R.string.track_next_closed)
}

/** Avance registrado sobre un reporte. */
data class ReportUpdate(
    val date: String,
    @param:StringRes val textRes: Int
)

/** Reporte recibido por el canal. */
data class ReportRecord(
    val folio: String,
    val password: String,
    val createdAt: String,
    @param:StringRes val actionRes: Int,
    @param:StringRes val categoryRes: Int,
    @param:StringRes val reasonRes: Int,
    val anonymous: Boolean,
    val name: String?,
    val email: String?,
    val phone: String?,
    val files: List<String>,
    val status: ReportStatus,
    val updates: List<ReportUpdate>
)

/**
 * Almacén local de reportes.
 *
 * La aplicación todavía no cuenta con el servidor del canal, por lo que este
 * repositorio cumple el papel del panel de control: genera el folio, guarda el
 * reporte y lo devuelve cuando se consulta con el folio y la contraseña.
 */
object ReportRepository {

    private const val PREFS = "gsi_reportes"
    private const val KEY_RECORDS = "reportes"

    /** Caracteres sin ambigüedad para formar el folio. */
    private const val FOLIO_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    private const val FOLIO_LENGTH = 6
    private const val FOLIO_PREFIX = "GSI-"

    private val random = Random()

    /** Genera un folio con el formato GSI-XXXXXX. */
    fun generateFolio(): String {
        val suffix = (1..FOLIO_LENGTH)
            .map { FOLIO_CHARS[random.nextInt(FOLIO_CHARS.length)] }
            .joinToString("")
        return FOLIO_PREFIX + suffix
    }

    /** Registra un reporte y lo devuelve ya almacenado. */
    fun submit(context: Context, record: ReportRecord): ReportRecord {
        val updated = load(context) + record
        save(context, updated)
        return record
    }

    /** Devuelve el reporte que coincide con el folio y la contraseña. */
    fun find(context: Context, folio: String, password: String): ReportRecord? {
        val normalized = folio.trim().uppercase()
        return load(context).firstOrNull {
            it.folio.equals(normalized, ignoreCase = true) && it.password == password
        }
    }

    /** Devuelve el reporte que coincide con el folio. */
    fun findByFolio(context: Context, folio: String): ReportRecord? {
        val normalized = folio.trim().uppercase()
        return load(context).firstOrNull { it.folio.equals(normalized, ignoreCase = true) }
    }

    private fun load(context: Context): List<ReportRecord> {
        val raw = prefs(context).getString(KEY_RECORDS, null) ?: return emptyList()
        return runCatching {
            val array = JSONArray(raw)
            (0 until array.length()).map { jsonToRecord(array.getJSONObject(it)) }
        }.getOrDefault(emptyList())
    }

    private fun save(context: Context, records: List<ReportRecord>) {
        val array = JSONArray()
        records.forEach { array.put(recordToJson(it)) }
        prefs(context).edit().putString(KEY_RECORDS, array.toString()).apply()
    }

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun recordToJson(record: ReportRecord): JSONObject = JSONObject().apply {
        put("folio", record.folio)
        put("password", record.password)
        put("createdAt", record.createdAt)
        put("actionRes", record.actionRes)
        put("categoryRes", record.categoryRes)
        put("reasonRes", record.reasonRes)
        put("anonymous", record.anonymous)
        put("name", record.name)
        put("email", record.email)
        put("phone", record.phone)
        put("status", record.status.name)
        put("files", JSONArray(record.files))
        put(
            "updates",
            JSONArray().apply {
                record.updates.forEach { update ->
                    put(
                        JSONObject().apply {
                            put("date", update.date)
                            put("textRes", update.textRes)
                        }
                    )
                }
            }
        )
    }

    private fun jsonToRecord(json: JSONObject): ReportRecord = ReportRecord(
        folio = json.getString("folio"),
        password = json.getString("password"),
        createdAt = json.getString("createdAt"),
        actionRes = json.getInt("actionRes"),
        categoryRes = json.getInt("categoryRes"),
        reasonRes = json.getInt("reasonRes"),
        anonymous = json.getBoolean("anonymous"),
        name = json.optString("name").ifEmpty { null },
        email = json.optString("email").ifEmpty { null },
        phone = json.optString("phone").ifEmpty { null },
        files = json.optJSONArray("files")?.let { array ->
            (0 until array.length()).map { array.getString(it) }
        }.orEmpty(),
        status = runCatching { ReportStatus.valueOf(json.getString("status")) }
            .getOrDefault(ReportStatus.RECEIVED),
        updates = json.optJSONArray("updates")?.let { array ->
            (0 until array.length()).map { index ->
                val item = array.getJSONObject(index)
                ReportUpdate(item.getString("date"), item.getInt("textRes"))
            }
        }.orEmpty()
    )
}
