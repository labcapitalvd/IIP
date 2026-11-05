import {
  CardTemplate,
  FieldChoice,
  FieldTree,
  FormField,
  FormQuestion,
  FormSection,
  FormTree,
  IIPForm,
  QuestionKind,
  QuestionTree,
  SectionTree,
} from '../types';

/**
 * Modelo del formulario (igual que en la BD, `forms.section_types` C / V / I):
 *   Formulario → Componentes → Variables → Indicadores → Preguntas
 * Cada pregunta lleva un peso (`grading.criteria`) para la calificación manual; los pesos de
 * todas las preguntas del formulario deben sumar 100.
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

export const newVariable = (componentCode: string, n: number): FormSection => {
  const code = `${componentCode}_V${n}`;
  return {
    id: uid('var'),
    code,
    label: '',
    description: '',
    help_text: '',
    order_index: n,
    icon_name: 'Layers',
    children: [newIndicator(code, 1)],
  };
};

export const newComponent = (n: number): FormSection => {
  const code = `C${n}`;
  return {
    id: uid('cmp'),
    code,
    label: '',
    description: '',
    help_text: '',
    order_index: n,
    icon_name: 'Building2',
    children: [newVariable(code, 1)],
  };
};

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

export const getVariables = (component: FormSection): FormSection[] => component.children ?? [];
export const getIndicators = (variable: FormSection): FormSection[] => variable.children ?? [];

/** Todos los indicadores del formulario, en orden. */
export const allIndicators = (form: IIPForm): FormSection[] =>
  form.sections.flatMap((c) => getVariables(c).flatMap(getIndicators));

/** Todas las preguntas del formulario (de todos los indicadores), en orden. */
export const allQuestions = (form: IIPForm): FormQuestion[] => allIndicators(form).flatMap((i) => i.questions ?? []);

export const countComponents = (form: IIPForm): number => form.sections.length;
export const countVariables = (form: IIPForm): number =>
  form.sections.reduce((acc, c) => acc + getVariables(c).length, 0);
export const countIndicators = (form: IIPForm): number => allIndicators(form).length;
export const countQuestions = (form: IIPForm): number => allQuestions(form).length;

/* ------------------------------ Pesos ------------------------------ */

export const TARGET_WEIGHT = 100;

const cents = (n: number | undefined) => Math.round((Number(n) || 0) * 100);

/** Suma de pesos de las preguntas de una sección (recursiva). */
export const sectionWeight = (section: FormSection): number =>
  ((section.questions ?? []).reduce((a, q) => a + cents(q.weight), 0) +
    (section.children ?? []).reduce((a, c) => a + sectionWeight(c) * 100, 0)) /
  100;

export const formWeight = (form: IIPForm): number => form.sections.reduce((a, c) => a + sectionWeight(c), 0);

export const weightIsComplete = (total: number) => Math.abs(total - TARGET_WEIGHT) < 0.005;

export const formatWeight = (n: number) => `${+n.toFixed(2)}`;

/** Reparte `target` en `n` partes de centésimas que suman exactamente `target`. */
const evenCents = (n: number, targetCents: number): number[] => {
  if (!n) return [];
  const base = Math.floor(targetCents / n);
  const extra = targetCents - base * n;
  return Array.from({ length: n }, (_, i) => base + (i < extra ? 1 : 0));
};

/** Escala proporcionalmente los pesos actuales para que sumen 100 (o reparte parejo si todos son 0). */
export const scaleWeightsTo100 = (form: IIPForm): IIPForm => {
  const copy = structuredClone(form);
  const qs = allQuestions(copy);
  const targetCents = TARGET_WEIGHT * 100;
  const total = qs.reduce((a, q) => a + cents(q.weight), 0);
  if (!qs.length) return copy;
  let result: number[];
  if (total === 0) {
    result = evenCents(qs.length, targetCents);
  } else {
    const raw = qs.map((q) => (cents(q.weight) / total) * targetCents);
    result = raw.map(Math.floor);
    let left = targetCents - result.reduce((a, b) => a + b, 0);
    [...raw.keys()]
      .sort((x, y) => raw[y] - Math.floor(raw[y]) - (raw[x] - Math.floor(raw[x])))
      .forEach((idx) => {
        if (left-- > 0) result[idx] += 1;
      });
  }
  qs.forEach((q, i) => (q.weight = result[i] / 100));
  return copy;
};

/** Reparte 100 en partes iguales entre todas las preguntas del formulario. */
export const distributeWeightsEvenly = (form: IIPForm): IIPForm => {
  const copy = structuredClone(form);
  const qs = allQuestions(copy);
  const parts = evenCents(qs.length, TARGET_WEIGHT * 100);
  qs.forEach((q, i) => (q.weight = parts[i] / 100));
  return copy;
};

/**
 * Lleva formularios con formatos anteriores al modelo actual. Es idempotente:
 *  - Dimensión → Criterio (pregunta con N campos)      → Componente → Variable → Indicador → Preguntas
 *  - Variable → Indicador → Preguntas (sin Componente) → se agrupa en un «Componente 1»
 */
const migrateLegacyDimension = (sec: FormSection): FormSection => {
  const indicators: FormSection[] = (sec.questions ?? []).map((legacy, i) => {
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
};

/** Una raíz es una Variable (formato sin Componente) si sus hijos son Indicadores (tienen preguntas, no hijos). */
const isVariableRoot = (sec: FormSection) =>
  !!sec.children?.length && sec.children.every((c) => !c.children?.length);

export const migrateForm = (form: IIPForm): IIPForm => {
  const roots = form.sections.map((sec) =>
    !sec.children?.length && sec.questions?.length ? migrateLegacyDimension(sec) : sec
  );
  if (!roots.some(isVariableRoot)) return { ...form, sections: roots };
  // Formato sin Componente: todas las variables raíz pasan a un único «Componente 1».
  const variables = roots.filter(isVariableRoot);
  const others = roots.filter((r) => !isVariableRoot(r));
  const component: FormSection = {
    id: uid('cmp'),
    code: 'C1',
    label: 'Componente 1',
    description: '',
    help_text: '',
    order_index: 1,
    icon_name: 'Building2',
    children: variables,
  };
  return { ...form, sections: [component, ...others] };
};

/**
 * Vista para el portal de entidades (aún con el diseño anterior): cada Variable (de
 * cualquier Componente) agrupa en `questions` las preguntas de todos sus Indicadores.
 */
export const flattenForEntity = (form: IIPForm): IIPForm => ({
  ...form,
  sections: form.sections.flatMap((c) =>
    getVariables(c).map((v) => ({
      ...v,
      children: undefined,
      questions: [...(v.questions ?? []), ...getIndicators(v).flatMap((i) => i.questions ?? [])],
    }))
  ),
});

export interface FormIssue {
  message: string;
  /** Índices del componente / variable / indicador y id de la pregunta con el problema. */
  c: number;
  v: number | null;
  i: number | null;
  questionId?: string;
}

/**
 * Validación previa al guardado. Devuelve el primer problema (con su ubicación) o null.
 * Los pesos de todas las preguntas deben sumar exactamente 100.
 */
export const findFormIssue = (form: IIPForm): FormIssue | null => {
  if (!form.sections.length) return { message: 'El formulario necesita al menos un componente.', c: 0, v: null, i: null };
  const labelOk = (s: string | undefined | null) => !!s && s.trim().length > 0 && s.length <= 255;
  for (const [ci, c] of form.sections.entries()) {
    const cn = `Componente ${ci + 1}`;
    if (!labelOk(c.label)) return { message: `${cn}: el nombre es obligatorio (máx. 255 caracteres).`, c: ci, v: null, i: null };
    const vars = getVariables(c);
    if (!vars.length) return { message: `${cn}: agregue al menos una variable.`, c: ci, v: null, i: null };
    for (const [vi, v] of vars.entries()) {
      const vn = `${cn}, variable ${ci + 1}.${vi + 1}`;
      if (!labelOk(v.label)) return { message: `${vn}: el nombre es obligatorio (máx. 255 caracteres).`, c: ci, v: vi, i: null };
      const inds = getIndicators(v);
      if (!inds.length) return { message: `${vn}: agregue al menos un indicador.`, c: ci, v: vi, i: null };
      for (const [ii, ind] of inds.entries()) {
        const inn = `${vn}, indicador ${ci + 1}.${vi + 1}.${ii + 1}`;
        const at = (message: string, questionId?: string): FormIssue => ({ message, c: ci, v: vi, i: ii, questionId });
        if (!labelOk(ind.label)) return at(`${inn}: el nombre es obligatorio (máx. 255 caracteres).`);
        const qs = ind.questions ?? [];
        if (!qs.length) return at(`${inn}: agregue al menos una pregunta.`);
        const nums = numberQuestions(qs);
        for (const q of qs) {
          const qn = `${inn}, pregunta ${nums[q.id]}`;
          if (!labelOk(q.label)) return at(`${qn}: el enunciado es obligatorio (máx. 255 caracteres).`, q.id);
          const w = Number(q.weight ?? 0);
          if (!Number.isFinite(w) || w < 0 || w > TARGET_WEIGHT)
            return at(`${qn}: el peso debe estar entre 0 y ${TARGET_WEIGHT}.`, q.id);
          if (cents(w) !== w * 100 && Math.abs(cents(w) - w * 100) > 1e-6)
            return at(`${qn}: el peso admite máximo 2 decimales.`, q.id);
          if ((q.grading_guide ?? '').length > 4096) return at(`${qn}: la guía de calificación es demasiado larga.`, q.id);
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
  }
  const total = formWeight(form);
  if (!weightIsComplete(total))
    return {
      message: `Los pesos de las preguntas suman ${formatWeight(total)} y deben sumar exactamente ${TARGET_WEIGHT}. Ajústelos o use «Escalar a 100» / «Repartir en partes iguales».`,
      c: 0,
      v: null,
      i: null,
    };
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
      weight: Number((q.weight ?? 0).toFixed(2)),
      grading_guide: q.grading_guide?.trim() || null,
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

  const LEVELS = ['C', 'V', 'I'] as const;
  const sectionReq = (s: FormSection, order: number, depth: 0 | 1 | 2): any => ({
    code: s.code,
    label: s.label,
    description: s.description || null,
    helper: s.help_text || null,
    icon: s.icon_name || null,
    display_order: order,
    section_type_code: LEVELS[depth],
    // Solo los indicadores (nivel 2) tienen preguntas; componentes y variables solo hijos.
    questions: depth === 2 ? (s.questions ?? []).map((q, i) => questionReq(q, i, s.questions ?? [])) : [],
    children: depth < 2 ? (s.children ?? []).map((c, i) => sectionReq(c, i, (depth + 1) as 1 | 2)) : [],
  });

  return {
    code: form.code,
    label: form.label,
    description: form.description,
    year: form.year || null,
    version: form.version || null,
    is_active: form.is_active,
    sections: form.sections.map((c, i) => sectionReq(c, i, 0)),
  };
};

const FIELD_TYPE_UI: Record<string, FormField['field_type_code']> = {
  single_choice: 'singlechoice',
  multi_choice: 'multichoice',
};

/** Árbol de GET /public/forms/{id} → IIPForm. Inverso de toCreateFormRequest. */
export const fromFormTree = (tree: FormTree): IIPForm => {
  const field = (f: FieldTree): FormField => {
    const type = FIELD_TYPE_UI[f.field_type_code] ?? (f.field_type_code as FormField['field_type_code']);
    return {
      id: f.id,
      code: f.code,
      label: f.label,
      field_type_id: `ft-${type}`,
      field_type_code: type,
      is_required: f.required,
      help_text: f.description ?? undefined,
      choices: isChoiceType(type) ? f.field_choices.map((c) => ({ id: c.id, code: c.code, label: c.label })) : undefined,
      allowed_file_types: type === 'file' ? f.allowed_file_type_codes : undefined,
      max_file_size: type === 'file' ? (f.max_file_size ?? DEFAULT_MAX_FILE_SIZE) : undefined,
    };
  };

  const question = (q: QuestionTree, i: number): FormQuestion => {
    const groups = q.card_template?.field_groups ?? [];
    const firstType = groups[0]?.fields[0] ? field(groups[0].fields[0]).field_type_code : 'text';
    return {
      id: q.id,
      code: q.code,
      label: q.label,
      description: q.description,
      help_text: q.helper ?? '',
      order_index: i + 1,
      weight: q.weight ?? 0,
      grading_guide: q.grading_guide ?? '',
      question_kind: q.is_loop ? 'loop' : fieldTypeToKind(firstType),
      is_required: q.required,
      depends_on: q.depends_on ? { question_id: q.depends_on.question_id, value: q.depends_on.expected_value } : null,
      card_template: {
        id: q.card_template?.id ?? uid('ct'),
        code: q.card_template?.code ?? `CT_${q.code}`,
        label: q.card_template?.label ?? q.label,
        is_repeatable: q.is_loop,
        field_groups: groups.map((g) => ({ id: g.id, code: g.code, label: g.label, fields: g.fields.map(field) })),
      },
    };
  };

  const section = (s: SectionTree, i: number): FormSection => ({
    id: s.id,
    code: s.code,
    label: s.label,
    description: s.description ?? '',
    help_text: s.helper ?? '',
    order_index: i + 1,
    icon_name: s.icon ?? undefined,
    questions: s.questions.map(question),
    children: s.children.length ? s.children.map(section) : undefined,
  });

  return migrateForm({
    id: tree.id,
    code: tree.code,
    label: tree.label,
    description: tree.description,
    year: tree.year ?? new Date(tree.updated_at).getFullYear(),
    version: tree.version ?? '1.0',
    is_active: tree.is_active,
    sections: tree.sections.map(section),
    is_synced_to_backend: true,
    updated_at: tree.updated_at,
  });
};

/**
 * Reasigna códigos estables por posición (C1, C1_V1, C1_V1_I1, Q1, F1, OP1…), únicos dentro
 * de su contenedor como exige el backend. Las dependencias usan ids, no códigos.
 */
export const normalizeCodes = (form: IIPForm): IIPForm => ({
  ...form,
  sections: form.sections.map((c, ci) => {
    const ccode = `C${ci + 1}`;
    return {
      ...c,
      code: ccode,
      order_index: ci + 1,
      children: getVariables(c).map((v, vi) => {
        const vcode = `${ccode}_V${vi + 1}`;
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
                      choices: f.choices?.map((ch, chi) => ({ ...ch, code: `OP${chi + 1}` })),
                    })),
                  })),
                },
              };
            }),
          })),
        };
      }),
    };
  }),
});
