import React from 'react';
import { Check } from 'lucide-react';
import { FormIcon } from '../../common/formIcons';
import { AnswerState, IndicatorRef, progressOf, refsOfComponent, refsOfVariable } from '../../../utils/guidedForm';
import { IipProgress } from './ProgressBar';

interface Props {
  refs: IndicatorRef[];
  current: IndicatorRef;
  state: AnswerState;
  /** Posición (1-based) de cada componente dentro del formulario completo. */
  componentNumber: (componentId: string) => number;
  onGo: (index: number) => void;
}

/** Panel lateral: componente activo con su progreso, y sus variables. */
export const ComponentSidebar: React.FC<Props> = ({ refs, current, state, componentNumber, onGo }) => {
  const component = current.component;
  const compRefs = refsOfComponent(refs, component.id);
  const compPct = progressOf(compRefs, state);

  const variables = compRefs.filter((r, i, all) => all.findIndex((x) => x.variable.id === r.variable.id) === i);
  const components = refs.filter((r, i, all) => all.findIndex((x) => x.component.id === r.component.id) === i);

  return (
    <aside aria-label="Componente y variables" className="rounded-3xl border border-iip-line bg-white p-4 shadow-sm sm:p-5">
      <div className="rounded-2xl bg-iip-bg p-4">
        <div className="flex items-start gap-3">
          <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-iip-navy text-white">
            <FormIcon name={component.icon_name} className="h-7 w-7" />
          </span>
          <div className="min-w-0">
            <p className="text-xl font-extrabold leading-tight text-iip-ink">Componente {componentNumber(component.id)}</p>
            <p className="text-lg font-semibold leading-snug text-iip-ink">{component.label}</p>
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm font-semibold text-iip-ink">Progreso del componente</p>
          <div className="mt-1 flex items-center gap-3">
            <IipProgress value={compPct} label={`Progreso del componente ${component.label}`} />
            <span className="w-12 text-right text-sm font-bold text-iip-ink">{compPct}%</span>
          </div>
        </div>
      </div>

      <nav aria-label="Variables del componente" className="mt-4">
        <ul className="space-y-1.5 rounded-2xl bg-white">
          {variables.map((v, i) => {
            const vRefs = refsOfVariable(refs, v.variable.id);
            const active = v.variable.id === current.variable.id;
            const done = vRefs.length > 0 && progressOf(vRefs, state) === 100;
            return (
              <li key={v.variable.id}>
                <button
                  type="button"
                  onClick={() => onGo(vRefs[0].index)}
                  aria-current={active ? 'step' : undefined}
                  className={`iip-focus flex w-full items-center gap-3 rounded-xl px-3.5 py-3 text-left text-[15px] transition-colors ${
                    active ? 'bg-iip-yellow font-bold text-iip-ink' : 'text-iip-ink hover:bg-iip-bg'
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                      done ? 'border-iip-green bg-iip-green text-white' : active ? 'border-iip-ink bg-iip-yellow' : 'border-slate-400'
                    }`}
                  >
                    {done ? <Check className="h-3.5 w-3.5" /> : active ? <span className="h-2.5 w-2.5 rounded-full bg-iip-ink" /> : null}
                  </span>
                  <span className="min-w-0 flex-1 truncate">Variable {i + 1}</span>
                  {done && <span className="sr-only">completa</span>}
                </button>
                {active && <p className="px-3.5 pb-1 pt-1.5 text-sm text-iip-muted">{v.variable.label}</p>}
              </li>
            );
          })}
        </ul>
      </nav>

      {components.length > 1 && (
        <nav aria-label="Componentes elegidos" className="mt-4 border-t border-iip-line pt-4">
          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-iip-muted">Componentes elegidos</p>
          <ul className="flex flex-wrap gap-2">
            {components.map((c) => (
              <li key={c.component.id}>
                <button
                  type="button"
                  onClick={() => onGo(c.index)}
                  aria-current={c.component.id === component.id ? 'step' : undefined}
                  title={c.component.label}
                  className={`iip-focus rounded-lg border px-3 py-1.5 text-sm font-bold ${
                    c.component.id === component.id ? 'border-iip-navy bg-iip-navy text-white' : 'border-iip-line bg-white text-iip-ink hover:bg-iip-bg'
                  }`}
                >
                  C{componentNumber(c.component.id)}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </aside>
  );
};
