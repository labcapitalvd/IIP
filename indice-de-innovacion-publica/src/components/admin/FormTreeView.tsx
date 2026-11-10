import React, { useState } from 'react';
import { IIPForm, FormQuestion } from '../../types';
import { ChevronDown, ChevronRight, CornerDownRight, Link2, Repeat } from 'lucide-react';
import { FormIcon } from '../common/formIcons';
import {
  QUESTION_KINDS,
  formatWeight,
  getIndicators,
  getVariables,
  kindOf,
  numberQuestions,
  questionFields,
  sectionWeight,
} from '../../utils/formTree';

const kindLabel = (q: FormQuestion) => QUESTION_KINDS.find((k) => k.value === kindOf(q))?.label ?? '';

/** Vista de solo lectura: Componentes → Variables → Indicadores → Preguntas (con su peso). */
export const FormTreeView: React.FC<{ form: IIPForm }> = ({ form }) => {
  const [open, setOpen] = useState<Record<string, boolean>>({ [form.sections[0]?.id ?? '']: true });
  const allQs = form.sections.flatMap((c) =>
    (c.children ?? []).flatMap((v) => (v.children ?? []).flatMap((i) => i.questions ?? []))
  );
  const sourceLabel = (id: string) => allQs.find((x) => x.id === id)?.label || 'pregunta eliminada';

  const toggle = (id: string) => setOpen((o) => ({ ...o, [id]: !o[id] }));
  const weightTag = (w: number) => (
    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
      {formatWeight(w)} pts
    </span>
  );

  return (
    <div className="space-y-3">
      {form.sections.map((c, ci) => {
        const vars = getVariables(c);
        const cOpen = !!open[c.id];
        return (
          <div key={c.id} className="rounded-2xl border border-slate-300 overflow-hidden bg-white">
            <button
              type="button"
              onClick={() => toggle(c.id)}
              className="w-full p-4 bg-slate-900 text-white hover:bg-slate-800 flex items-center gap-3 text-left"
            >
              <div className="w-9 h-9 rounded-xl bg-amber-500 text-slate-950 flex items-center justify-center shrink-0">
                <FormIcon name={c.icon_name} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-300">
                  Componente {ci + 1} • {vars.length} variable(s)
                </div>
                <div className="font-bold text-sm truncate">{c.label}</div>
              </div>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white/15 shrink-0">
                {formatWeight(sectionWeight(c))} pts
              </span>
              {cOpen ? <ChevronDown className="w-4 h-4 text-slate-300" /> : <ChevronRight className="w-4 h-4 text-slate-300" />}
            </button>

            {cOpen && (
              <div className="p-3 space-y-3 border-t border-slate-200">
                {c.description && <p className="text-xs text-slate-600">{c.description}</p>}
                {vars.map((v, vi) => {
                  const inds = getIndicators(v);
                  const isOpen = !!open[v.id];
                  return (
                    <div key={v.id} className="rounded-2xl border border-slate-200 overflow-hidden bg-white">
                      <button
                        type="button"
                        onClick={() => toggle(v.id)}
                        className="w-full p-3 bg-slate-50 hover:bg-slate-100/80 flex items-center gap-3 text-left"
                      >
                        <div className="w-8 h-8 rounded-xl bg-slate-200 text-amber-700 flex items-center justify-center shrink-0">
                          <FormIcon name={v.icon_name} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                            Variable {ci + 1}.{vi + 1} • {inds.length} indicador(es)
                          </div>
                          <div className="font-bold text-sm text-slate-900 truncate">{v.label}</div>
                        </div>
                        {weightTag(sectionWeight(v))}
                        {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                      </button>

                      {isOpen && (
                        <div className="p-4 space-y-4 border-t border-slate-200">
                          {(v.description || v.help_text) && (
                            <div className="text-xs text-slate-600 bg-amber-50/50 border border-amber-100 rounded-xl p-3 space-y-1">
                              {v.description && <p>{v.description}</p>}
                              {v.help_text && <p className="italic text-slate-500">Ayuda: {v.help_text}</p>}
                            </div>
                          )}

                          {inds.map((ind, ii) => {
                            const qs = ind.questions ?? [];
                            const nums = numberQuestions(qs);
                            return (
                              <div key={ind.id} className="rounded-xl border border-slate-200 p-4 space-y-3">
                                <div className="flex items-center gap-2">
                                  <FormIcon name={ind.icon_name} className="w-4 h-4 text-amber-600" />
                                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                                    Indicador {ci + 1}.{vi + 1}.{ii + 1}
                                  </div>
                                  <div className="font-bold text-xs text-slate-900 flex-1 min-w-0 truncate">{ind.label}</div>
                                  {weightTag(sectionWeight(ind))}
                                </div>
                                {(ind.description || ind.help_text) && (
                                  <p className="text-[11px] text-slate-500">
                                    {ind.description} {ind.help_text && <em>— {ind.help_text}</em>}
                                  </p>
                                )}

                                <div className="space-y-2">
                                  {qs.map((q) => {
                                    const isLoop = kindOf(q) === 'loop';
                                    const parent = q.depends_on && qs.find((p) => p.id === q.depends_on!.question_id);
                                    return (
                                      <div
                                        key={q.id}
                                        className={`rounded-xl border p-3 text-xs space-y-1.5 ${
                                          isLoop ? 'ml-6 bg-amber-50/40 border-amber-200' : 'bg-slate-50 border-slate-200'
                                        }`}
                                      >
                                        <div className="flex items-start gap-2">
                                          <span className="font-black text-slate-500 shrink-0">{nums[q.id]}.</span>
                                          <span className="flex-1 font-semibold text-slate-900">{q.label}</span>
                                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-600 shrink-0">
                                            {kindLabel(q)}
                                          </span>
                                          {weightTag(q.weight ?? 0)}
                                        </div>
                                        {parent && (
                                          <div className="flex items-center gap-1 text-[11px] text-amber-800">
                                            <CornerDownRight className="w-3 h-3" />
                                            Si la pregunta {nums[parent.id]} es {q.depends_on!.value ? 'Sí' : 'No'}; de lo contrario continúa.
                                          </div>
                                        )}
                                        {isLoop && q.source_question_id && (
                                          <div className="flex items-center gap-1 text-[11px] text-sky-800">
                                            <Link2 className="w-3 h-3" />
                                            Cada tarjeta se refiere a una tarjeta de: {sourceLabel(q.source_question_id)}
                                          </div>
                                        )}
                                        {isLoop && (
                                          <div className="flex flex-wrap items-center gap-1.5">
                                            <Repeat className="w-3 h-3 text-slate-400" />
                                            {questionFields(q).map((f) => (
                                              <span key={f.id} className="px-2 py-0.5 bg-white border border-slate-200 rounded text-[10px] text-slate-700">
                                                {f.label} · {f.field_type_code}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                        {!isLoop && questionFields(q)[0]?.choices && (
                                          <div className="flex flex-wrap gap-1">
                                            {questionFields(q)[0].choices!.map((ch) => (
                                              <span key={ch.id} className="px-2 py-0.5 bg-white border border-slate-200 rounded text-[10px] text-slate-700">
                                                {ch.label}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                        {q.help_text && <p className="text-[11px] text-slate-500">Ayuda: {q.help_text}</p>}
                                        {q.grading_guide && (
                                          <p className="text-[11px] text-emerald-800 bg-emerald-50 border border-emerald-100 rounded-lg px-2 py-1">
                                            Guía de calificación: {q.grading_guide}
                                          </p>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
