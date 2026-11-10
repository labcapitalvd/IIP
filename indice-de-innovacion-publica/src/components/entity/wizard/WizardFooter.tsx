import React from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, Loader2, Save } from 'lucide-react';
import { IipProgress } from './ProgressBar';

interface Props {
  position: number;
  total: number;
  progress: number;
  isFirst: boolean;
  isLast: boolean;
  isSaving: boolean;
  savedAt: Date | null;
  saveError: string | null;
  onPrev: () => void;
  onNext: () => void;
  onSave: () => void;
}

const time = (d: Date) => d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });

export const WizardFooter: React.FC<Props> = ({ position, total, progress, isFirst, isLast, isSaving, savedAt, saveError, onPrev, onNext, onSave }) => (
  <footer className="sticky bottom-0 z-20 border-t border-iip-line bg-white/95 backdrop-blur">
    <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-x-4 gap-y-1.5 px-4 py-1.5 sm:px-6">
      <button
        type="button"
        onClick={onPrev}
        disabled={isFirst}
        className="iip-focus flex items-center gap-2 rounded-xl border-2 border-iip-line bg-white px-3.5 py-1.5 text-sm font-bold text-iip-ink hover:bg-iip-bg disabled:cursor-not-allowed disabled:opacity-40"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Anterior
      </button>

      <div className="order-last w-full min-w-0 flex-1 basis-full md:order-none md:basis-auto">
        <p className="text-sm font-semibold text-iip-ink">Indicador {position} de {total}</p>
        <div className="flex items-center gap-3">
          <IipProgress value={progress} label="Progreso del diligenciamiento" />
          <span className="w-12 text-right text-sm font-bold text-iip-ink">{progress}%</span>
        </div>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <div className="hidden text-right text-xs sm:block" role="status" aria-live="polite">
          {saveError ? (
            <span className="font-semibold text-rose-700">{saveError}</span>
          ) : savedAt ? (
            <span className="flex items-center gap-1 font-semibold text-iip-green"><CheckCircle2 className="h-4 w-4" aria-hidden="true" /> Borrador guardado {time(savedAt)}</span>
          ) : null}
        </div>
        <button
          type="button"
          onClick={onSave}
          disabled={isSaving}
          className="iip-focus flex items-center gap-2 rounded-xl border-2 border-iip-line bg-white px-3.5 py-1.5 text-sm font-bold text-iip-ink hover:bg-iip-bg disabled:opacity-60"
        >
          {isSaving ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Save className="h-4 w-4" aria-hidden="true" />}
          {isSaving ? 'Guardando…' : 'Guardar borrador'}
        </button>
        <button
          type="button"
          onClick={onNext}
          className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-4 py-1.5 text-sm font-extrabold text-iip-ink shadow-sm hover:bg-iip-yellow-600"
        >
          {isLast ? 'Ir a revisión' : 'Siguiente'} <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
    <p className="sr-only" role="status" aria-live="polite">{saveError ?? (savedAt ? `Borrador guardado a las ${time(savedAt)}` : '')}</p>
  </footer>
);
