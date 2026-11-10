import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Download, X } from 'lucide-react';
import { FormField, IIPForm } from '../../../types';
import { AnswerState, activeQuestions, buildIndicatorRefs, isFilled, visibleFields } from '../../../utils/guidedForm';
import { numberQuestions } from '../../../utils/formTree';

/** Texto legible de una respuesta (etiquetas de opciones en lugar de ids). */
export const answerText = (f: FormField, v: any): string => {
  if (!isFilled(v)) return '';
  const label = (id: any) => f.choices?.find((c) => c.id === id || c.code === id)?.label ?? String(id);
  switch (f.field_type_code) {
    case 'boolean':
      return v === true || v === 'true' ? 'Sí' : 'No';
    case 'singlechoice':
      return label(v);
    case 'multichoice':
      return (Array.isArray(v) ? v : [v]).map(label).join(', ');
    case 'numeric':
      return `${v}${f.unit ? ` ${f.unit}` : ''}`;
    case 'date':
      return new Date(`${v}T00:00:00`).toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });
    default:
      return String(v);
  }
};

const Value: React.FC<{ text: string }> = ({ text }) =>
  text ? <span className="whitespace-pre-line font-semibold text-iip-ink">{text}</span> : <span className="italic text-iip-muted">Sin respuesta</span>;

interface Props {
  form: IIPForm;
  selectedIds: string[] | null;
  state: AnswerState;
  entityLabel: string;
  onClose: () => void;
}

/** Todas las respuestas del formulario, por Componente → Variable → Indicador, con exportación a PDF. */
export const AnswersReport: React.FC<Props> = ({ form, selectedIds, state, entityLabel, onClose }) => {
  const refs = buildIndicatorRefs(form, selectedIds);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    panelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const compNumber = (id: string) => form.sections.findIndex((c) => c.id === id) + 1;
  const components = refs.filter((r, i, a) => a.findIndex((x) => x.component.id === r.component.id) === i);
  const today = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

  return createPortal(
    <div className="iip-report-overlay fixed inset-0 z-50 flex items-center justify-center bg-iip-ink/70 p-3 sm:p-6">
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-title"
        className="iip-report-panel flex max-h-full w-full max-w-4xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl outline-none"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 bg-iip-navy px-5 py-4 text-white">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-wide text-iip-yellow">Índice de Innovación Pública</p>
            <h2 id="report-title" className="truncate text-xl font-extrabold">Respuestas del formulario</h2>
          </div>
          <div className="iip-no-print flex items-center gap-2">
            <button type="button" onClick={() => window.print()} className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-4 py-2.5 text-sm font-extrabold text-iip-ink hover:bg-iip-yellow-600">
              <Download className="h-4 w-4" aria-hidden="true" /> Exportar PDF
            </button>
            <button type="button" onClick={onClose} aria-label="Cerrar" className="iip-focus rounded-xl p-2.5 text-white hover:bg-white/10">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto p-5 sm:p-7">
          <dl className="grid gap-2 rounded-2xl bg-iip-bg p-4 text-sm sm:grid-cols-3">
            <div><dt className="text-xs font-bold uppercase text-iip-muted">Entidad</dt><dd className="font-semibold">{entityLabel}</dd></div>
            <div><dt className="text-xs font-bold uppercase text-iip-muted">Formulario</dt><dd className="font-semibold">{form.label}</dd></div>
            <div><dt className="text-xs font-bold uppercase text-iip-muted">Fecha</dt><dd className="font-semibold">{today}</dd></div>
          </dl>

          {components.map(({ component }) => (
            <section key={component.id} className="space-y-4">
              <h3 className="border-b-2 border-iip-yellow pb-1 text-lg font-extrabold">Componente {compNumber(component.id)} · {component.label}</h3>
              {refs.filter((r) => r.component.id === component.id).map((r, k, list) => {
                const numbering = numberQuestions(r.indicator.questions ?? []);
                const firstOfVariable = k === 0 || list[k - 1].variable.id !== r.variable.id;
                return (
                  <div key={r.indicator.id} className="iip-avoid-break space-y-3">
                    {firstOfVariable && <p className="inline-block rounded-lg bg-iip-yellow px-2.5 py-1 text-sm font-extrabold">{r.variable.label}</p>}
                    <div className="rounded-2xl border border-iip-line p-4">
                      <h4 className="text-[15px] font-extrabold">{r.indicator.label}</h4>
                      <ol className="mt-3 space-y-3">
                        {activeQuestions(r.indicator, state.answers).map((q) => (
                          <li key={q.id} className="text-sm">
                            <p className="font-semibold text-iip-muted">{numbering[q.id]}. {q.label}</p>
                            {q.card_template.is_repeatable ? (
                              (state.cardEntries[q.id] ?? []).length === 0 ? (
                                <Value text="" />
                              ) : (
                                <ul className="mt-1 space-y-2">
                                  {(state.cardEntries[q.id] ?? []).map((e, i) => (
                                    <li key={e.id} className="rounded-xl bg-iip-bg p-3">
                                      <p className="font-bold">#{i + 1} {e.title}</p>
                                      <dl className="mt-1 space-y-1">
                                        {visibleFields(q).map((f) => (
                                          <div key={f.id}><dt className="inline text-iip-muted">{f.label}: </dt><dd className="inline"><Value text={answerText(f, e.answers[f.id])} /></dd></div>
                                        ))}
                                      </dl>
                                    </li>
                                  ))}
                                </ul>
                              )
                            ) : (
                              <div className="mt-0.5 space-y-0.5">
                                {visibleFields(q).map((f) => (
                                  <p key={f.id}>
                                    {visibleFields(q).length > 1 && f.label && <span className="text-iip-muted">{f.label}: </span>}
                                    <Value text={answerText(f, state.answers[f.id])} />
                                  </p>
                                ))}
                              </div>
                            )}
                          </li>
                        ))}
                      </ol>
                    </div>
                  </div>
                );
              })}
            </section>
          ))}
        </div>
      </div>
    </div>,
    document.body
  );
};
