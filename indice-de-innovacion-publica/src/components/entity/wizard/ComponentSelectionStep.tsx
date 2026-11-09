import React, { useState } from 'react';
import { AlertCircle, ArrowRight, Check, Loader2 } from 'lucide-react';
import { FormIcon } from '../../common/formIcons';
import { FormSection } from '../../../types';
import { getIndicators, getVariables } from '../../../utils/formTree';
import { AnswerState, buildIndicatorRefs, progressOf, refsOfComponent } from '../../../utils/guidedForm';
import { IipProgress } from './ProgressBar';

interface Props {
  components: FormSection[];
  initialSelected: string[];
  state: AnswerState;
  onConfirm: (ids: string[]) => Promise<void>;
}

/** Etapa 2: la entidad elige los componentes del formulario que debe responder. */
export const ComponentSelectionStep: React.FC<Props> = ({ components, initialSelected, state, onConfirm }) => {
  const [selected, setSelected] = useState<string[]>(initialSelected);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (id: string) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const allOn = selected.length === components.length;

  const confirm = async () => {
    setSaving(true);
    setError(null);
    try {
      // Se conserva el orden del formulario, no el orden de clic.
      await onConfirm(components.filter((c) => selected.includes(c.id)).map((c) => c.id));
    } catch (e: any) {
      setError(e?.message || 'No se pudo guardar la selección. Intente de nuevo.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section aria-labelledby="sel-title" className="mx-auto w-full max-w-5xl rounded-3xl border border-iip-line bg-white p-5 shadow-sm sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="sel-title" className="text-2xl font-extrabold text-iip-ink">¿Qué componentes va a responder?</h2>
          <p className="mt-1 text-[15px] text-iip-muted">Seleccione uno o más componentes. Solo se le pedirá diligenciar los elegidos; podrá cambiar la selección más adelante.</p>
        </div>
        <button type="button" onClick={() => setSelected(allOn ? [] : components.map((c) => c.id))} className="iip-focus rounded-xl border-2 border-iip-line px-4 py-2 text-sm font-bold text-iip-ink hover:bg-iip-bg">
          {allOn ? 'Quitar todos' : 'Seleccionar todos'}
        </button>
      </div>

      <ul className="mt-6 grid gap-4 md:grid-cols-2" role="group" aria-label="Componentes del formulario">
        {components.map((c, i) => {
          const on = selected.includes(c.id);
          const variables = getVariables(c);
          const indicators = variables.reduce((n, v) => n + (getIndicators(v).length || (v.questions?.length ? 1 : 0)), 0);
          const pct = progressOf(refsOfComponent(buildIndicatorRefs({ sections: components } as any, [c.id]), c.id), state);
          return (
            <li key={c.id}>
              <label
                className={`flex h-full cursor-pointer gap-4 rounded-2xl border-2 p-4 transition-colors has-[input:focus-visible]:outline-3 has-[input:focus-visible]:outline-offset-2 has-[input:focus-visible]:outline-iip-navy-700 ${
                  on ? 'border-iip-navy bg-iip-sky' : 'border-iip-line bg-white hover:border-iip-navy-700/40'
                }`}
              >
                <input type="checkbox" checked={on} onChange={() => toggle(c.id)} className="sr-only" />
                <span className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ${on ? 'bg-iip-navy text-white' : 'bg-iip-bg text-iip-navy'}`}>
                  <FormIcon name={c.icon_name} className="h-7 w-7" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-bold text-iip-muted">Componente {i + 1}</span>
                  <span className="block text-lg font-extrabold leading-snug text-iip-ink">{c.label}</span>
                  {c.description && <span className="mt-1 line-clamp-3 block text-sm text-iip-muted">{c.description}</span>}
                  <span className="mt-2 block text-xs font-semibold text-iip-ink">{variables.length} variable(s) · {indicators} indicador(es)</span>
                  {pct > 0 && (
                    <span className="mt-2 flex items-center gap-2">
                      <IipProgress value={pct} label={`Avance de ${c.label}`} className="!h-2" />
                      <span className="text-xs font-bold text-iip-ink">{pct}%</span>
                    </span>
                  )}
                </span>
                <span aria-hidden="true" className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border-2 ${on ? 'border-iip-navy bg-iip-navy text-white' : 'border-slate-400 bg-white'}`}>
                  {on && <Check className="h-4 w-4" />}
                </span>
              </label>
            </li>
          );
        })}
      </ul>

      {error && (
        <p role="alert" className="mt-4 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-semibold text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" /> {error}
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-semibold text-iip-ink" role="status" aria-live="polite">{selected.length} de {components.length} componente(s) seleccionado(s)</p>
        <button
          type="button"
          onClick={confirm}
          disabled={selected.length === 0 || saving}
          className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-6 py-3 text-[15px] font-extrabold text-iip-ink shadow-sm hover:bg-iip-yellow-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> : null}
          {saving ? 'Guardando…' : 'Continuar al diligenciamiento'} {!saving && <ArrowRight className="h-5 w-5" aria-hidden="true" />}
        </button>
      </div>
    </section>
  );
};
