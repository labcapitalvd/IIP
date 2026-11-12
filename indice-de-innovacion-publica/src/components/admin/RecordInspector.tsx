import React, { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Award, BarChart3, Layers, Loader2, Rocket, Trash2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { coreService } from '../../services/coreService';
import { EntityResults, EntitySubmission, FormQuestion, FormSection, IIPForm, MonitorRecord } from '../../types';
import { ROUTES, navigate } from '../../utils/router';
import { deleteSubmissionWithConfirm } from '../../utils/deleteSubmissionFlow';
import { getIndicators, getVariables, kindOf, numberQuestions, questionFields } from '../../utils/formTree';

const fmt = (n: number) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 4 }).format(n);

interface Loaded {
  form: IIPForm;
  record: MonitorRecord | null;
  results: EntityResults;
  submission: EntitySubmission | null;
}

/**
 * Pantalla de una entidad en un formulario: su resultado estadístico (el que se cargó) y sus
 * respuestas, organizados por componente, variable, indicador y pregunta.
 */
export const RecordInspector: React.FC<{ formId: string; actorId: string }> = ({ formId, actorId }) => {
  const { deleteSubmission } = useApp();
  const [data, setData] = useState<Loaded | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [form, records, results] = await Promise.all([
        coreService.getForm(formId),
        coreService.listRecords(),
        coreService.getEntityResults(formId, actorId),
      ]);
      const record = records.find((r) => r.form_id === formId && r.actor_id === actorId) ?? null;
      const submission = record?.submission_id ? await coreService.getSubmission(record.submission_id) : null;
      setData({ form, record, results, submission });
    } catch (err: any) {
      setError(err?.message || 'No se pudo cargar la información.');
    }
  }, [formId, actorId]);

  useEffect(() => {
    setData(null);
    void load();
  }, [load]);

  const back = () => navigate(ROUTES.admin.submissions);

  const handleDelete = async () => {
    const sub = data?.submission;
    if (!sub || !data?.record) return;
    setDeleting(true);
    try {
      if (await deleteSubmissionWithConfirm(deleteSubmission, sub.id, data.record.actor_label, data.record.form_code)) {
        await load();
      }
    } catch (err: any) {
      setError(err?.message || 'No se pudo eliminar el radicado.');
    } finally {
      setDeleting(false);
    }
  };

  if (error && !data) {
    return (
      <Shell onBack={back}>
        <div className="p-4 rounded-2xl border bg-rose-50 border-rose-200 text-rose-800 text-xs">{error}</div>
      </Shell>
    );
  }
  if (!data) {
    return (
      <Shell onBack={back}>
        <div className="p-10 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" /> Cargando…
        </div>
      </Shell>
    );
  }

  const { form, record, results, submission } = data;
  const scores = new Map(results.sections.map((s) => [s.section_id, s.score ?? null]));
  const qScores = new Map((results.questions ?? []).map((q) => [q.question_id, q.score ?? null]));
  const scoreOfQ = (q: FormQuestion) => (qScores.has(q.id) ? qScores.get(q.id) ?? null : undefined);
  const scoreOf = (s: FormSection) => (scores.has(s.id) ? scores.get(s.id) ?? null : undefined);

  return (
    <Shell onBack={back}>
      {error && <div className="p-3 rounded-xl border bg-rose-50 border-rose-200 text-rose-800 text-xs">{error}</div>}

      {/* Encabezado */}
      <div className="bg-slate-900 text-white rounded-3xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Entidad × formulario</span>
          <h2 className="text-xl font-bold mt-0.5">{record?.actor_label ?? 'Entidad'}</h2>
          {record?.actor_segment_label && <p className="text-xs text-slate-400">{record.actor_segment_label}</p>}
          <p className="text-xs text-slate-300 mt-2">
            {form.label} <span className="font-mono text-slate-400">({form.code})</span>
          </p>
        </div>
        <div className="flex flex-col items-start sm:items-end gap-2">
          {submission ? (
            <span
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold ${
                submission.status === 'draft' ? 'bg-amber-400/20 text-amber-200' : 'bg-emerald-400/20 text-emerald-200'
              }`}
            >
              {submission.status === 'draft' ? 'Borrador' : 'Enviado'} ·{' '}
              {new Date(submission.submitted_at).toLocaleString()}
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-white/10 text-slate-300">
              Sin respuestas cargadas
            </span>
          )}
          {submission && (
            <button
              disabled={deleting}
              onClick={() => void handleDelete()}
              className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-rose-500/30 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-60"
            >
              {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
              Eliminar respuestas
            </button>
          )}
        </div>
      </div>

      {/* Resultado estadístico */}
      <section className="bg-white rounded-3xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-3">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-indigo-600" />
            Resultado estadístico cargado
          </h3>
          {results.has_results && results.updated_at && (
            <span className="text-[11px] text-slate-400">
              Cargado el {new Date(results.updated_at).toLocaleDateString()}
            </span>
          )}
        </div>
        {!results.has_results ? (
          <p className="px-6 py-8 text-xs text-slate-400 italic">
            Esta entidad no tiene resultado cargado para este formulario. Se carga desde «Cargas históricas».
          </p>
        ) : (
          <div className="p-6 space-y-4">
            <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-600 text-white rounded-xl">
                  <Award className="w-6 h-6" />
                </div>
                <span className="text-xs font-bold text-emerald-900">Total</span>
              </div>
              <div className="text-2xl font-black text-emerald-700 font-mono">
                {results.total != null ? fmt(results.total) : '—'}
              </div>
            </div>

            <div className="space-y-1">
              {form.sections.map((c) => (
                <div key={c.id}>
                  <ScoreRow depth={0} kind="Componente" section={c} score={scoreOf(c)} />
                  {getVariables(c).map((v) => (
                    <div key={v.id}>
                      <ScoreRow depth={1} kind="Variable" section={v} score={scoreOf(v)} />
                      {getIndicators(v).map((i) => (
                        <div key={i.id}>
                          <ScoreRow depth={2} kind="Indicador" section={i} score={scoreOf(i)} />
                          {(i.questions ?? []).map((q) => (
                            <ScoreRow key={q.id} depth={3} kind="Pregunta" section={{ label: `${q.code ? q.code + '. ' : ''}${q.label}` }} score={scoreOfQ(q)} />
                          ))}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Respuestas */}
      <section className="bg-white rounded-3xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            Respuestas de la entidad
          </h3>
        </div>
        {!submission ? (
          <p className="px-6 py-8 text-xs text-slate-400 italic">
            Esta entidad no tiene respuestas cargadas para este formulario.
          </p>
        ) : (
          <div className="p-6 space-y-6">
            {form.sections.map((c, ci) => (
              <div key={c.id} className="space-y-4">
                <h4 className="text-sm font-black text-slate-900 border-b border-slate-200 pb-1">
                  Componente {ci + 1}. {c.label}
                </h4>
                {getVariables(c).map((v, vi) => (
                  <div key={v.id} className="space-y-3 pl-3 border-l-2 border-indigo-100">
                    <h5 className="text-xs font-bold text-indigo-900">
                      Variable {ci + 1}.{vi + 1} · {v.label}
                    </h5>
                    {getIndicators(v).map((ind, ii) => {
                      const qs = ind.questions ?? [];
                      const nums = numberQuestions(qs);
                      return (
                        <div key={ind.id} className="space-y-2 pl-3">
                          <h6 className="text-xs font-bold text-slate-700">
                            Indicador {ci + 1}.{vi + 1}.{ii + 1} · {ind.label}
                          </h6>
                          {qs.map((q) => (
                            <QuestionAnswer key={q.id} q={q} number={nums[q.id]} submission={submission} />
                          ))}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </section>
    </Shell>
  );
};

const Shell: React.FC<{ onBack: () => void; children: React.ReactNode }> = ({ onBack, children }) => (
  <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
    <button
      onClick={onBack}
      className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1.5"
    >
      <ArrowLeft className="w-4 h-4" />
      Volver al monitor
    </button>
    {children}
  </div>
);

const ScoreRow: React.FC<{
  depth: number;
  kind: string;
  section: { label: string };
  score: number | null | undefined;
}> = ({ depth, kind, section, score }) => (
  <div
    className={`flex items-center justify-between gap-3 py-1.5 px-3 rounded-lg text-xs ${
      depth === 0 ? 'bg-slate-100 font-bold' : depth === 1 ? 'font-semibold' : 'text-slate-600'
    }`}
    style={{ marginLeft: depth * 20 }}
  >
    <span className="min-w-0 truncate">
      <span className="text-[10px] uppercase tracking-wider text-slate-400 mr-2">{kind}</span>
      {section.label}
    </span>
    <span className={`font-mono shrink-0 ${score == null ? 'text-slate-300' : 'text-slate-900'}`}>
      {score == null ? '—' : fmt(score)}
    </span>
  </div>
);

const QuestionAnswer: React.FC<{ q: FormQuestion; number: string; submission: EntitySubmission }> = ({
  q,
  number,
  submission,
}) => {
  const fields = questionFields(q);
  const isLoop = kindOf(q) === 'loop';
  const cards = isLoop ? submission.card_entries?.[q.id] ?? [] : [];

  return (
    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-2 text-xs">
      <div className="font-semibold text-slate-900">
        <span className="text-slate-400 mr-1.5">{number}.</span>
        {q.label}
      </div>

      {isLoop ? (
        cards.length === 0 ? (
          <p className="text-slate-400 italic">Sin tarjetas registradas.</p>
        ) : (
          <div className="space-y-2">
            {cards.map((card, idx) => (
              <div key={card.id} className="bg-white rounded-xl border border-slate-200 p-3 space-y-2">
                <div className="flex flex-wrap items-center gap-2 font-bold text-slate-900">
                  <Rocket className="w-3.5 h-3.5 text-indigo-600" />
                  #{idx + 1}: {card.title}
                  {card.parent_title && (
                    <span className="text-[10px] font-semibold text-sky-700 bg-sky-50 border border-sky-200 px-1.5 py-0.5 rounded">
                      Referencia: {card.parent_title}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {fields.map((f) => (
                    <div key={f.id} className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                      <span className="text-[10px] text-slate-400 block">{f.label}</span>
                      <span className="font-medium text-slate-800">
                        {card.display?.[f.id] || <em className="text-slate-300 font-normal">Sin respuesta</em>}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {fields.map((f) => (
            <div key={f.id} className="bg-white p-2 rounded-lg border border-slate-100">
              {fields.length > 1 && <span className="text-[10px] text-slate-400 block">{f.label}</span>}
              <span className="font-medium text-slate-800">
                {submission.display_values?.[f.id] || <em className="text-slate-300 font-normal">Sin respuesta</em>}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
