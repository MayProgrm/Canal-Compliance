package com.example.canaldedenunciasgsi

import com.example.canaldedenunciasgsi.data.remote.ApiFailureKind
import com.example.canaldedenunciasgsi.data.remote.ApiResult
import com.example.canaldedenunciasgsi.data.remote.getOrNull
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** Verifica el envoltorio de resultados que usa la app contra la API. */
class ApiResultTest {

    @Test
    fun getOrNull_returnsDataWhenSuccess() {
        val result: ApiResult<String> = ApiResult.Success("DEN-2026-000123")
        assertEquals("DEN-2026-000123", result.getOrNull())
    }

    @Test
    fun getOrNull_returnsNullWhenFailure() {
        val result: ApiResult<String> =
            ApiResult.Failure(ApiFailureKind.NOT_FOUND, "El folio no existe")
        assertNull(result.getOrNull())
    }

    @Test
    fun success_wrapsData() {
        val success = ApiResult.Success(42)
        assertEquals(42, success.data)
    }

    @Test
    fun failure_keepsKindAndDetail() {
        val failure = ApiResult.Failure(ApiFailureKind.UNAUTHORIZED, "Contraseña incorrecta")
        assertEquals(ApiFailureKind.UNAUTHORIZED, failure.kind)
        assertEquals("Contraseña incorrecta", failure.detail)
    }

    @Test
    fun failure_detailDefaultsToNull() {
        val failure = ApiResult.Failure(ApiFailureKind.NETWORK)
        assertNull(failure.detail)
    }

    @Test
    fun failureKinds_coverExpectedHttpScenarios() {
        val kinds = ApiFailureKind.values().toList()
        assertEquals(
            listOf(
                ApiFailureKind.NOT_FOUND,
                ApiFailureKind.UNAUTHORIZED,
                ApiFailureKind.CONFLICT,
                ApiFailureKind.SERVER,
                ApiFailureKind.NETWORK,
                ApiFailureKind.UNKNOWN,
            ),
            kinds,
        )
    }
}
