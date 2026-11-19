package com.example.canaldedenunciasgsi

import com.example.canaldedenunciasgsi.data.remote.ComplaintCatalog
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Verifica que el cuestionario traduce los índices de la interfaz a los valores
 * exactos que espera el servidor del canal.
 */
class ComplaintCatalogTest {

    @Test
    fun actionType_mapsKnownIndexes() {
        assertEquals("denuncia", ComplaintCatalog.actionType(0))
        assertEquals("inquietud", ComplaintCatalog.actionType(1))
    }

    @Test
    fun actionType_fallsBackToFirstWhenOutOfRange() {
        assertEquals("denuncia", ComplaintCatalog.actionType(-1))
        assertEquals("denuncia", ComplaintCatalog.actionType(99))
    }

    @Test
    fun relationship_mapsKnownIndexes() {
        assertEquals("Colaborador", ComplaintCatalog.relationship(0))
        assertEquals("Cliente", ComplaintCatalog.relationship(1))
        assertEquals("Proveedor", ComplaintCatalog.relationship(2))
    }

    @Test
    fun relationship_fallsBackToFirstWhenOutOfRange() {
        assertEquals("Colaborador", ComplaintCatalog.relationship(10))
    }

    @Test
    fun reporterRole_mapsKnownIndexes() {
        assertEquals("Conocimiento", ComplaintCatalog.reporterRole(0))
        assertEquals("Testigo", ComplaintCatalog.reporterRole(1))
        assertEquals("Víctima", ComplaintCatalog.reporterRole(2))
    }

    @Test
    fun contactPreference_mapsKnownIndexesAndFallsBackToAny() {
        assertEquals("email", ComplaintCatalog.contactPreference(0))
        assertEquals("phone", ComplaintCatalog.contactPreference(1))
        assertEquals("any", ComplaintCatalog.contactPreference(2))
        assertEquals("any", ComplaintCatalog.contactPreference(7))
    }

    @Test
    fun yesNo_returnsSiForFirstOption() {
        assertEquals("si", ComplaintCatalog.yesNo(0))
        assertEquals("no", ComplaintCatalog.yesNo(1))
        assertEquals("no", ComplaintCatalog.yesNo(5))
    }

    @Test
    fun boolean_returnsTextValuesForModelBooleanFields() {
        assertEquals("true", ComplaintCatalog.boolean(0))
        assertEquals("false", ComplaintCatalog.boolean(1))
        assertEquals("false", ComplaintCatalog.boolean(9))
    }

    @Test
    fun recurrence_isNoForSingleOccurrenceAndSiWhenRepeated() {
        assertEquals("no", ComplaintCatalog.recurrence(0))
        assertEquals("si", ComplaintCatalog.recurrence(1))
        assertEquals("no", ComplaintCatalog.recurrence(2))
    }

    @Test
    fun reason_mapsCategoryAndReason() {
        assertEquals("Acoso laboral", ComplaintCatalog.reason(0, 0))
        assertEquals("Acoso sexual", ComplaintCatalog.reason(0, 1))
        assertEquals("Prácticas laborales ilegales", ComplaintCatalog.reason(0, 5))
        assertEquals("Violación de la política interna (Código de Ética)", ComplaintCatalog.reason(1, 1))
        assertEquals("Fraude y corrupción", ComplaintCatalog.reason(3, 5))
    }

    @Test
    fun reason_fallsBackWhenIndexesOutOfRange() {
        assertEquals("Acoso laboral", ComplaintCatalog.reason(0, 99))
        assertEquals("Acoso laboral", ComplaintCatalog.reason(99, 99))
    }

    @Test
    fun reason_everyCategoryHasAtLeastOneReason() {
        for (category in 0 until 5) {
            val reason = ComplaintCatalog.reason(category, 0)
            assertTrue("La categoría $category debe tener motivos", reason.isNotBlank())
        }
    }
}
