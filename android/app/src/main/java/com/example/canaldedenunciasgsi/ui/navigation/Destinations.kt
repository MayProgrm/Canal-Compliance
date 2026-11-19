package com.example.canaldedenunciasgsi.ui.navigation

/**
 * Rutas de navegación de la aplicación.
 */
object Destinations {
    const val HOME = "home"
    const val REPORT = "report"
    const val TRACK = "track"
    const val GUIDE = "guide"
    const val FAQ = "faq"
    const val LIBRARY = "library"

    /** Parámetro con el folio del reporte. Se usa en el comprobante y en la consulta. */
    const val ARG_FOLIO = "folio"

    /** Comprobante del reporte recién enviado. */
    const val REPORT_SUCCESS = "report_success"
    const val REPORT_SUCCESS_ROUTE = "$REPORT_SUCCESS/{$ARG_FOLIO}"

    /**
     * Consulta del reporte. El folio es opcional: solo se envía cuando el usuario
     * llega desde el comprobante, para no autorrellenar la consulta si entra
     * directamente desde la pestaña.
     */
    const val TRACK_ROUTE = "$TRACK?$ARG_FOLIO={$ARG_FOLIO}"

    /** Ruta del comprobante para el folio indicado. */
    fun reportSuccess(folio: String) = "$REPORT_SUCCESS/$folio"

    /** Ruta de la consulta con el folio precargado. */
    fun track(folio: String) = "$TRACK?$ARG_FOLIO=$folio"
}
