from datetime import timedelta

from django.utils import timezone

from ..models import InvestigationPlan, InvestigationProcedure

PROTOCOL_LIBRARY = {
    'acoso': {
        'label': 'Acoso, hostigamiento y discriminación',
        'objective': 'Investigar de forma imparcial, confidencial y con perspectiva de género los hechos denunciados, protegiendo a la persona afectada y evitando la revictimización.',
        'scope': 'Conductas de acoso sexual, acoso u hostigamiento laboral y discriminación ocurridas entre personal de la organización o relacionado con ella.',
        'activities': 'Adoptar medidas de protección inmediata; recabar testimoniales en condiciones de seguridad; resguardar la confidencialidad; documentar las medidas de apoyo psicológico y verificar la ausencia de represalias.',
        'steps': [
            {'key': 'medida_proteccion', 'title': 'Medida de protección inmediata',
             'desc': 'Separar preventivamente a la presunta víctima del presunto agresor (reubicación, cambio de turno o suspensión preventiva) sin afectar sus condiciones laborales.',
             'ref': 'ISO 37301 · 8.1 Control operacional'},
            {'key': 'enfoque_genero', 'title': 'Investigación con perspectiva de género',
             'desc': 'Aplicar el protocolo con perspectiva de género, garantizando trato digno y debido proceso a la persona afectada.',
             'ref': 'ISO 37301 · 5.1 Liderazgo / 8.1'},
            {'key': 'confidencialidad', 'title': 'Confidencialidad reforzada',
             'desc': 'Restringir el acceso a la información y proteger la identidad de la persona denunciante y de las personas testigas.',
             'ref': 'ISO 37301 · 7.5 Información documentada'},
            {'key': 'apoyo_psicologico', 'title': 'Apoyo psicológico y acompañamiento',
             'desc': 'Ofrecer acompañamiento psicológico y asesoría a la persona afectada, documentando las medidas de apoyo otorgadas.',
             'ref': 'ISO 37301 · 7.2 Competencia / 8.1'},
            {'key': 'verificacion_no_represalia', 'title': 'Verificación de no represalia',
             'desc': 'Vigilar y documentar que no existan actos de represalia contra la persona denunciante o las personas testigas.',
             'ref': 'ISO 37301 · 5.1 / 10.1 Mejora'},
        ],
    },
    'fraude': {
        'label': 'Fraude, corrupción y lavado de dinero',
        'objective': 'Determinar la existencia y el alcance del acto fraudulento o de corrupción, cuantificar el daño y preservar la evidencia con fines de sanción y, en su caso, denuncia.',
        'scope': 'Operaciones financieras, contrataciones, pagos, activos y conductas de soborno o blanqueo presuntamente irregulares.',
        'activities': 'Asegurar registros contables y evidencia financiera; congelar accesos; dar intervención a auditoría; cuantificar el daño; evaluar el deber de denuncia ante autoridades.',
        'steps': [
            {'key': 'evidencia_financiera', 'title': 'Aseguramiento de evidencia financiera',
             'desc': 'Asegurar registros contables, movimientos bancarios, facturación y controles internos relacionados con los hechos.',
             'ref': 'ISO 37301 · 8.1 / 7.5'},
            {'key': 'congelamiento_accesos', 'title': 'Congelamiento de accesos y permisos',
             'desc': 'Suspender preventivamente los accesos a sistemas, firmas y cuentas vinculadas al presunto responsable.',
             'ref': 'ISO 37301 · 8.1 Control operacional'},
            {'key': 'intervencion_auditoria', 'title': 'Notificación a auditoría y áreas financieras',
             'desc': 'Informar a auditoría interna, contraloría y áreas financieras para la cuantificación del daño.',
             'ref': 'ISO 37301 · 5.3 / 8.4'},
            {'key': 'cuantificacion_dano', 'title': 'Cuantificación del daño patrimonial',
             'desc': 'Determinar el monto y alcance del perjuicio económico y su impacto en los estados financieros.',
             'ref': 'ISO 37301 · 9.1 Seguimiento y evaluación'},
            {'key': 'deber_denuncia', 'title': 'Análisis del deber de denuncia ante autoridades',
             'desc': 'Evaluar y, en su caso, presentar la denuncia ante las autoridades competentes (fiscalía / unidad de inteligencia financiera).',
             'ref': 'ISO 37301 · 4.5 Requisitos legales'},
        ],
    },
    'datos': {
        'label': 'Protección de datos y seguridad de la información',
        'objective': 'Contener el incidente, determinar el alcance de la afectación a datos personales y cumplir con las obligaciones de notificación aplicables.',
        'scope': 'Tratamiento, acceso, divulgación o pérdida no autorizada de datos personales y vulneraciones a la seguridad de la información.',
        'activities': 'Contener técnicamente la brecha; analizar su alcance; evaluar el riesgo para los titulares; notificar a la autoridad y comunicar a las personas afectadas cuando proceda.',
        'steps': [
            {'key': 'contencion_tecnica', 'title': 'Contención técnica de la brecha',
             'desc': 'Aislar sistemas afectados, revocar credenciales y detener la fuga o exposición de datos personales.',
             'ref': 'ISO 37301 · 8.1 / Seguridad de la información'},
            {'key': 'analisis_brecha', 'title': 'Análisis del alcance de la brecha',
             'desc': 'Determinar qué datos personales, titulares y tratamientos se vieron comprometidos.',
             'ref': 'ISO 37301 · 7.5 / 9.1'},
            {'key': 'riesgo_titulares', 'title': 'Evaluación del riesgo para los titulares',
             'desc': 'Valorar el nivel de riesgo y las medidas para mitigar el impacto en las personas titulares de los datos.',
             'ref': 'ISO 37301 · 6.1 Enfoque basado en riesgos'},
            {'key': 'notificacion_autoridad', 'title': 'Notificación a la autoridad de protección de datos',
             'desc': 'Cumplir los plazos y el procedimiento de notificación a la autoridad de protección de datos.',
             'ref': 'ISO 37301 · 4.5 Requisitos legales'},
            {'key': 'comunicacion_titulares', 'title': 'Comunicación a las personas titulares afectadas',
             'desc': 'Informar a las personas titulares afectadas cuando exista un riesgo alto, con lenguaje claro y accesible.',
             'ref': 'ISO 37301 · 8.4 Comunicación'},
        ],
    },
    'sst': {
        'label': 'Seguridad y salud laboral',
        'objective': 'Eliminar o controlar el riesgo laboral, atender a las personas afectadas y dar cumplimiento a las obligaciones en materia de seguridad y salud.',
        'scope': 'Incumplimientos graves en materia de seguridad y salud laboral y condiciones de riesgo para el personal.',
        'activities': 'Evaluar el riesgo laboral; aplicar medidas inmediatas de control; dar intervención a la comisión de seguridad e higiene; atender a las personas afectadas; cumplir obligaciones ante la autoridad laboral.',
        'steps': [
            {'key': 'evaluacion_riesgo_laboral', 'title': 'Evaluación del riesgo laboral',
             'desc': 'Evaluar las condiciones de seguridad y salud, el riesgo inminente y su afectación al personal.',
             'ref': 'ISO 37301 · 6.1 / 8.1'},
            {'key': 'medidas_inmediatas', 'title': 'Medidas de intervención inmediata',
             'desc': 'Aplicar medidas para eliminar o controlar el riesgo (paro de actividad, señalización, equipo de protección).',
             'ref': 'ISO 37301 · 8.1 Control operacional'},
            {'key': 'comision_ss', 'title': 'Intervención de la comisión de seguridad e higiene',
             'desc': 'Dar intervención a la comisión de seguridad y salud para investigar y dar seguimiento al caso.',
             'ref': 'ISO 37301 · 5.3 Roles y responsabilidades'},
            {'key': 'atencion_medica', 'title': 'Atención médica y registro de lesiones',
             'desc': 'Garantizar atención médica y documentar lesiones y su seguimiento.',
             'ref': 'ISO 37301 · 8.1'},
            {'key': 'obligaciones_laborales', 'title': 'Cumplimiento ante la autoridad laboral',
             'desc': 'Evaluar avisos y trámites ante la autoridad laboral conforme a la normativa aplicable.',
             'ref': 'ISO 37301 · 4.5 Requisitos legales'},
        ],
    },
    'etica': {
        'label': 'Ética, conflictos de interés y política interna',
        'objective': 'Determinar el incumplimiento al Código de Ética o a la política interna y restablecer la integridad de las decisiones.',
        'scope': 'Conflictos de interés, violaciones al Código de Ética y a la política interna de la organización.',
        'activities': 'Documentar y analizar el conflicto; asegurar la abstención de los involucrados; identificar la norma interna incumplida; definir acciones de reforzamiento.',
        'steps': [
            {'key': 'analisis_conflicto', 'title': 'Análisis de conflicto de interés',
             'desc': 'Documentar el conflicto de interés y su impacto en la imparcialidad de las decisiones.',
             'ref': 'ISO 37301 · 5.1 / 7.5'},
            {'key': 'abstencion_involucrado', 'title': 'Abstención de las personas involucradas',
             'desc': 'Asegurar la abstención de las personas involucradas en las decisiones afectadas por el conflicto.',
             'ref': 'ISO 37301 · 5.3 Roles y responsabilidades'},
            {'key': 'norma_interna', 'title': 'Identificación de la norma interna incumplida',
             'desc': 'Referenciar la cláusula del Código de Ética o de la política interna presuntamente incumplida.',
             'ref': 'ISO 37301 · 4.5 / 7.5'},
            {'key': 'acciones_integridad', 'title': 'Acciones de integridad y reforzamiento',
             'desc': 'Definir acciones correctivas, de capacitación o de refuerzo en materia de ética.',
             'ref': 'ISO 37301 · 10.1 Mejora'},
        ],
    },
    'competencia': {
        'label': 'Derecho de la competencia',
        'objective': 'Evaluar la conducta frente a la legislación de competencia económica y, en su caso, atender los deberes de colaboración.',
        'scope': 'Prácticas anticompetitivas, coordinación de precios, reparto de mercado y demás infracciones al derecho de la competencia.',
        'activities': 'Preservar la evidencia de mercado; analizar la conducta bajo la ley de competencia; recabar asesoría legal especializada; evaluar el deber de notificación a la autoridad.',
        'steps': [
            {'key': 'evidencia_mercado', 'title': 'Preservación de evidencia de mercado',
             'desc': 'Conservar comunicaciones, precios, licitaciones y coordinaciones que puedan constituir una conducta anticompetitiva.',
             'ref': 'ISO 37301 · 7.5 / 8.1'},
            {'key': 'analisis_competencia', 'title': 'Análisis bajo la ley de competencia',
             'desc': 'Evaluar la conducta frente a la legislación de competencia económica aplicable.',
             'ref': 'ISO 37301 · 4.5 Requisitos legales'},
            {'key': 'asesoria_especializada', 'title': 'Asesoría legal especializada',
             'desc': 'Cuando proceda, recabar opinión legal especializada en materia de competencia.',
             'ref': 'ISO 37301 · 7.2 Competencia'},
            {'key': 'notificacion_competencia', 'title': 'Evaluación del deber de notificación',
             'desc': 'Analizar el deber de colaboración o denuncia ante la autoridad de competencia.',
             'ref': 'ISO 37301 · 4.5'},
        ],
    },
    'general': {
        'label': 'Procedimiento general',
        'objective': 'Investigar los hechos denunciados de forma imparcial y trazable, determinando su existencia y las acciones que correspondan.',
        'scope': 'Asuntos de competencia del Sistema de Gestión de Cumplimiento no clasificados en una familia específica.',
        'activities': 'Confirmar el alcance del asunto; recabar la evidencia necesaria; solicitar asesoría jurídica cuando proceda y documentar los hallazgos.',
        'steps': [
            {'key': 'verificacion_alcance', 'title': 'Verificación del alcance del asunto',
             'desc': 'Confirmar la competencia del Sistema de Gestión de Cumplimiento y definir el alcance del caso.',
             'ref': 'ISO 37301 · 4.3 Alcance del SGC'},
            {'key': 'asesoria_juridica', 'title': 'Asesoría jurídica cuando proceda',
             'desc': 'Solicitar opinión jurídica si el asunto involucra riesgos legales o normativos específicos.',
             'ref': 'ISO 37301 · 7.2 Competencia'},
        ],
    },
}

FAMILY_LABELS = {key: data['label'] for key, data in PROTOCOL_LIBRARY.items()}

SEVERITY_DEADLINE_DAYS = {
    'muy_grave': 10,
    'grave': 15,
    'media': 20,
    'leve': 30,
}

_FAMILY_BY_CATEGORY = {
    'acoso': {
        'Acoso laboral (mobbing)', 'Acoso laboral', 'Acoso sexual', 'Discriminación',
        'Hostigamiento laboral', 'Hostigamiento sexual', 'Ambiente de trabajo',
    },
    'fraude': {
        'Fraude y corrupción', 'Soborno', 'Malversación o robo', 'Malversación o Robo',
        'Blanqueo de capitales', 'Extorsión', 'Incumplimiento a la Política de Prevención de Lavado de Dinero',
    },
    'datos': {
        'Incumplimiento de la normativa de Protección de Datos',
        'Incumplimiento de la Política de Protección de Datos Personales',
        'Violación de la seguridad de la información',
    },
    'sst': {
        'Incumplimientos graves de seguridad y salud laboral',
        'Incumplimientos de Seguridad y Salud laboral',
        'Condiciones laborales',
    },
    'etica': {
        'Conflictos de interés',
        'Violación de la política interna (Código de Ética)',
        'Violación del Código de Ética',
        'Prácticas laborales ilegales',
        'Incumplimiento a la Política del Sistema de Gestión de Cumplimiento',
    },
    'competencia': {
        'Infracciones de derecho de la competencia',
    },
    'general': {
        'Uso indebido de activos/recursos de la empresa',
        'Prácticas laborales ilegales (Inquietud del Sistema de Gestión de Cumplimiento)',
        'Incumplimiento a los procedimientos de alguna Ley o del Sistema de Gestión de Cumplimiento',
        'Deficiencias en servicios', 'Procesos administrativos', 'Interpretación normativa', 'Situaciones ambiguas',
    },
}

_CATEGORY_ALIASES = {
    'incumplimiento de la normativa de protección de datos': 'Incumplimiento de la normativa de Protección de Datos',
    'incumplimiento de la normativa de proteccion de datos': 'Incumplimiento de la normativa de Protección de Datos',
    'violación de la seguridad de la información': 'Violación de la seguridad de la información',
    'violacion de la seguridad de la informacion': 'Violación de la seguridad de la información',
    'infracciones de derecho de la competencia': 'Infracciones de derecho de la competencia',
    'malversación o robo': 'Malversación o robo',
    'malversacion o robo': 'Malversación o robo',
    'acoso laboral (mobbing)': 'Acoso laboral (mobbing)',
}


def resolve_incident_family(category):
    raw = (category or '').strip()
    if not raw:
        return 'general'
    normalized = _CATEGORY_ALIASES.get(raw.lower(), raw)
    for family, categories in _FAMILY_BY_CATEGORY.items():
        if normalized in categories:
            return family
    lowered = normalized.lower()
    if 'acoso' in lowered or 'hostigamiento' in lowered or 'discrimin' in lowered:
        return 'acoso'
    if 'fraude' in lowered or 'soborno' in lowered or 'robo' in lowered or 'lavado' in lowered:
        return 'fraude'
    if 'datos' in lowered or 'seguridad de la informaci' in lowered:
        return 'datos'
    if 'salud laboral' in lowered or 'seguridad y salud' in lowered:
        return 'sst'
    if 'competencia' in lowered:
        return 'competencia'
    if 'ética' in lowered or 'etica' in lowered or 'conflicto' in lowered or 'política interna' in lowered:
        return 'etica'
    return 'general'


def build_extra_steps(family):
    data = PROTOCOL_LIBRARY.get(family) or PROTOCOL_LIBRARY['general']
    return [
        {'key': step['key'], 'title': step['title'], 'desc': step['desc'], 'ref': step['ref'], 'done': False}
        for step in data['steps']
    ]


def _prefill_plan(complaint, family):
    plan, _ = InvestigationPlan.objects.get_or_create(complaint=complaint)
    data = PROTOCOL_LIBRARY.get(family) or PROTOCOL_LIBRARY['general']

    to_update = []
    if not (plan.objective or '').strip() and data.get('objective'):
        plan.objective = data['objective']
        to_update.append('objective')
    if not (plan.scope or '').strip() and data.get('scope'):
        plan.scope = data['scope']
        to_update.append('scope')
    if not (plan.activities or '').strip() and data.get('activities'):
        plan.activities = data['activities']
        to_update.append('activities')

    if not plan.deadline:
        days = SEVERITY_DEADLINE_DAYS.get((complaint.severity or '').strip(), 20)
        base = complaint.created_at or timezone.now()
        if timezone.is_aware(base):
            base = timezone.localtime(base)
        plan.deadline = base.date() + timedelta(days=days)
        to_update.append('deadline')

    if to_update:
        plan.save(update_fields=to_update)
    return plan


def apply_iso_protocol(complaint, force=False):
    family = resolve_incident_family(getattr(complaint, 'category', '') or '')
    procedure, _ = InvestigationProcedure.objects.get_or_create(complaint=complaint)

    if force or procedure.protocol_family != family:
        procedure.protocol_family = family
        procedure.extra_steps = build_extra_steps(family)
        procedure.save(update_fields=['protocol_family', 'extra_steps', 'updated_at'])

    _prefill_plan(complaint, family)
    return procedure
