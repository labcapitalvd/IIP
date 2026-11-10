import React from 'react';
import { Check } from 'lucide-react';

export type WizardStage = 'info' | 'components' | 'fill' | 'review' | 'done';

export const STAGES: { id: WizardStage; label: string }[] = [
  { id: 'info', label: 'Información general' },
  { id: 'components', label: 'Componentes' },
  { id: 'fill', label: 'Diligenciamiento' },
  { id: 'review', label: 'Revisión' },
  { id: 'done', label: 'Envío' },
];

interface StepperProps {
  current: WizardStage;
  /** Etapas a las que se puede volver (ya recorridas). */
  onGo: (stage: WizardStage) => void;
  canGo: (stage: WizardStage) => boolean;
}

export const Stepper: React.FC<StepperProps> = ({ current, onGo, canGo }) => {
  const currentIdx = STAGES.findIndex((s) => s.id === current);
  return (
    <nav aria-label="Etapas del diligenciamiento" className="bg-white px-4 pb-3 pt-4 sm:px-6">
      <ol className="mx-auto flex max-w-5xl items-start">
        {STAGES.map((s, i) => {
          const done = i < currentIdx;
          const active = i === currentIdx;
          const clickable = !active && canGo(s.id);
          return (
            <li key={s.id} className="relative flex flex-1 flex-col items-center">
              {i > 0 && (
                <span
                  className={`absolute right-1/2 top-[18px] h-0.5 w-full ${i <= currentIdx ? (i === currentIdx ? 'bg-iip-yellow' : 'bg-iip-green') : 'bg-slate-300'}`}
                  aria-hidden="true"
                />
              )}
              <button
                type="button"
                disabled={!clickable}
                onClick={() => onGo(s.id)}
                aria-current={active ? 'step' : undefined}
                className="iip-focus relative z-10 flex flex-col items-center gap-1.5 rounded-lg disabled:cursor-default"
              >
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold ${
                    done ? 'bg-iip-green text-white' : active ? 'bg-iip-yellow text-iip-ink ring-4 ring-iip-yellow/30' : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {done ? <Check className="h-5 w-5" aria-hidden="true" /> : i + 1}
                </span>
                <span className={`hidden text-center text-sm sm:block ${active ? 'font-bold text-iip-ink' : 'text-iip-muted'}`}>{s.label}</span>
                <span className="sr-only sm:hidden">{s.label}</span>
              </button>
            </li>
          );
        })}
      </ol>
      <p className="mt-1 text-center text-xs font-bold text-iip-ink sm:hidden">{STAGES[currentIdx].label}</p>
    </nav>
  );
};
