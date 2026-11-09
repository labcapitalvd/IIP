import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, Building2, CheckCircle2, Info, Loader2, Send, X } from 'lucide-react';
import { useFormSubmission } from '../../context/FormSubmissionContext';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { buildIndicatorRefs, indicatorProgress } from '../../utils/guidedForm';

interface SubmissionReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

/** Confirmación del envío oficial: resumen por componente y acción de enviar. */
export const SubmissionReviewModal: React.FC<SubmissionReviewModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { answers, cardEntries, selectedComponentIds, submitForm, isSubmitting } = useFormSubmission();
  const { activeForm } = useApp();
  const { user } = useAuth();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    setErrorMsg(null);
    panelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && !isSubmitting && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen) return null;

  const refs = buildIndicatorRefs(activeForm, selectedComponentIds);
  const state = { answers, cardEntries };
  const components = refs.filter((r, i, a) => a.findIndex((x) => x.component.id === r.component.id) === i).map((r) => r.component);

  const confirm = async () => {
    setErrorMsg(null);
    try {
      await submitForm();
      onSuccess();
    } catch (err: any) {
      setErrorMsg(err?.message || 'No se pudo enviar el formulario. Verifique su conexión e intente de nuevo.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-iip-ink/70 p-4">
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="flex max-h-[92vh] w-full max-w-2xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl outline-none"
      >
        <div className="flex items-start justify-between gap-3 bg-iip-navy px-6 py-5 text-white">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-iip-yellow">Paso final · Confirmación de envío</p>
            <h2 id="confirm-title" className="mt-0.5 text-xl font-extrabold">¿Enviar el formulario del IIP?</h2>
          </div>
          <button type="button" onClick={onClose} disabled={isSubmitting} aria-label="Cerrar" className="iip-focus rounded-xl p-2 text-white hover:bg-white/10 disabled:opacity-50">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto p-6">
          <div className="flex items-center gap-3 rounded-2xl bg-iip-bg p-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-iip-navy text-white"><Building2 className="h-5 w-5" aria-hidden="true" /></span>
            <div className="min-w-0">
              <p className="truncate font-extrabold text-iip-ink">{user?.actor_label || 'Entidad pública'}</p>
              <p className="truncate text-sm text-iip-muted">{activeForm.label}</p>
            </div>
          </div>

          <ul className="divide-y divide-iip-line rounded-2xl border border-iip-line" aria-label="Resumen por componente">
            {components.map((c) => {
              const cr = refs.filter((r) => r.component.id === c.id);
              const done = cr.filter((r) => indicatorProgress(r.indicator, state).complete).length;
              return (
                <li key={c.id} className="flex items-center gap-3 px-4 py-3">
                  <CheckCircle2 className={`h-5 w-5 shrink-0 ${done === cr.length ? 'text-iip-green' : 'text-slate-300'}`} aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate text-[15px] font-semibold text-iip-ink">{c.label}</span>
                  <span className="shrink-0 text-sm font-bold text-iip-ink">{done}/{cr.length} indicadores</span>
                </li>
              );
            })}
          </ul>

          <p className="flex items-start gap-2 rounded-2xl bg-iip-yellow-50 p-4 text-sm leading-relaxed text-iip-ink">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-iip-yellow-600" aria-hidden="true" />
            Una vez enviado, las modificaciones estarán sujetas a los procedimientos y autorizaciones definidos por los administradores. Al finalizar podrá consultar todas sus respuestas y exportarlas en PDF.
          </p>

          {errorMsg && (
            <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm text-rose-800">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <div><span className="block font-bold">No se pudo enviar</span>{errorMsg}</div>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-iip-line bg-iip-bg px-6 py-4">
          <button type="button" onClick={onClose} disabled={isSubmitting} className="iip-focus rounded-xl border-2 border-iip-line bg-white px-5 py-3 text-[15px] font-bold text-iip-ink hover:bg-white/60 disabled:opacity-50">
            Volver a editar
          </button>
          <button type="button" onClick={confirm} disabled={isSubmitting} className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-6 py-3 text-[15px] font-extrabold text-iip-ink shadow-sm hover:bg-iip-yellow-600 disabled:opacity-60">
            {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" /> : <Send className="h-5 w-5" aria-hidden="true" />}
            {isSubmitting ? 'Enviando…' : 'Confirmar y enviar'}
          </button>
        </div>
      </div>
    </div>
  );
};
