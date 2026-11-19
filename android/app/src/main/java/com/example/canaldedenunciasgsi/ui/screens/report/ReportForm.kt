package com.example.canaldedenunciasgsi.ui.screens.report

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.StringRes
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyItemScope
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Assignment
import androidx.compose.material.icons.automirrored.filled.EventNote
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.automirrored.filled.Notes
import androidx.compose.material.icons.automirrored.filled.Rule
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Business
import androidx.compose.material.icons.filled.Category
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.EditNote
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Groups
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Key
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.Policy
import androidx.compose.material.icons.filled.Quiz
import androidx.compose.material.icons.filled.RadioButtonChecked
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.SupportAgent
import androidx.compose.material.icons.filled.Task
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Work
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TimePicker
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberTimePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.data.ReportRecord
import com.example.canaldedenunciasgsi.data.ReportRepository
import com.example.canaldedenunciasgsi.data.ReportStatus
import com.example.canaldedenunciasgsi.data.ReportUpdate
import com.example.canaldedenunciasgsi.data.SucursalesCatalog
import com.example.canaldedenunciasgsi.data.remote.ApiFailureKind
import com.example.canaldedenunciasgsi.data.remote.ApiRepository
import com.example.canaldedenunciasgsi.data.remote.ApiResult
import com.example.canaldedenunciasgsi.data.remote.ComplaintCatalog
import com.example.canaldedenunciasgsi.ui.components.pressScale
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto
import com.example.canaldedenunciasgsi.ui.theme.GsiNegro
import com.example.canaldedenunciasgsi.ui.theme.GsiRojo
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Índices de las opciones que activan campos condicionales. */
private const val RELATION_COLLABORATOR = 0
private const val MODE_IDENTIFIED = 1
private const val ANSWER_YES = 0
private const val RECURRENCE_REPEATED = 1

/** Longitud máxima permitida para el teléfono. */
private const val PHONE_MAX_LENGTH = 10

/** Adjuntos máximos aceptados por el servidor. */
private const val SUBMIT_MAX_ATTACHMENTS = 5

/**
 * Cuestionario de reporte. Incluye los datos de la persona (solo cuando el
 * reporte se envía con datos), los datos de la denuncia, la descripción con
 * evidencia y las preguntas adicionales opcionales.
 */
@Composable
fun ReportForm(
    onExit: () -> Unit,
    onSubmitted: (String) -> Unit,
    privacyOpened: String,
    modifier: Modifier = Modifier
) {
    // Preguntas iniciales.
    var action by rememberSaveable { mutableStateOf<Int?>(null) }
    var relation by rememberSaveable { mutableStateOf<Int?>(null) }
    var mode by rememberSaveable { mutableStateOf<Int?>(null) }
    var password by rememberSaveable { mutableStateOf("") }
    var confirmation by rememberSaveable { mutableStateOf("") }

    // Datos de contacto.
    var fullName by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }
    var phone by rememberSaveable { mutableStateOf("") }
    var employeeNumber by rememberSaveable { mutableStateOf("") }
    var position by rememberSaveable { mutableStateOf("") }

    // Datos de la denuncia.
    var category by rememberSaveable { mutableStateOf<Int?>(null) }
    var reason by rememberSaveable { mutableStateOf<Int?>(null) }
    var state by rememberSaveable { mutableStateOf("") }
    var branch by rememberSaveable { mutableStateOf("") }
    var dateMillis by rememberSaveable { mutableStateOf<Long?>(null) }
    var timeHour by rememberSaveable { mutableStateOf<Int?>(null) }
    var timeMinute by rememberSaveable { mutableStateOf<Int?>(null) }
    var knowsActor by rememberSaveable { mutableStateOf<Int?>(null) }
    var actorName by rememberSaveable { mutableStateOf("") }
    var actorEmployee by rememberSaveable { mutableStateOf("") }
    var actorArea by rememberSaveable { mutableStateOf("") }
    var participation by rememberSaveable { mutableStateOf<Int?>(null) }
    var hasWitnesses by rememberSaveable { mutableStateOf<Int?>(null) }
    var witnessesCount by rememberSaveable { mutableStateOf("") }

    // Descripción y evidencia. La evidencia se guarda como URI (string) para
    // poder enviar el archivo real al servidor en la petición multipart.
    var description by rememberSaveable { mutableStateOf("") }
    var evidence by rememberSaveable { mutableStateOf<List<String>>(emptyList()) }

    // Preguntas adicionales.
    var answerExtraQuestions by rememberSaveable { mutableStateOf(1) }
    var recurrence by rememberSaveable { mutableStateOf<Int?>(null) }
    var frequency by rememberSaveable { mutableStateOf("") }
    var hasImmediateRisk by rememberSaveable { mutableStateOf<Int?>(null) }
    var reportedBefore by rememberSaveable { mutableStateOf<Int?>(null) }
    var reportMedium by rememberSaveable { mutableStateOf("") }
    var contactPreference by rememberSaveable { mutableStateOf<Int?>(null) }
    var impactNotes by rememberSaveable { mutableStateOf("") }

    var showValidation by rememberSaveable { mutableStateOf(false) }
    var validationErrors by remember { mutableStateOf<List<Int>>(emptyList()) }
    var isSubmitting by rememberSaveable { mutableStateOf(false) }
    var submitErrorKind by remember { mutableStateOf<ApiFailureKind?>(null) }

    val context = LocalContext.current
    val resources = context.resources
    val scope = rememberCoroutineScope()
    val withPersonalData = mode == MODE_IDENTIFIED

    // Estados y sucursales tomados del mismo JSON que usa el formulario web.
    val sucursales = remember { SucursalesCatalog.load(context) }

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            val value = uri.toString()
            if (value !in evidence && evidence.size < SUBMIT_MAX_ATTACHMENTS) {
                evidence = evidence + value
            }
        }
    }

    // Campos obligatorios pendientes. Se evalúan únicamente al intentar enviar,
    // de modo que escribir en el formulario no provoque recomposiciones de toda la lista.
    fun pendingFields(): List<Int> = buildList {
        val identified = mode == MODE_IDENTIFIED
        val passwordsMatch = password == confirmation
        if (action == null) add(R.string.report_field_action)
        if (relation == null) add(R.string.report_field_relation)
        if (mode == null) add(R.string.report_field_mode)
        if (identified) {
            if (fullName.isBlank()) add(R.string.report_personal_name)
            if (email.isBlank()) add(R.string.report_personal_email)
            if (phone.isBlank()) add(R.string.report_personal_phone)
            if (relation == RELATION_COLLABORATOR && employeeNumber.isBlank()) {
                add(R.string.report_personal_employee)
            }
            if (position.isBlank()) add(R.string.report_personal_position)
        }
        if (password.isBlank()) add(R.string.report_field_password)
        if (confirmation.isBlank()) add(R.string.report_field_password_confirm)
        if (password.isNotBlank() && confirmation.isNotBlank() && !passwordsMatch) {
            add(R.string.report_password_mismatch)
        }
        if (category == null) {
            add(R.string.report_field_category)
        } else if (reason == null) {
            add(R.string.report_field_reason)
        }
        if (state.isBlank()) add(R.string.report_field_state)
        if (branch.isBlank()) add(R.string.report_field_branch)
        if (dateMillis == null) add(R.string.report_field_date)
        if (timeHour == null) add(R.string.report_field_time)
        if (knowsActor == null) add(R.string.report_field_actor)
        if (participation == null) add(R.string.report_field_participation)
        if (hasWitnesses == null) add(R.string.report_field_witnesses)
        if (hasWitnesses == ANSWER_YES && witnessesCount.isBlank()) {
            add(R.string.report_witnesses_count)
        }
        if (description.isBlank()) add(R.string.report_field_description)
    }

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        item(key = "lead", contentType = "header") {
            AnimatedFormItem { ReportLeadCard() }
        }

        item(key = "action", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.AutoMirrored.Filled.Assignment,
                    titleRes = R.string.report_step_action_title,
                    options = actionOptions,
                    selectedIndex = action,
                    onSelect = { action = it }
                )
            }
        }

        item(key = "relation", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Groups,
                    titleRes = R.string.report_step_relation_title,
                    options = relationOptions,
                    selectedIndex = relation,
                    onSelect = { relation = it }
                )
            }
        }

        item(key = "mode", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Person,
                    titleRes = R.string.report_step_mode_title,
                    options = modeOptions,
                    selectedIndex = mode,
                    onSelect = { mode = it }
                )
            }
        }

        // Los datos de contacto solo se solicitan cuando el reporte va con datos.
        if (withPersonalData) {
            item(key = "personal", contentType = "block") {
                AnimatedFormItem {
                    PersonalDataBlock(
                        showEmployeeNumber = relation == RELATION_COLLABORATOR,
                        fullName = { fullName },
                        onFullNameChange = { fullName = it },
                        email = { email },
                        onEmailChange = { email = it },
                        phone = { phone },
                        onPhoneChange = { phone = it },
                        employeeNumber = { employeeNumber },
                        onEmployeeNumberChange = { employeeNumber = it },
                        position = { position },
                        onPositionChange = { position = it }
                    )
                }
            }
        }

        item(key = "password", contentType = "block") {
            AnimatedFormItem {
                PasswordBlock(
                    password = password,
                    onPasswordChange = { password = it },
                    confirmation = confirmation,
                    onConfirmationChange = { confirmation = it }
                )
            }
        }

        item(key = "section-report", contentType = "header") {
            AnimatedFormItem {
                FormSectionHeader(
                    icon = Icons.Filled.Policy,
                    titleRes = R.string.report_section_report_title
                )
            }
        }

        item(key = "category", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Category,
                    titleRes = R.string.report_step_category_title,
                    options = reportCategories.map { ReportOption(it.titleRes) },
                    selectedIndex = category,
                    onSelect = {
                        category = it
                        reason = null
                    }
                )
            }
        }

        val currentCategory = category?.let { reportCategories[it] }
        if (currentCategory != null) {
            item(key = "reason", contentType = "question") {
                AnimatedFormItem {
                    // Al cambiar el tipo de denuncia se despliegan los nuevos motivos.
                    key(category) {
                        QuestionBlock(
                            icon = Icons.AutoMirrored.Filled.Rule,
                            titleRes = R.string.report_step_reason_title,
                            options = currentCategory.reasons,
                            selectedIndex = reason,
                            onSelect = { reason = it }
                        )
                    }
                }
            }
        }

        item(key = "section-event", contentType = "header") {
            AnimatedFormItem {
                FormSectionHeader(
                    icon = Icons.AutoMirrored.Filled.FactCheck,
                    titleRes = R.string.report_section_event_title
                )
            }
        }

        item(key = "state", contentType = "field") {
            AnimatedFormItem {
                SelectField(
                    value = state,
                    labelRes = R.string.report_fact_state,
                    icon = Icons.Filled.LocationOn,
                    options = sucursales.keys.toList(),
                    placeholder = stringResource(R.string.report_select_state),
                    onSelect = {
                        state = it
                        // Al cambiar de estado se descarta la sucursal previa.
                        branch = ""
                    }
                )
            }
        }

        item(key = "branch", contentType = "field") {
            AnimatedFormItem {
                SelectField(
                    value = branch,
                    labelRes = R.string.report_fact_branch,
                    icon = Icons.Filled.Business,
                    options = sucursales[state].orEmpty(),
                    placeholder = stringResource(
                        if (state.isBlank()) {
                            R.string.report_select_state_first
                        } else {
                            R.string.report_select_branch
                        }
                    ),
                    enabled = state.isNotBlank(),
                    onSelect = { branch = it }
                )
            }
        }

        item(key = "date", contentType = "field") {
            AnimatedFormItem {
                DateField(
                    dateMillis = dateMillis,
                    onDateChange = { dateMillis = it }
                )
            }
        }

        item(key = "time", contentType = "field") {
            AnimatedFormItem {
                TimeField(
                    hour = timeHour,
                    minute = timeMinute,
                    onTimeChange = { hour, minute ->
                        timeHour = hour
                        timeMinute = minute
                    }
                )
            }
        }

        item(key = "actor", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Person,
                    titleRes = R.string.report_step_actor_title,
                    options = yesNoOptions,
                    selectedIndex = knowsActor,
                    onSelect = { knowsActor = it }
                )
            }
        }

        if (knowsActor == ANSWER_YES) {
            item(key = "actor-name", contentType = "field") {
                AnimatedFormItem {
                    FormTextField(
                        value = { actorName },
                        onValueChange = { actorName = it },
                        labelRes = R.string.report_actor_name,
                        leadingIcon = Icons.Filled.Person
                    )
                }
            }
            item(key = "actor-employee", contentType = "field") {
                AnimatedFormItem {
                    FormTextField(
                        value = { actorEmployee },
                        onValueChange = { input ->
                            actorEmployee = input.filter { it.isDigit() }.take(10)
                        },
                        labelRes = R.string.report_actor_employee,
                        leadingIcon = Icons.Filled.Badge,
                        keyboardType = KeyboardType.Number
                    )
                }
            }
            item(key = "actor-area", contentType = "field") {
                AnimatedFormItem {
                    FormTextField(
                        value = { actorArea },
                        onValueChange = { actorArea = it },
                        labelRes = R.string.report_actor_area,
                        leadingIcon = Icons.Filled.Work
                    )
                }
            }
        }

        item(key = "participation", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Fingerprint,
                    titleRes = R.string.report_step_participation_title,
                    options = participationOptions,
                    selectedIndex = participation,
                    onSelect = { participation = it }
                )
            }
        }

        item(key = "witnesses", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Groups,
                    titleRes = R.string.report_step_witnesses_title,
                    options = yesNoOptions,
                    selectedIndex = hasWitnesses,
                    onSelect = { hasWitnesses = it }
                )
            }
        }

        if (hasWitnesses == ANSWER_YES) {
            item(key = "witnesses-count", contentType = "field") {
                AnimatedFormItem {
                    FormTextField(
                        value = { witnessesCount },
                        onValueChange = { input ->
                            if (input.length <= 3 && input.all { it.isDigit() }) {
                                witnessesCount = input
                            }
                        },
                        labelRes = R.string.report_witnesses_count,
                        leadingIcon = Icons.Filled.Groups,
                        keyboardType = KeyboardType.Number
                    )
                }
            }
        }

        item(key = "description", contentType = "block") {
            AnimatedFormItem {
                DescriptionBlock(
                    description = { description },
                    onDescriptionChange = { description = it }
                )
            }
        }

        item(key = "evidence", contentType = "block") {
            AnimatedFormItem {
                EvidenceBlock(
                    files = evidence,
                    onPick = { filePicker.launch(arrayOf("*/*")) },
                    onRemove = { uri -> evidence = evidence - uri }
                )
            }
        }

        item(key = "section-extra", contentType = "header") {
            AnimatedFormItem {
                FormSectionHeader(
                    icon = Icons.Filled.Quiz,
                    titleRes = R.string.report_section_extra_title
                )
            }
        }

        item(key = "extra-intro", contentType = "text") {
            AnimatedFormItem {
                Text(
                    text = stringResource(R.string.report_extra_intro),
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiGrisTexto
                )
            }
        }

        item(key = "extra-choice", contentType = "question") {
            AnimatedFormItem {
                QuestionBlock(
                    icon = Icons.Filled.Quiz,
                    titleRes = R.string.report_extra_opt_in_title,
                    options = yesNoOptions,
                    selectedIndex = answerExtraQuestions,
                    onSelect = { selected ->
                        answerExtraQuestions = selected
                        if (selected != ANSWER_YES) {
                            recurrence = null
                            frequency = ""
                            hasImmediateRisk = null
                            reportedBefore = null
                            reportMedium = ""
                            contactPreference = null
                            impactNotes = ""
                        }
                    }
                )
            }
        }

        if (answerExtraQuestions == ANSWER_YES) {
            item(key = "extra-recurrence", contentType = "question") {
                AnimatedFormItem {
                    QuestionBlock(
                        icon = Icons.Filled.Refresh,
                        titleRes = R.string.report_extra_recurrence_title,
                        options = recurrenceOptions,
                        selectedIndex = recurrence,
                        onSelect = { recurrence = it }
                    )
                }
            }

            if (recurrence == RECURRENCE_REPEATED) {
                item(key = "extra-frequency", contentType = "field") {
                    AnimatedFormItem {
                        FormTextField(
                            value = { frequency },
                            onValueChange = { frequency = it },
                            labelRes = R.string.report_extra_frequency_label,
                            leadingIcon = Icons.Filled.Refresh,
                            required = false
                        )
                    }
                }
            }

            item(key = "extra-risk", contentType = "question") {
                AnimatedFormItem {
                    QuestionBlock(
                        icon = Icons.Filled.Warning,
                        titleRes = R.string.report_extra_risk_title,
                        options = yesNoOptions,
                        selectedIndex = hasImmediateRisk,
                        onSelect = { hasImmediateRisk = it },
                        required = false
                    )
                }
            }

            item(key = "extra-reported", contentType = "question") {
                AnimatedFormItem {
                    QuestionBlock(
                        icon = Icons.Filled.Task,
                        titleRes = R.string.report_extra_reported_title,
                        options = yesNoOptions,
                        selectedIndex = reportedBefore,
                        onSelect = { reportedBefore = it },
                        required = false
                    )
                }
            }

            if (reportedBefore == ANSWER_YES) {
                item(key = "extra-medium", contentType = "field") {
                    AnimatedFormItem {
                        FormTextField(
                            value = { reportMedium },
                            onValueChange = { reportMedium = it },
                            labelRes = R.string.report_extra_medium_label,
                            leadingIcon = Icons.Filled.Task,
                            required = false
                        )
                    }
                }
            }

            // Solo tiene sentido si el reporte se envía con datos de contacto.
            if (withPersonalData) {
                item(key = "extra-contact", contentType = "question") {
                    AnimatedFormItem {
                        QuestionBlock(
                            icon = Icons.Filled.SupportAgent,
                            titleRes = R.string.report_extra_contact_title,
                            options = contactPreferenceOptions,
                            selectedIndex = contactPreference,
                            onSelect = { contactPreference = it },
                            required = false
                        )
                    }
                }
            }

            item(key = "extra-impact", contentType = "field") {
                AnimatedFormItem {
                    FormTextField(
                        value = { impactNotes },
                        onValueChange = { impactNotes = it },
                        labelRes = R.string.report_extra_impact_label,
                        leadingIcon = Icons.AutoMirrored.Filled.Notes,
                        required = false,
                        singleLine = false,
                        minLines = 3,
                        showLeadingIcon = false
                    )
                }
            }
        }

        item(key = "actions", contentType = "actions") {
            AnimatedFormItem {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Button(
                        onClick = {
                            val missing = pendingFields()
                            if (missing.isNotEmpty()) {
                                validationErrors = missing
                                showValidation = true
                                return@Button
                            }
                            val actionIndex = action ?: 0
                            val categoryIndex = category ?: 0
                            val categoryData = reportCategories[categoryIndex]
                            val reasonIndex = reason ?: 0
                            val reasonValue = ComplaintCatalog.reason(categoryIndex, reasonIndex)
                            val fields = buildMap {
                                put("action_type", ComplaintCatalog.actionType(actionIndex))
                                if (withPersonalData) {
                                    put("name", fullName.trim())
                                    put("email", email.trim())
                                    put("phone", phone.trim())
                                    if (relation == RELATION_COLLABORATOR) {
                                        put("reporter_matricula", employeeNumber.trim())
                                    }
                                }
                                // El servidor guarda el motivo concreto en `category`
                                // (y en `inquietud_category` cuando la acción es inquietud).
                                put("category", reasonValue)
                                put("inquietud_category", reasonValue)
                                put("relationship", ComplaintCatalog.relationship(relation ?: 0))
                                put("description", description.trim())
                                put("password", password)
                                put("terms_accept", "true")
                                put(
                                    "privacy_policies_opened",
                                    privacyOpened.ifBlank { "Aviso de privacidad aceptado" }
                                )
                                put("incident_state", state.trim())
                                put("incident_branch", branch.trim())
                                put("incident_date", isoDate(dateMillis))
                                put("incident_time", isoTime(timeHour, timeMinute))
                                put("knows_actor", ComplaintCatalog.boolean(knowsActor ?: 1))
                                if (knowsActor == ANSWER_YES) {
                                    put("actor_name", actorName.trim())
                                    put("actor_matricula", actorEmployee.trim())
                                    put("actor_area", actorArea.trim())
                                }
                                put("reporter_role", ComplaintCatalog.reporterRole(participation ?: 0))
                                put("has_witnesses", ComplaintCatalog.boolean(hasWitnesses ?: 1))
                                if (hasWitnesses == ANSWER_YES) {
                                    put("witnesses_count", witnessesCount.trim())
                                }
                                if (answerExtraQuestions == ANSWER_YES) {
                                    recurrence?.let {
                                        put("recurrence", ComplaintCatalog.recurrence(it))
                                    }
                                    if (recurrence == RECURRENCE_REPEATED && frequency.isNotBlank()) {
                                        put("recurrence_since", frequency.trim())
                                    }
                                    hasImmediateRisk?.let {
                                        put("immediate_risk", ComplaintCatalog.yesNo(it))
                                    }
                                    reportedBefore?.let {
                                        put("previous_report", ComplaintCatalog.yesNo(it))
                                    }
                                    if (reportedBefore == ANSWER_YES && reportMedium.isNotBlank()) {
                                        put("previous_report_channel", reportMedium.trim())
                                    }
                                    if (withPersonalData) {
                                        contactPreference?.let {
                                            put(
                                                "contact_preference",
                                                ComplaintCatalog.contactPreference(it)
                                            )
                                        }
                                    }
                                    if (impactNotes.isNotBlank()) {
                                        put("impact_notes", impactNotes.trim())
                                    }
                                }
                            }
                            val uris = evidence.map { Uri.parse(it) }
                            isSubmitting = true
                            scope.launch {
                                when (val result = ApiRepository.createComplaint(context, fields, uris)) {
                                    is ApiResult.Success -> {
                                        val submittedAt = formatDate(System.currentTimeMillis())
                                        // Espejo local para el comprobante de envío.
                                        ReportRepository.submit(
                                            context,
                                            ReportRecord(
                                                folio = result.data.folio,
                                                password = password,
                                                createdAt = submittedAt,
                                                actionRes = actionOptions[actionIndex].titleRes,
                                                categoryRes = categoryData.titleRes,
                                                reasonRes = categoryData.reasons[reasonIndex].titleRes,
                                                anonymous = !withPersonalData,
                                                name = fullName.ifBlank { null },
                                                email = email.ifBlank { null },
                                                phone = phone.ifBlank { null },
                                                files = evidence,
                                                status = ReportStatus.RECEIVED,
                                                updates = listOf(
                                                    ReportUpdate(
                                                        date = submittedAt,
                                                        textRes = R.string.track_update_received
                                                    )
                                                )
                                            )
                                        )
                                        isSubmitting = false
                                        onSubmitted(result.data.folio)
                                    }

                                    is ApiResult.Failure -> {
                                        isSubmitting = false
                                        submitErrorKind = result.kind
                                    }
                                }
                            }
                        },
                        enabled = !isSubmitting,
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = GsiAzul285,
                            contentColor = Color.White
                        )
                    ) {
                        if (isSubmitting) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                color = Color.White,
                                strokeWidth = 2.dp
                            )
                        } else {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.Send,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                        Text(
                            text = stringResource(
                                if (isSubmitting) R.string.report_submitting else R.string.report_submit
                            ),
                            style = MaterialTheme.typography.labelLarge,
                            modifier = Modifier.padding(start = 8.dp)
                        )
                    }
                    OutlinedButton(
                        onClick = onExit,
                        modifier = Modifier.fillMaxWidth(),
                        border = BorderStroke(1.dp, GsiAzul285),
                        colors = ButtonDefaults.outlinedButtonColors(
                            contentColor = GsiAzul285
                        )
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Home,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Text(
                            text = stringResource(R.string.report_back_home),
                            style = MaterialTheme.typography.labelLarge,
                            modifier = Modifier.padding(start = 8.dp)
                        )
                    }
                }
            }
        }
    }

    if (showValidation) {
        AlertDialog(
            onDismissRequest = { showValidation = false },
            icon = {
                Icon(
                    imageVector = Icons.Filled.ErrorOutline,
                    contentDescription = null,
                    tint = GsiRojo
                )
            },
            title = {
                Text(
                    text = stringResource(R.string.report_validation_title),
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654
                )
            },
            text = {
                Column(
                    modifier = Modifier
                        .heightIn(max = 320.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = stringResource(R.string.report_validation_body),
                        style = MaterialTheme.typography.bodyMedium,
                        color = GsiNegro
                    )
                    validationErrors.forEach { fieldRes ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(6.dp)
                                    .background(GsiRojo, CircleShape)
                            )
                            Text(
                                text = resources.getString(fieldRes),
                                style = MaterialTheme.typography.bodyMedium,
                                color = GsiGrisTexto,
                                modifier = Modifier.padding(start = 10.dp)
                            )
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showValidation = false }) {
                    Text(
                        text = stringResource(R.string.report_pending_ok),
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        )
    }

    // Error al enviar el reporte al servidor.
    submitErrorKind?.let { kind ->
        AlertDialog(
            onDismissRequest = { submitErrorKind = null },
            icon = {
                Icon(
                    imageVector = Icons.Filled.ErrorOutline,
                    contentDescription = null,
                    tint = GsiRojo
                )
            },
            title = {
                Text(
                    text = stringResource(R.string.report_submit_error_title),
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654
                )
            },
            text = {
                Text(
                    text = stringResource(
                        when (kind) {
                            ApiFailureKind.NETWORK -> R.string.report_submit_error_network
                            ApiFailureKind.SERVER -> R.string.report_submit_error_server
                            else -> R.string.report_submit_error_body
                        }
                    ),
                    style = MaterialTheme.typography.bodyMedium,
                    color = GsiNegro
                )
            },
            confirmButton = {
                TextButton(onClick = { submitErrorKind = null }) {
                    Text(
                        text = stringResource(R.string.report_pending_ok),
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        )
    }
}

/**
 * Envuelve el contenido de un elemento de la lista para animar con suavidad su
 * aparición y desaparición cuando una respuesta despliega nuevos campos.
 */
@Composable
private fun LazyItemScope.AnimatedFormItem(content: @Composable () -> Unit) {
    Box(modifier = Modifier.animateItem()) { content() }
}

/** Encabezado del cuestionario. */
@Composable
private fun ReportLeadCard(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(GsiAzulClaro, RoundedCornerShape(16.dp))
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Text(
            text = stringResource(R.string.report_form_lead_title),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = GsiAzul654
        )
        Text(
            text = stringResource(R.string.report_form_lead_body),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
    }
}

/** Título de una sección del formulario. */
@Composable
private fun FormSectionHeader(
    icon: ImageVector,
    @StringRes titleRes: Int,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .background(GsiAzul654, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.size(22.dp)
            )
        }
        Text(
            text = stringResource(titleRes),
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            color = GsiAzul654,
            modifier = Modifier.padding(start = 12.dp)
        )
    }
}

/**
 * Pregunta del cuestionario. Al elegir una opción las demás se pliegan y solo
 * se muestra la respuesta elegida; al tocar la pregunta se despliegan de nuevo.
 */
@Composable
private fun QuestionBlock(
    icon: ImageVector,
    @StringRes titleRes: Int,
    options: List<ReportOption>,
    selectedIndex: Int?,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
    required: Boolean = true
) {
    var expanded by rememberSaveable { mutableStateOf(true) }
    val interactionSource = remember { MutableInteractionSource() }
    val chevronRotation by animateFloatAsState(
        targetValue = if (expanded) 180f else 0f,
        label = "questionChevron"
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable(
                    interactionSource = interactionSource,
                    indication = null
                ) { expanded = !expanded }
                .pressScale(interactionSource),
            verticalAlignment = Alignment.CenterVertically
        ) {
            QuestionHeader(
                icon = icon,
                title = stringResource(titleRes),
                required = required,
                modifier = Modifier.weight(1f)
            )
            Icon(
                imageVector = Icons.Filled.KeyboardArrowDown,
                contentDescription = null,
                tint = GsiAzul285,
                modifier = Modifier.rotate(chevronRotation)
            )
        }

        AnimatedVisibility(
            visible = expanded,
            // Se usan tiempos explícitos y cortos para que el despliegue coincida
            // con la animación de altura de la lista y no se perciban tirones.
            enter = expandVertically(animationSpec = tween(durationMillis = 240)) +
                fadeIn(animationSpec = tween(durationMillis = 200)),
            exit = shrinkVertically(animationSpec = tween(durationMillis = 180)) +
                fadeOut(animationSpec = tween(durationMillis = 120))
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                options.forEachIndexed { index, option ->
                    SelectableOptionCard(
                        option = option,
                        selected = selectedIndex == index,
                        onClick = {
                            onSelect(index)
                            expanded = false
                        }
                    )
                }
            }
        }

        if (!expanded && selectedIndex != null) {
            SelectableOptionCard(
                option = options[selectedIndex],
                selected = true,
                onClick = { expanded = true }
            )
        }
    }
}

/** Título de una pregunta, con su icono y la marca de obligatorio. */
@Composable
private fun QuestionHeader(
    icon: ImageVector,
    title: String,
    modifier: Modifier = Modifier,
    required: Boolean = false
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .background(GsiAzulClaro, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = GsiAzul654,
                modifier = Modifier.size(20.dp)
            )
        }
        Text(
            text = buildAnnotatedString {
                append(title)
                if (required) {
                    withStyle(SpanStyle(color = GsiRojo)) { append(" *") }
                }
            },
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = GsiAzul654,
            modifier = Modifier.padding(start = 12.dp)
        )
    }
}

/** Opción de respuesta seleccionable. */
@Composable
private fun SelectableOptionCard(
    option: ReportOption,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val interactionSource = remember { MutableInteractionSource() }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                onClick = onClick
            )
            .pressScale(interactionSource),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) GsiAzulClaro else Color.White
        ),
        border = BorderStroke(
            width = if (selected) 2.dp else 1.dp,
            color = if (selected) GsiAzul285 else GsiGrisBorde
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = if (selected) {
                    Icons.Filled.RadioButtonChecked
                } else {
                    Icons.Filled.RadioButtonUnchecked
                },
                contentDescription = null,
                tint = if (selected) GsiAzul285 else GsiGrisBorde
            )
            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(start = 12.dp),
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Text(
                    text = stringResource(option.titleRes),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = if (selected) GsiAzul654 else GsiNegro
                )
                option.bodyRes?.let { bodyRes ->
                    Text(
                        text = stringResource(bodyRes),
                        style = MaterialTheme.typography.bodySmall,
                        color = GsiGrisTexto
                    )
                }
            }
        }
    }
}

/** Campos del reporte enviado con datos de la persona. */
@Composable
private fun PersonalDataBlock(
    showEmployeeNumber: Boolean,
    fullName: () -> String,
    onFullNameChange: (String) -> Unit,
    email: () -> String,
    onEmailChange: (String) -> Unit,
    phone: () -> String,
    onPhoneChange: (String) -> Unit,
    employeeNumber: () -> String,
    onEmployeeNumberChange: (String) -> Unit,
    position: () -> String,
    onPositionChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        FormSectionHeader(
            icon = Icons.Filled.Badge,
            titleRes = R.string.report_personal_title
        )
        Text(
            text = stringResource(R.string.report_personal_intro),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
        FormTextField(
            value = fullName,
            onValueChange = onFullNameChange,
            labelRes = R.string.report_personal_name,
            leadingIcon = Icons.Filled.Person
        )
        FormTextField(
            value = email,
            onValueChange = onEmailChange,
            labelRes = R.string.report_personal_email,
            leadingIcon = Icons.Filled.Email,
            keyboardType = KeyboardType.Email
        )
        FormTextField(
            value = phone,
            onValueChange = { input ->
                if (input.length <= PHONE_MAX_LENGTH &&
                    input.all { it.isDigit() }
                ) {
                    onPhoneChange(input)
                }
            },
            labelRes = R.string.report_personal_phone,
            leadingIcon = Icons.Filled.Phone,
            keyboardType = KeyboardType.Number
        )
        if (showEmployeeNumber) {
            FormTextField(
                value = employeeNumber,
                onValueChange = { input ->
                    onEmployeeNumberChange(input.filter { it.isDigit() }.take(10))
                },
                labelRes = R.string.report_personal_employee,
                leadingIcon = Icons.Filled.Badge,
                keyboardType = KeyboardType.Number
            )
        }
        FormTextField(
            value = position,
            onValueChange = onPositionChange,
            labelRes = R.string.report_personal_position,
            leadingIcon = Icons.Filled.Work
        )
    }
}

/** Etiqueta de un campo, con asterisco cuando es obligatorio. */
@Composable
private fun FieldLabel(
    @StringRes textRes: Int,
    required: Boolean
) {
    Text(
        text = buildAnnotatedString {
            append(stringResource(textRes))
            if (required) {
                withStyle(SpanStyle(color = GsiRojo)) { append(" *") }
            }
        }
    )
}

/**
 * Campo de texto del formulario.
 *
 * El valor llega como función (`() -> String`) en lugar de como texto ya
 * resuelto. Con esto la lectura del estado ocurre dentro de este componente: al
 * escribir en un campo solo se recompone ese campo y no todo el bloque o la
 * lista, lo que mantiene fluido el cuestionario.
 */
@Composable
private fun FormTextField(
    value: () -> String,
    onValueChange: (String) -> Unit,
    @StringRes labelRes: Int,
    leadingIcon: ImageVector,
    modifier: Modifier = Modifier,
    required: Boolean = true,
    keyboardType: KeyboardType = KeyboardType.Text,
    singleLine: Boolean = true,
    minLines: Int = 1,
    showLeadingIcon: Boolean = true
) {
    OutlinedTextField(
        value = value(),
        onValueChange = onValueChange,
        modifier = modifier.fillMaxWidth(),
        label = { FieldLabel(textRes = labelRes, required = required) },
        singleLine = singleLine,
        minLines = minLines,
        leadingIcon = if (showLeadingIcon) {
            {
                Icon(
                    imageVector = leadingIcon,
                    contentDescription = null,
                    tint = GsiAzul654
                )
            }
        } else {
            null
        },
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType)
    )
}

/** Campo de fecha: solo lectura, abre el selector al tocarlo. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DateField(
    dateMillis: Long?,
    onDateChange: (Long) -> Unit,
    modifier: Modifier = Modifier
) {
    var showPicker by rememberSaveable { mutableStateOf(false) }
    val formatted = dateMillis?.let { formatDate(it) }.orEmpty()

    PickerField(
        value = formatted,
        labelRes = R.string.report_fact_date,
        icon = Icons.AutoMirrored.Filled.EventNote,
        onClick = { showPicker = true },
        modifier = modifier
    )

    if (showPicker) {
        val datePickerState = rememberDatePickerState(initialSelectedDateMillis = dateMillis)
        DatePickerDialog(
            onDismissRequest = { showPicker = false },
            confirmButton = {
                TextButton(
                    onClick = {
                        datePickerState.selectedDateMillis?.let(onDateChange)
                        showPicker = false
                    }
                ) {
                    Text(
                        text = stringResource(R.string.report_accept),
                        fontWeight = FontWeight.SemiBold
                    )
                }
            },
            dismissButton = {
                TextButton(onClick = { showPicker = false }) {
                    Text(text = stringResource(R.string.report_cancel))
                }
            }
        ) {
            DatePicker(state = datePickerState)
        }
    }
}

/** Campo de hora: solo lectura, abre el selector al tocarlo. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TimeField(
    hour: Int?,
    minute: Int?,
    onTimeChange: (Int, Int) -> Unit,
    modifier: Modifier = Modifier
) {
    var showPicker by rememberSaveable { mutableStateOf(false) }
    val formatted = if (hour != null && minute != null) formatTime(hour, minute) else ""

    PickerField(
        value = formatted,
        labelRes = R.string.report_fact_time,
        icon = Icons.Filled.Schedule,
        onClick = { showPicker = true },
        modifier = modifier
    )

    if (showPicker) {
        val timePickerState = rememberTimePickerState(
            initialHour = hour ?: 0,
            initialMinute = minute ?: 0,
            is24Hour = true
        )
        AlertDialog(
            onDismissRequest = { showPicker = false },
            title = {
                Text(
                    text = stringResource(R.string.report_fact_time),
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654
                )
            },
            text = { TimePicker(state = timePickerState) },
            confirmButton = {
                TextButton(
                    onClick = {
                        onTimeChange(timePickerState.hour, timePickerState.minute)
                        showPicker = false
                    }
                ) {
                    Text(
                        text = stringResource(R.string.report_accept),
                        fontWeight = FontWeight.SemiBold
                    )
                }
            },
            dismissButton = {
                TextButton(onClick = { showPicker = false }) {
                    Text(text = stringResource(R.string.report_cancel))
                }
            }
        )
    }
}

/** Campo de solo lectura que abre un selector al tocarlo. */
@Composable
private fun PickerField(
    value: String,
    @StringRes labelRes: Int,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Box(modifier = modifier.fillMaxWidth()) {
        OutlinedTextField(
            value = value,
            onValueChange = { },
            modifier = Modifier.fillMaxWidth(),
            readOnly = true,
            enabled = enabled,
            singleLine = true,
            label = { FieldLabel(textRes = labelRes, required = true) },
            leadingIcon = {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = GsiAzul654
                )
            }
        )
        Box(
            modifier = Modifier
                .matchParentSize()
                .clickable(enabled = enabled, onClick = onClick)
        )
    }
}

/**
 * Campo de selección: muestra el valor elegido y abre un diálogo con la lista
 * de opciones. Se usa para estado y sucursal, cuyas opciones vienen del
 * catálogo compartido con el formulario web.
 */
@Composable
private fun SelectField(
    value: String,
    @StringRes labelRes: Int,
    icon: ImageVector,
    options: List<String>,
    placeholder: String,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    var expanded by rememberSaveable { mutableStateOf(false) }

    PickerField(
        value = value.ifBlank { placeholder },
        labelRes = labelRes,
        icon = icon,
        enabled = enabled,
        onClick = { if (enabled) expanded = true },
        modifier = modifier
    )

    if (expanded) {
        AlertDialog(
            onDismissRequest = { expanded = false },
            title = {
                Text(
                    text = stringResource(labelRes),
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul654
                )
            },
            text = {
                LazyColumn(modifier = Modifier.heightIn(max = 360.dp)) {
                    items(options, key = { it }) { option ->
                        val selected = option == value
                        Text(
                            text = option,
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    onSelect(option)
                                    expanded = false
                                }
                                .padding(vertical = 14.dp, horizontal = 4.dp),
                            style = MaterialTheme.typography.bodyLarge,
                            color = if (selected) GsiAzul285 else GsiNegro,
                            fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Normal
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { expanded = false }) {
                    Text(text = stringResource(R.string.report_cancel))
                }
            }
        )
    }
}

/** Descripción de los hechos. */
@Composable
private fun DescriptionBlock(
    description: () -> String,
    onDescriptionChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        QuestionHeader(
            icon = Icons.Filled.EditNote,
            title = stringResource(R.string.report_step_description_title),
            required = true
        )
        Text(
            text = stringResource(R.string.report_description_body),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
        FormTextField(
            value = description,
            onValueChange = onDescriptionChange,
            labelRes = R.string.report_description_label,
            leadingIcon = Icons.Filled.EditNote,
            singleLine = false,
            minLines = 5,
            showLeadingIcon = false
        )
    }
}

/** Evidencia adjunta al reporte. Los elementos son URIs en formato texto. */
@Composable
private fun EvidenceBlock(
    files: List<String>,
    onPick: () -> Unit,
    onRemove: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        QuestionHeader(
            icon = Icons.Filled.AttachFile,
            title = stringResource(R.string.report_step_evidence_title)
        )
        Text(
            text = stringResource(R.string.report_evidence_body),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
        OutlinedButton(
            onClick = onPick,
            modifier = Modifier.fillMaxWidth(),
            border = BorderStroke(1.dp, GsiAzul285),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = GsiAzul285)
        ) {
            Icon(
                imageVector = Icons.Filled.AttachFile,
                contentDescription = null,
                modifier = Modifier.size(18.dp)
            )
            Text(
                text = stringResource(R.string.report_evidence_add),
                style = MaterialTheme.typography.labelLarge,
                modifier = Modifier.padding(start = 8.dp)
            )
        }
        files.forEach { uriString ->
            val name = ApiRepository.attachmentDisplayName(context, Uri.parse(uriString))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(GsiGrisClaro, RoundedCornerShape(12.dp))
                    .padding(start = 12.dp, end = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Filled.Description,
                    contentDescription = null,
                    tint = GsiAzul654,
                    modifier = Modifier.size(18.dp)
                )
                Text(
                    text = name,
                    style = MaterialTheme.typography.bodySmall,
                    color = GsiNegro,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier
                        .weight(1f)
                        .padding(horizontal = 10.dp)
                )
                IconButton(onClick = { onRemove(uriString) }) {
                    Icon(
                        imageVector = Icons.Filled.Clear,
                        contentDescription = stringResource(R.string.report_evidence_remove),
                        tint = GsiGrisTexto
                    )
                }
            }
        }
    }
}

/** Contraseña de consulta y su confirmación. */
@Composable
private fun PasswordBlock(
    password: String,
    onPasswordChange: (String) -> Unit,
    confirmation: String,
    onConfirmationChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var visible by rememberSaveable { mutableStateOf(false) }
    val passwordsMatch = password == confirmation

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        QuestionHeader(
            icon = Icons.Filled.Key,
            title = stringResource(R.string.report_step_password_title),
            required = true
        )
        Text(
            text = stringResource(R.string.report_password_helper),
            style = MaterialTheme.typography.bodySmall,
            color = GsiGrisTexto
        )
        OutlinedTextField(
            value = password,
            onValueChange = onPasswordChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text(text = stringResource(R.string.report_password_label)) },
            singleLine = true,
            leadingIcon = {
                Icon(
                    imageVector = Icons.Filled.Lock,
                    contentDescription = null,
                    tint = GsiAzul654
                )
            },
            trailingIcon = {
                IconButton(onClick = { visible = !visible }) {
                    Icon(
                        imageVector = if (visible) {
                            Icons.Filled.VisibilityOff
                        } else {
                            Icons.Filled.Visibility
                        },
                        contentDescription = stringResource(
                            if (visible) R.string.report_password_hide else R.string.report_password_show
                        ),
                        tint = GsiGrisTexto
                    )
                }
            },
            visualTransformation = if (visible) {
                VisualTransformation.None
            } else {
                PasswordVisualTransformation()
            },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password)
        )
        OutlinedTextField(
            value = confirmation,
            onValueChange = onConfirmationChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text(text = stringResource(R.string.report_password_confirm_label)) },
            singleLine = true,
            isError = confirmation.isNotEmpty() && !passwordsMatch,
            leadingIcon = {
                Icon(
                    imageVector = Icons.Filled.Lock,
                    contentDescription = null,
                    tint = GsiAzul654
                )
            },
            visualTransformation = if (visible) {
                VisualTransformation.None
            } else {
                PasswordVisualTransformation()
            },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password)
        )
        if (confirmation.isNotEmpty() && !passwordsMatch) {
            Text(
                text = stringResource(R.string.report_password_mismatch),
                style = MaterialTheme.typography.bodySmall,
                color = GsiRojo
            )
        }
    }
}

/** Da formato de fecha a los milisegundos seleccionados. */
private fun formatDate(millis: Long): String =
    SimpleDateFormat("dd/MM/yyyy", Locale.getDefault()).format(Date(millis))

/** Da formato de hora (24 h) a la hora seleccionada. */
private fun formatTime(hour: Int, minute: Int): String =
    String.format(Locale.getDefault(), "%02d:%02d", hour, minute)

/** Fecha en formato ISO (aaaa-mm-dd) para el servidor, o cadena vacía. */
private fun isoDate(millis: Long?): String =
    millis?.let { SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date(it)) }.orEmpty()

/** Hora en formato ISO (hh:mm) para el servidor, o cadena vacía. */
private fun isoTime(hour: Int?, minute: Int?): String =
    if (hour != null) String.format(Locale.US, "%02d:%02d", hour, minute ?: 0) else ""
