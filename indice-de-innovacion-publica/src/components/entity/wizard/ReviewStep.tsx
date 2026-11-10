import React from 'react';
import { AlertCircle, ArrowLeft, CheckCircle2, Circle, Send } from 'lucide-react';
import { AnswerState, IndicatorRef, indicatorProgress, progressOf } from '../../../utils/guidedForm';
import { IipProgress } from './ProgressBar';

interface Props {
  refs: IndicatorRef[];
  state: AnswerState;
  componentNumber: (componentId: string) => number;
  onEdit: (index: number) => void;
  onBack: () => void;
  onSubmit: () => void;
}

/** Etapa 4: revisión por indicador; el envío solo se habilita con todos completos. */
export const ReviewStep: React.FC<Props> = ({ refs, state, componentNumber, onEdit, onBack, onSubmit }) => {
  const pending = refs.filter((r) => !indicatorProgress(r.indicator, state).complete);
  const pct = progressOf(refs, state);
  const components = refs.filter((r, i, all) => all.findIndex((x) => x.component.id === r.component.id) === i).map((r) => r.component);

  return (
    <section aria-labelledby="rev-title" className="mx-auto w-full max-w-4xl rounded-3xl border border-iip-line bg-white p-5 shadow-sm sm:p-8">
      <h2 id="rev-title" className="text-2xl font-extrabold text-iip-ink">Revisión antes del envío</h2>
      <div className="mt-3 flex items-center gap-3">
        <IipProgress value={pct} label="Indicadores completos" tone={pending.length ? 'yellow' : 'green'} />
        <span className="w-12 text-right text-sm font-bold text-iip-ink">{pct}%</span>
      </div>

      {pending.length > 0 ? (
        <p role="status" className="mt-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Faltan {pending.length} indicador(es) por completar. Use «Completar» para ir a cada uno.
        </p>
      ) : (
        <p role="status" className="mt-4 flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-900">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Todos los indicadores están completos. Ya puede enviar el formulario.
        </p>
      )}

      <div className="mt-6 space-y-6">
        {components.map((c) => (
          <div key={c.id}>
            <h3 className="text-lg font-extrabold text-iip-ink">Componente {componentNumber(c.id)} · {c.label}</h3>
            <ul className="mt-2 divide-y divide-iip-line rounded-2xl border border-iip-line">
              {refs.filter((r) => r.component.id === c.id).map((r) => {
                const ok = indicatorProgress(r.indicator, state).complete;
                return (
                  <li key={r.indicator.id} className="flex items-center gap-3 px-4 py-3">
                    {ok ? <CheckCircle2 className="h-5 w-5 shrink-0 text-iip-green" aria-label="Completo" /> : <Circle className="h-5 w-5 shrink-0 text-slate-400" aria-label="Pendiente" />}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[15px] font-semibold text-iip-ink">{r.indicator.label}</p>
                      <p className="truncate text-xs text-iip-muted">{r.variable.label}</p>
                    </div>
                    <button type="button" onClick={() => onEdit(r.index)} className="iip-focus shrink-0 rounded-lg px-3 py-1.5 text-sm font-bold text-iip-navy-700 hover:bg-iip-sky">
                      {ok ? 'Editar' : 'Completar'}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
        <button type="button" onClick={onBack} className="iip-focus flex items-center gap-2 rounded-xl border-2 border-iip-line px-5 py-3 text-[15px] font-bold text-iip-ink hover:bg-iip-bg">
          <ArrowLeft className="h-5 w-5" aria-hidden="true" /> Volver al diligenciamiento
        </button>
        <button type="button" onClick={onSubmit} disabled={pending.length > 0} className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-6 py-3 text-[15px] font-extrabold text-iip-ink shadow-sm hover:bg-iip-yellow-600 disabled:cursor-not-allowed disabled:opacity-50">
          <Send className="h-5 w-5" aria-hidden="true" /> Revisar y enviar
        </button>
      </div>
    </section>
  );
};
