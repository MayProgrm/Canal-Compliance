package com.example.canaldedenunciasgsi.ui.screens.faq

import androidx.annotation.StringRes
import com.example.canaldedenunciasgsi.R

/** Pregunta frecuente con su respuesta. */
data class FaqItem(
    @param:StringRes val questionRes: Int,
    @param:StringRes val answerRes: Int
)

/** Listado completo de preguntas frecuentes del canal. */
val faqItems: List<FaqItem> = listOf(
    FaqItem(R.string.faq_q1, R.string.faq_a1),
    FaqItem(R.string.faq_q2, R.string.faq_a2),
    FaqItem(R.string.faq_q3, R.string.faq_a3),
    FaqItem(R.string.faq_q4, R.string.faq_a4),
    FaqItem(R.string.faq_q5, R.string.faq_a5),
    FaqItem(R.string.faq_q6, R.string.faq_a6),
    FaqItem(R.string.faq_q7, R.string.faq_a7),
    FaqItem(R.string.faq_q8, R.string.faq_a8),
    FaqItem(R.string.faq_q9, R.string.faq_a9),
    FaqItem(R.string.faq_q10, R.string.faq_a10),
    FaqItem(R.string.faq_q11, R.string.faq_a11),
    FaqItem(R.string.faq_q12, R.string.faq_a12)
)
