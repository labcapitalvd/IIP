import { FormField, FormQuestion, FormSection, IIPForm } from '../types';
import { getIndicators, getVariables, kindOf, questionFields } from './formTree';

/**
 * Lógica pura del asistente de diligenciamiento (sin React):
 * recorrido Componente → Variable → Indicador, preguntas activas, validación y progreso.
 * Esta interfaz no maneja evidencias: las preguntas/campos de tipo `file` se ignoran.
 */

export interface AnswerState {
  answers: Record<string, any>;
  cardEntries: Record<string, { id: string; title: string; answers: Record<string, any>; parent_id?: string | null }[]>;
}

/** Posición de un indicador dentro del recorrido guiado. */
export interface IndicatorRef {
  index: number;
  component: FormSection;
  variable: FormSection;
  /** Si la variable no tiene indicadores (diseño antiguo) la propia variable hace de indicador. */
  indicator: FormSection;
}

export const isFilled = (v: unknown): boolean =>
  v !== undefined && v !== null && v !== '' && !(Array.isArray(v) && v.length === 0);

/** Componentes que la entidad debe responder (todos si aún no eligió). */
export const selectedComponents = (form: IIPForm, selectedIds: string[] | null): FormSection[] =>
  selectedIds ? form.sections.filter((c) => selectedIds.includes(c.id)) : form.sections;

/** Recorrido plano de indicadores de los componentes elegidos, en orden. */
export const buildIndicatorRefs = (form: IIPForm, selectedIds: string[] | null): IndicatorRef[] => {
  const refs: IndicatorRef[] = [];
  for (const component of selectedComponents(form, selectedIds)) {
    for (const variable of getVariables(component)) {
      const indicators = getIndicators(variable);
      const list = indicators.length ? indicators : (variable.questions?.length ? [variable] : []);
      for (const indicator of list) refs.push({ index: refs.length, component, variable, indicator });
    }
  }
  return refs;
};

// ---- Preguntas activas ------------------------------------------------------------------

const isFileField = (f: FormField) => f.field_type_code === 'file';

/** Campos visibles/contables de una pregunta (sin archivos). */
export const visibleFields = (q: FormQuestion): FormField[] => questionFields(q).filter((f) => !isFileField(f));

/** Una pregunta bucle con `depends_on` solo aplica si la pregunta de la que depende tiene esa respuesta. */
export const isQuestionActive = (q: FormQuestion, siblings: FormQuestion[], answers: Record<string, any>): boolean => {
  if (kindOf(q) === 'file') return false;
  if (visibleFields(q).length === 0 && !q.card_template.is_repeatable) return false;
  if (!q.depends_on) return true;
  const parent = siblings.find((s) => s.id === q.depends_on!.question_id);
  const parentField = parent && visibleFields(parent)[0];
  if (!parentField) return true;
  return answers[parentField.id] === q.depends_on.value;
};

export const activeQuestions = (indicator: FormSection, answers: Record<string, any>): FormQuestion[] => {
  const all = indicator.questions ?? [];
  return all.filter((q) => isQuestionActive(q, all, answers));
};

// ---- Validación -------------------------------------------------------------------------

/** Errores de un indicador con las mismas claves que usa la UI (field.id, `${entry.id}_${field.id}` o question.id). */
export const validateIndicator = (indicator: FormSection, state: AnswerState): Record<string, string> => {
  const errors: Record<string, string> = {};
  for (const q of activeQuestions(indicator, state.answers)) {
    if (q.card_template.is_repeatable) {
      const entries = state.cardEntries[q.id] ?? [];
      const min = q.card_template.min_entries ?? 0;
      if (entries.length < min) errors[q.id] = `Debe registrar al menos ${min} ficha(s).`;
      entries.forEach((entry, i) => {
        visibleFields(q).forEach((f) => {
          if (f.is_required && !isFilled(entry.answers[f.id]))
            errors[`${entry.id}_${f.id}`] = `«${f.label}» es obligatorio en la ficha #${i + 1}.`;
        });
      });
    } else {
      visibleFields(q).forEach((f) => {
        if (f.is_required && !isFilled(state.answers[f.id])) errors[f.id] = `«${f.label}» es obligatorio.`;
      });
    }
  }
  return errors;
};

// ---- Progreso ---------------------------------------------------------------------------

export interface IndicatorProgress {
  answered: number;
  total: number;
  /** Tiene al menos una respuesta y no le falta ningún dato obligatorio. */
  complete: boolean;
}

export const indicatorProgress = (indicator: FormSection, state: AnswerState): IndicatorProgress => {
  let answered = 0;
  let total = 0;
  for (const q of activeQuestions(indicator, state.answers)) {
    if (q.card_template.is_repeatable) {
      total += 1;
      const entries = state.cardEntries[q.id] ?? [];
      if (entries.some((e) => Object.values(e.answers).some(isFilled))) answered += 1;
    } else {
      visibleFields(q).forEach((f) => {
        total += 1;
        if (isFilled(state.answers[f.id])) answered += 1;
      });
    }
  }
  const complete = answered > 0 && Object.keys(validateIndicator(indicator, state)).length === 0;
  return { answered, total, complete };
};

const percent = (done: number, all: number) => (all === 0 ? 0 : Math.round((done / all) * 100));

/** % de indicadores completos dentro de un conjunto de referencias. */
export const progressOf = (refs: IndicatorRef[], state: AnswerState): number =>
  percent(refs.filter((r) => indicatorProgress(r.indicator, state).complete).length, refs.length);

export const refsOfComponent = (refs: IndicatorRef[], componentId: string) =>
  refs.filter((r) => r.component.id === componentId);

export const refsOfVariable = (refs: IndicatorRef[], variableId: string) =>
  refs.filter((r) => r.variable.id === variableId);
