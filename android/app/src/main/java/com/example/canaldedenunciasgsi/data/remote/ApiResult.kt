package com.example.canaldedenunciasgsi.data.remote

/** Motivo por el que una llamada a la API no pudo completarse. */
enum class ApiFailureKind {
    /** El folio no existe (HTTP 404). */
    NOT_FOUND,

    /** Falta la contraseña o es incorrecta (HTTP 401). */
    UNAUTHORIZED,

    /** La operación no aplica al estado actual, por ejemplo el chat deshabilitado (HTTP 409). */
    CONFLICT,

    /** El servidor respondió con un error (HTTP 5xx). */
    SERVER,

    /** No hubo conexión con el servidor. */
    NETWORK,

    /** Cualquier otro fallo. */
    UNKNOWN,
}

/** Resultado de una operación contra la API del canal. */
sealed interface ApiResult<out T> {

    data class Success<T>(val data: T) : ApiResult<T>

    data class Failure(
        val kind: ApiFailureKind,
        val detail: String? = null,
    ) : ApiResult<Nothing>
}

/** Devuelve el dato si la llamada fue correcta o `null` si falló. */
fun <T> ApiResult<T>.getOrNull(): T? = (this as? ApiResult.Success)?.data
