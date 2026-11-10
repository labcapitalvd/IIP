import React from 'react';
import { AlertCircle, Plus, Trash2 } from 'lucide-react';
import { useFormSubmission } from '../../../context/FormSubmissionContext';
import { FormQuestion, FormSection } from '../../../types';
import { numberQuestions } from '../../../utils/formTree';
import { activeQuestions, visibleFields } from '../../../utils/guidedForm';
import { FieldInput } from './FieldInput';

type CardEntry = { id: string; title: string; answers: Record<string, any>; parent_id?: string | null };

/** Preguntas del indicador activo: simples y fichas repetibles (bucles, con o sin referencia a otra pregunta). */
export const IndicatorForm: React.FC<{ indicator: FormSection }> = ({ indicator }) => {
  const {
    answers, cardEntries, errors, setFieldValue, addCardEntry, removeCardEntry, countDependentCards,
    setCardEntryFieldValue, setCardEntryTitle, activeForm,
  } = useFormSubmission();

  const numbering = numberQuestions(indicator.questions ?? []);
  const questions = activeQuestions(indicator, answers);
  const allQs = activeForm.sections.flatMap((s) => s.questions ?? []);

  const removeCard = (q: FormQuestion, entry: CardEntry) => {
    const n = countDependentCards(entry.id);
    if (n > 0 && !confirm(`Al eliminar «${entry.title || 'esta ficha'}» también se eliminarán ${n} ficha(s) de otras preguntas que se refieren a ella. ¿Continuar?`)) return;
    removeCardEntry(q.id, entry.id);
  };

  const renderCard = (q: FormQuestion, entry: CardEntry, i: number, canRemove: boolean, reference?: string) => (
    <li key={entry.id} className="space-y-4 rounded-2xl border border-iip-line bg-iip-bg/60 p-4">
      <div className="flex items-center gap-2">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-iip-navy text-sm font-bold text-white">{i + 1}</span>
        <input
          type="text"
          value={entry.title}
          aria-label={`Nombre de la ficha ${i + 1}`}
          onChange={(e) => setCardEntryTitle(q.id, entry.id, e.target.value)}
          placeholder={`Nombre de la ficha #${i + 1}`}
          className="iip-focus min-w-0 flex-1 rounded-lg border border-transparent bg-transparent px-2 py-1 text-[15px] font-bold text-iip-ink hover:border-iip-line"
        />
        {reference && <span className="hidden shrink-0 rounded-lg border border-sky-200 bg-sky-50 px-2 py-0.5 text-xs font-semibold text-sky-800 sm:inline">Ref.: {reference}</span>}
        {canRemove && (
          <button type="button" onClick={() => removeCard(q, entry)} aria-label={`Eliminar la ficha ${i + 1}`} className="iip-focus rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600">
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {visibleFields(q).map((f) => (
          <div key={f.id} className={f.field_type_code === 'text' ? 'md:col-span-2' : ''}>
            <FieldInput
              field={f}
              domId={`${entry.id}_${f.id}`}
              value={entry.answers[f.id]}
              error={errors[`${entry.id}_${f.id}`]}
              onChange={(v) => setCardEntryFieldValue(q.id, entry.id, f.id, v)}
            />
          </div>
        ))}
      </div>
    </li>
  );

  const loopError = (q: FormQuestion) =>
    errors[q.id] && (
      <p role="alert" className="flex items-center gap-1.5 text-sm font-semibold text-rose-700">
        <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
        {errors[q.id]}
      </p>
    );

  return (
    <div className="space-y-8">
      {questions.map((q) => {
        const num = numbering[q.id];
        const required = visibleFields(q).some((f) => f.is_required);
        const statement = (
          <div className="space-y-1">
            <h3 className="text-[17px] font-semibold leading-snug text-iip-ink">
              {num && <span className="mr-1.5 text-iip-muted">{num}.</span>}
              {q.label}
              {required && <span className="ml-1 text-rose-600" aria-hidden="true">*</span>}
            </h3>
            {q.description && <p className="text-sm text-iip-muted">{q.description}</p>}
            {q.help_text && <p className="text-sm text-iip-navy-700">{q.help_text}</p>}
          </div>
        );

        if (q.card_template.is_repeatable) {
          const source = q.source_question_id ? allQs.find((x) => x.id === q.source_question_id) : undefined;
          const mine = cardEntries[q.id] ?? [];

          if (source) {
            const sourceEntries = cardEntries[source.id] ?? [];
            return (
              <section key={q.id} className="space-y-3" aria-label={q.label}>
                {statement}
                <p className="text-sm text-sky-800">Registre fichas solo para las iniciativas que apliquen (origen: «{source.label}»).</p>
                {loopError(q)}
                {sourceEntries.length === 0 ? (
                  <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                    Aún no hay iniciativas para referenciar. Primero registre al menos una en «{source.label}».
                  </p>
                ) : (
                  sourceEntries.map((src, si) => {
                    const linked = mine.filter((e) => e.parent_id === src.id);
                    return (
                      <div key={src.id} className="space-y-3 rounded-2xl border border-sky-200 bg-sky-50/40 p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="text-sm font-bold text-sky-900">{si + 1}. {src.title || 'Iniciativa sin nombre'} <span className="font-normal text-sky-700">· {linked.length} registro(s)</span></p>
                        </div>
                        {linked.length > 0 && <ul className="space-y-3">{linked.map((e, i) => renderCard(q, e, i, true, src.title || undefined))}</ul>}
                        <button type="button" onClick={() => addCardEntry(q.id, q.card_template.id, undefined, src.id)} className="iip-focus flex items-center gap-1.5 rounded-xl border border-sky-200 bg-white px-3 py-1.5 text-sm font-semibold text-sky-900 hover:bg-sky-100">
                          <Plus className="h-4 w-4" aria-hidden="true" /> Agregar ficha para esta iniciativa
                        </button>
                      </div>
                    );
                  })
                )}
              </section>
            );
          }

          return (
            <section key={q.id} className="space-y-3" aria-label={q.label}>
              {statement}
              {loopError(q)}
              {mine.length === 0 ? (
                <p className="rounded-xl bg-iip-bg p-4 text-sm text-iip-muted">Aún no hay fichas. Use «Agregar ficha» para registrar la primera.</p>
              ) : (
                <ul className="space-y-3">{mine.map((e, i) => renderCard(q, e, i, mine.length > 1))}</ul>
              )}
              <button type="button" onClick={() => addCardEntry(q.id, q.card_template.id)} className="iip-focus flex items-center gap-1.5 rounded-xl bg-iip-yellow px-3.5 py-2 text-sm font-bold text-iip-ink hover:bg-iip-yellow-600">
                <Plus className="h-4 w-4" aria-hidden="true" /> Agregar ficha
              </button>
            </section>
          );
        }

        const fields = visibleFields(q);
        const single = fields.length === 1;
        return (
          <section key={q.id} className="space-y-3" aria-label={q.label}>
            {statement}
            <div className="space-y-4">
              {fields.map((f) => (
                <FieldInput
                  key={f.id}
                  field={f}
                  domId={f.id}
                  value={answers[f.id]}
                  error={errors[f.id]}
                  hideLabel={single && (!f.label || f.label === q.label)}
                  onChange={(v) => setFieldValue(f.id, v)}
                />
              ))}
            </div>
          </section>
        );
      })}
      {questions.length === 0 && <p className="rounded-xl bg-iip-bg p-4 text-sm text-iip-muted">Este indicador no tiene preguntas por responder.</p>}
    </div>
  );
};
