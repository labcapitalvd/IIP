import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, Clock, Loader2, PencilLine, Send, X, XCircle } from 'lucide-react';
import { coreService } from '../../../services/coreService';
import { EntityAssignment } from '../../../types';

const MIN = 10;

/** Estado de la solicitud de modificación de un formulario ya enviado, con la acción de solicitarla. */
export const ReopenSection: React.FC<{ assignment: EntityAssignment; onChanged: () => void }> = ({ assignment, onChanged }) => {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const areaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!open) return;
    areaRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && !sending && setOpen(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, sending]);

  const send = async () => {
    setSending(true);
    setError(null);
    try {
      await coreService.requestReopen(assignment.form_id, reason.trim());
      setOpen(false);
      setReason('');
      onChanged();
    } catch (e: any) {
      setError(e?.message || 'No se pudo enviar la solicitud.');
    } finally {
      setSending(false);
    }
  };

  const status = assignment.reopen_status;

  return (
    <div className="mt-6 border-t border-iip-line pt-5 text-left">
      {status === 'pending' ? (
        <p role="status" className="flex items-start gap-2 rounded-2xl bg-iip-yellow-50 p-4 text-sm text-iip-ink">
          <Clock className="mt-0.5 h-4 w-4 shrink-0 text-iip-yellow-600" aria-hidden="true" />
          <span><strong>Solicitud de modificación en revisión.</strong> Un administrador la aprobará o rechazará; si la aprueba, podrá editar sus respuestas y volver a enviar.</span>
        </p>
      ) : (
        <>
          {status === 'rejected' && (
            <p role="status" className="mb-3 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
              <XCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span><strong>Su última solicitud fue rechazada.</strong>{assignment.reopen_note ? ` Nota: «${assignment.reopen_note}»` : ''}</span>
            </p>
          )}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-iip-muted">¿Necesita corregir algo? Solicite la modificación y un administrador la evaluará.</p>
            <button type="button" onClick={() => setOpen(true)} className="iip-focus flex items-center gap-2 rounded-xl border-2 border-iip-navy px-5 py-2.5 text-[15px] font-bold text-iip-navy hover:bg-iip-sky">
              <PencilLine className="h-4 w-4" aria-hidden="true" /> {status === 'rejected' ? 'Solicitar nuevamente' : 'Solicitar modificación'}
            </button>
          </div>
        </>
      )}

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-iip-ink/70 p-4">
          <div role="dialog" aria-modal="true" aria-labelledby="reopen-title" className="w-full max-w-lg overflow-hidden rounded-3xl bg-white shadow-2xl">
            <div className="flex items-start justify-between gap-3 bg-iip-navy px-6 py-5 text-white">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-iip-yellow">Formulario enviado</p>
                <h2 id="reopen-title" className="text-xl font-extrabold">Solicitar modificación</h2>
              </div>
              <button type="button" onClick={() => setOpen(false)} disabled={sending} aria-label="Cerrar" className="iip-focus rounded-xl p-2 hover:bg-white/10 disabled:opacity-50"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-3 p-6">
              <label htmlFor="reopen-reason" className="block text-sm font-bold text-iip-ink">¿Qué desea modificar y por qué?</label>
              <textarea
                id="reopen-reason" ref={areaRef} rows={5} value={reason} onChange={(e) => setReason(e.target.value)} maxLength={2000}
                placeholder="Describa qué respuestas necesita corregir y el motivo…"
                className="iip-focus w-full rounded-xl border border-iip-line px-3.5 py-2.5 text-[15px] text-iip-ink"
              />
              <p className="text-xs text-iip-muted">Mínimo {MIN} caracteres. Si se aprueba, su envío volverá a borrador con todas sus respuestas.</p>
              {error && <p role="alert" className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-semibold text-rose-700"><AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" /> {error}</p>}
            </div>
            <div className="flex justify-end gap-3 border-t border-iip-line bg-iip-bg px-6 py-4">
              <button type="button" onClick={() => setOpen(false)} disabled={sending} className="iip-focus rounded-xl border-2 border-iip-line bg-white px-5 py-2.5 font-bold text-iip-ink disabled:opacity-50">Cancelar</button>
              <button type="button" onClick={send} disabled={sending || reason.trim().length < MIN} className="iip-focus flex items-center gap-2 rounded-xl bg-iip-yellow px-5 py-2.5 font-extrabold text-iip-ink hover:bg-iip-yellow-600 disabled:cursor-not-allowed disabled:opacity-50">
                {sending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Send className="h-4 w-4" aria-hidden="true" />} Enviar solicitud
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
