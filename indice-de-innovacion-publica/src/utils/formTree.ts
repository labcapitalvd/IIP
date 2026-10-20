import {
  CardTemplate,
  FieldChoice,
  FormField,
  FormQuestion,
  FormSection,
  IIPForm,
  QuestionKind,
} from '../types';

/**
 * Modelo del formulario:
 *   Formulario → Variables (sección raíz) → Indicadores (sección hija) → Preguntas
 * Una pregunta es simple (un campo) o bucle (tarjetas repetibles con varios campos).
 */

export const QUESTION_KINDS: { value: QuestionKind; label: string }[] = [
  { value: 'text', label: 'Texto' },
  { value: 'numeric', label: 'Numérica' },
  { value: 'single_choice', label: 'Selección única' },
  { value: 'multi_choice', label: 'Selección múltiple' },
  { value: 'boolean', label: 'Sí / No' },
  { value: 'file', label: 'Archivo (carga de documentos)' },
  { value: 'loop', label: 'Bucle (tarjetas repetibles)' },
];

/** Tipos permitidos para los campos de una tarjeta de bucle. */
export const LOOP_FIELD_KINDS: { value: FormField['field_type_code']; label: string }[] = [
  { value: 'text', label: 'Texto' },
  { value: 'numeric', label: 'Numérica' },
  { value: 'date', label: 'Fecha' },
  { value: 'singlechoice', label: 'Selección única' },
  { value: 'multichoice', label: 'Selección múltiple' },
  { value: 'boolean', label: 'Sí / No' },
  { value: 'file', label: 'Archivo' },
];

export const kindToFieldType = (kind: Exclude<QuestionKind, 'loop'>): FormField['field_type_code'] =>
  kind === 'single_choice' ? 'singlechoice' : kind === 'multi_choice' ? 'multichoice' : kind;

export const fieldTypeToKind = (t: FormField['field_type_code']): Exclude<QuestionKind, 'loop'> =>
  t === 'singlechoice' ? 'single_choice' : t === 'multichoice' ? 'multi_choice' : (t === 'date' ? 'text' : t);

let counter = 0;
export const uid = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${(counter++).toString(36)}`;

export const DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024;

export const isChoiceType = (t: FormField['field_type_code']) => t === 'singlechoice' || t === 'multichoice';

export const newChoice = (n: number): FieldChoice => ({ id: uid('ch'), code: `OP${n}`, label: `Opción ${n}` });

export const newField = (n: number, type: FormField['field_type_code'], label = ''): FormField => ({
  id: uid('f'),
  code: `F${n}`,
  label,
  field_type_id: `ft-${type}`,
  field_type_code: type,
  is_required: true,
  choices: isChoiceType(type) ? [newChoice(1), newChoice(2)] : undefined,
  unit: undefined,
  allowed_file_types: type === 'file' ? [] : undefined,
  max_file_size: type === 'file' ? DEFAULT_MAX_FILE_SIZE : undefined,
});

const emptyCard = (code: string, label: string, fields: FormField[], repeatable: boolean): CardTemplate => ({
  id: uid('ct'),
  code: `CT_${code}`,
  label,
  is_repeatable: repeatable,
  field_groups: [{ id: uid('fg'), code: 'FG', label, fields }],
});

/** Crea una pregunta vacía del tipo indicado. `n` = posición dentro del indicador. */
export const newQuestion = (kind: QuestionKind, n: number): FormQuestion => {
  const code = `Q${n}`;
  const base = { id: uid('q'), code, label: '', help_text: '', question_kind: kind, is_required: true, depends_on: null as FormQuestion['depends_on'] };
  if (kind === 'loop') {
    return { ...base, card_template: emptyCard(code, 'Detalle', [newField(1, 'text', '')], true) };
  }
  return { ...base, card_template: emptyCard(code, code, [newField(1, kindToFieldType(kind))], false) };
};

export const newIndicator = (variableCode: string, n: number): FormSection => ({
  id: uid('ind'),
  code: `${variableCode}_I${n}`,
  label: '',
  description: '',
  help_text: '',
  order_index: n,
  icon_name: 'Target',
  questions: [newQuestion('boolean', 1)],
});

export const newVariable = (n: number): FormSection => ({
  id: uid('var'),
  code: `V${n}`,
  label: '',
  description: '',
  help_text: '',
  order_index: n,
  icon_name: 'Layers',
  children: [newIndicator(`V${n}`, 1)],
});

export const questionFields = (q: FormQuestion): FormField[] =>
  q.card_template.field_groups.flatMap((g) => g.fields);

/** Tipo efectivo de una pregunta (tolera datos antiguos sin `question_kind`). */
export const kindOf = (q: FormQuestion): QuestionKind =>
  q.question_kind ?? (q.card_template.is_repeatable ? 'loop' : fieldTypeToKind(questionFields(q)[0]?.field_type_code ?? 'text'));

/**
 * Numeración visible: preguntas simples 1, 2, 3…; un bucle que depende de la
 * pregunta N se numera N.1, N.2…
 */
export const numberQuestions = (questions: FormQuestion[]): Record<string, string> => {
  const out: Record<string, string> = {};
  const childCount: Record<string, number> = {};
  let n = 0;
  for (const q of questions) {
    const parent = q.depends_on && out[q.depends_on.question_id];
    if (parent) {
      childCount[q.depends_on!.question_id] = (childCount[q.depends_on!.question_id] || 0) + 1;
      out[q.id] = `${parent}.${childCount[q.depends_on!.question_id]}`;
    } else {
      out[q.id] = String(++n);
    }
  }
  return out;
};

export const getIndicators = (variable: FormSection): FormSection[] => variable.children ?? [];

export const countQuestions = (form: IIPForm): number =>
  form.sections.reduce(
    (acc, v) => acc + getIndicators(v).reduce((a, i) => a + (i.questions?.length || 0), 0) + (v.questions?.length || 0),
    0
  );

export const countIndicators = (form: IIPForm): number =>
  form.sections.reduce((acc, v) => acc + getIndicators(v).length, 0);

/**
 * Convierte formularios guardados con el formato anterior
 * (Dimensión → Criterio(pregunta con N campos)) al modelo actual
 * (Variable → Indicador → Preguntas). Es idempotente.
 */
export const migrateForm = (form: IIPForm): IIPForm => ({
  ...form,
  sections: form.sections.map((sec) => {
    if (sec.children?.length || !sec.questions?.length) return sec;
    const indicators: FormSection[] = sec.questions.map((legacy, i) => {
      const fields = questionFields(legacy);
      const repeatable = !!legacy.card_template.is_repeatable;
      const questions: FormQuestion[] = repeatable
        ? [{ ...legacy, question_kind: 'loop', is_required: true, depends_on: null }]
        : fields.map((f, k) => ({
            id: `${legacy.id}-${k + 1}`,
            code: `Q${k + 1}`,
            label: f.label,
            help_text: f.help_text,
            question_kind: fieldTypeToKind(f.field_type_code),
            is_required: f.is_required,
            depends_on: null,
            card_template: emptyCard(`Q${k + 1}`, f.label, [f], false),
          }));
      return {
        id: legacy.id,
        code: `${sec.code}_I${i + 1}`.slice(0, 50),
        label: legacy.label,
        description: legacy.description ?? '',
        help_text: '',
        order_index: i + 1,
        icon_name: sec.icon_name ?? 'Target',
        questions,
      };
    });
    return { ...sec, questions: undefined, children: indicators };
  }),
});

/**
 * Vista para el portal de entidades (aún con el diseño anterior): cada Variable
 * agrupa en `questions` las preguntas de todos sus Indicadores.
 */
export const flattenForEntity = (form: IIPForm): IIPForm => ({
  ...form,
  sections: form.sections.map((v) => ({
    ...v,
    children: undefined,
    questions: [...(v.questions ?? []), ...getIndicators(v).flatMap((i) => i.questions ?? [])],
  })),
});

export interface FormIssue {
  message: string;
  /** Índices de la variable / indicador y id de la pregunta con el problema. */
  v: number;
  i: number | null;
  questionId?: string;
}

/** Validación previa al guardado. Devuelve el primer problema (con su ubicación) o null. */
export const findFormIssue = (form: IIPForm): FormIssue | null => {
  if (!form.sections.length) return { message: 'El formulario necesita al menos una variable.', v: 0, i: null };
  const labelOk = (s: string | undefined | null) => !!s && s.trim().length > 0 && s.length <= 255;
  for (const [vi, v] of form.sections.entries()) {
    const vn = `Variable ${vi + 1}`;
    if (!labelOk(v.label)) return { message: `${vn}: el nombre es obligatorio (máx. 255 caracteres).`, v: vi, i: null };
    const inds = getIndicators(v);
    if (!inds.length) return { message: `${vn}: agregue al menos un indicador.`, v: vi, i: null };
    for (const [ii, ind] of inds.entries()) {
      const inn = `${vn}, indicador ${ii + 1}`;
      const at = (message: string, questionId?: string): FormIssue => ({ message, v: vi, i: ii, questionId });
      if (!labelOk(ind.label)) return at(`${inn}: el nombre es obligatorio (máx. 255 caracteres).`);
      const qs = ind.questions ?? [];
      if (!qs.length) return at(`${inn}: agregue al menos una pregunta.`);
      const nums = numberQuestions(qs);
      for (const q of qs) {
        const qn = `${inn}, pregunta ${nums[q.id]}`;
        if (!labelOk(q.label)) return at(`${qn}: el enunciado es obligatorio (máx. 255 caracteres).`, q.id);
        const kind = kindOf(q);
        const fields = questionFields(q);
        if (kind === 'loop') {
          if (q.depends_on) {
            const parent = qs.find((p) => p.id === q.depends_on!.question_id);
            if (!parent || kindOf(parent) !== 'boolean' || qs.indexOf(parent) > qs.indexOf(q))
              return at(`${qn}: la pregunta Sí/No de la que depende debe estar antes, en el mismo indicador.`, q.id);
          }
          if (!fields.length) return at(`${qn}: agregue al menos un campo a la tarjeta.`, q.id);
        }
        for (const f of fields) {
          if (kind === 'loop' && !labelOk(f.label)) return at(`${qn}: todos los campos de la tarjeta necesitan nombre.`, q.id);
          if (f.field_type_code === 'file') {
            if (!f.allowed_file_types?.length) return at(`${qn}: seleccione al menos un tipo de archivo permitido.`, q.id);
            if (!f.max_file_size || f.max_file_size <= 0) return at(`${qn}: indique el tamaño máximo del archivo.`, q.id);
          }
          if (isChoiceType(f.field_type_code) && (f.choices?.length ?? 0) < 2)
            return at(`${qn}: la selección necesita al menos 2 opciones.`, q.id);
          if (isChoiceType(f.field_type_code) && f.choices!.some((c) => !labelOk(c.label)))
            return at(`${qn}: todas las opciones necesitan texto.`, q.id);
        }
      }
    }
  }
  return null;
};

export const validateForm = (form: IIPForm): string | null => findFormIssue(form)?.message ?? null;

const FIELD_TYPE_API: Record<FormField['field_type_code'], string> = {
  boolean: 'boolean',
  text: 'text',
  numeric: 'numeric',
  date: 'date',
  singlechoice: 'single_choice',
  multichoice: 'multi_choice',
  file: 'file',
};

/** IIPForm → cuerpo de POST /public/forms (CreateFormRequest del Core). */
export const toCreateFormRequest = (form: IIPForm) => {
  const questionReq = (q: FormQuestion, order: number, siblings: FormQuestion[]) => {
    const parent = q.depends_on ? siblings.find((p) => p.id === q.depends_on!.question_id) : undefined;
    const kind = kindOf(q);
    return {
      code: q.code,
      label: q.label,
      description: q.description ?? null,
      helper: q.help_text || null,
      required: q.is_required ?? true,
      is_loop: kind === 'loop',
      display_order: order,
      depends_on: parent ? { question_code: parent.code, expected_value: q.depends_on!.value } : null,
      card_template: {
        code: q.card_template.code,
        label: q.card_template.label || q.label,
        description: null,
        helper: null,
        field_groups: q.card_template.field_groups.map((g, gi) => ({
          code: g.code,
          label: g.label || q.label,
          description: null,
          display_order: gi,
          fields: g.fields.map((f, fi) => ({
            code: f.code,
            label: f.label || q.label,
            description: f.help_text || null,
            required: f.is_required,
            field_type_code: FIELD_TYPE_API[f.field_type_code],
            display_order: fi,
            allowed_file_type_codes: f.field_type_code === 'file' ? (f.allowed_file_types ?? []) : [],
            max_file_size: f.field_type_code === 'file' ? (f.max_file_size ?? null) : null,
            field_choices: (f.choices ?? []).map((c, ci) => ({
              code: c.code,
              label: c.label,
              description: null,
              display_order: ci,
            })),
          })),
        })),
      },
    };
  };

  const sectionReq = (s: FormSection, order: number, typeCode: 'V' | 'I'): any => ({
    code: s.code,
    label: s.label,
    description: s.description || null,
    helper: s.help_text || null,
    icon: s.icon_name || null,
    display_order: order,
    section_type_code: typeCode,
    questions: (s.questions ?? []).map((q, i) => questionReq(q, i, s.questions ?? [])),
    children: typeCode === 'V' ? getIndicators(s).map((c, i) => sectionReq(c, i, 'I')) : [],
  });

  return {
    code: form.code,
    label: form.label,
    description: form.description,
    sections: form.sections.map((v, i) => sectionReq(v, i, 'V')),
  };
};

/**
 * Reasigna códigos estables por posición (V1, V1_I1, Q1, F1, OP1…), únicos dentro
 * de su contenedor como exige el backend. Las dependencias usan ids, no códigos.
 */
export const normalizeCodes = (form: IIPForm): IIPForm => ({
  ...form,
  sections: form.sections.map((v, vi) => {
    const vcode = `V${vi + 1}`;
    return {
      ...v,
      code: vcode,
      order_index: vi + 1,
      children: getIndicators(v).map((ind, ii) => ({
        ...ind,
        code: `${vcode}_I${ii + 1}`,
        order_index: ii + 1,
        questions: (ind.questions ?? []).map((q, qi) => {
          const qcode = `Q${qi + 1}`;
          return {
            ...q,
            code: qcode,
            order_index: qi + 1,
            card_template: {
              ...q.card_template,
              code: `CT_${qcode}`,
              field_groups: q.card_template.field_groups.map((g) => ({
                ...g,
                code: 'FG',
                fields: g.fields.map((f, fi) => ({
                  ...f,
                  code: `F${fi + 1}`,
                  choices: f.choices?.map((c, ci) => ({ ...c, code: `OP${ci + 1}` })),
                })),
              })),
            },
          };
        }),
      })),
    };
  }),
});
