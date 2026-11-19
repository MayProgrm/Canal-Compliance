package com.example.canaldedenunciasgsi.data

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

/**
 * Catálogo de estados y sucursales. Se alimenta del mismo `sucursales.json` que
 * usa el formulario web, empaquetado en `assets/data/sucursales.json`, para que
 * la app ofrezca exactamente las mismas opciones sin depender de la red.
 */
object SucursalesCatalog {

    private const val ASSET_PATH = "data/sucursales.json"

    @Volatile
    private var cached: Map<String, List<String>>? = null

    /** Estados ordenados alfabéticamente junto con sus sucursales. */
    fun load(context: Context): Map<String, List<String>> {
        cached?.let { return it }
        val loaded = read(context)
        cached = loaded
        return loaded
    }

    private fun read(context: Context): Map<String, List<String>> = try {
        val json = context.assets.open(ASSET_PATH).bufferedReader().use { it.readText() }
        val type = object : TypeToken<Map<String, List<String>>>() {}.type
        val map: Map<String, List<String>>? = Gson().fromJson(json, type)
        map?.toSortedMap() ?: emptyMap()
    } catch (_: Exception) {
        emptyMap()
    }
}
