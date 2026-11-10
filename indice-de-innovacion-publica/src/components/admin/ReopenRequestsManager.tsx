import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, Loader2, RefreshCw, Unlock, XCircle } from 'lucide-react';
import { coreService } from '../../services/coreService';
import { ReopenRequest, ReopenStatus } from '../../types';

const STATUS_LABEL: Record<ReopenStatus, string> = { pending: 'Pendiente', approved: 'Aprobada', rejected: 'Rechazada' };
const STATUS_STYLE: Record<ReopenStatus, string> = {
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  rejected: 'bg-rose-50 text-rose-700 border-rose-200',
};
const fmt = (iso?: string) => (iso ? new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' }) : '—');

/** Solicitudes de las entidades para modificar un formulario ya enviado. Aprobar devuelve el envío a borrador. */
export const ReopenRequestsManager: React.FC = () => {
  const [filter, setFilter] = useState<ReopenStatus | 'all'>('pending');
  const [items, setItems] = useState<ReopenRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await coreService.listReopenRequests(filter === 'all' ? undefined : filter));
    } catch (e: any) {
      setError(e?.message || 'No se pudieron cargar las solicitudes.');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void load();
  }, [load]);

  const resolve = async (r: ReopenRequest, approve: boolean) => {
    if (approve && !confirm(`Al aprobar, el envío de «${r.actor_label}» vuelve a borrador y la entidad podrá modificarlo y reenviarlo. ¿Continuar?`)) return;
    setBusy(r.id);
    setError(null);
    try {
      await coreService.resolveReopenRequest(r.id, approve, notes[r.id]);
      await load();
    } catch (e: any) {
      setError(e?.message || 'No se pudo resolver la solicitud.');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-8 py-8 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-amber-600 text-xs font-bold uppercase tracking-wider"><Unlock className="w-4 h-4" /> Solicitudes de modificación</div>
          <h2 className="text-2xl font-extrabold text-slate-900 mt-1">Formularios enviados que la entidad quiere modificar</h2>
          <p className="text-sm text-slate-500 mt-1">Aprobar devuelve el envío a borrador con sus respuestas; rechazar lo deja como está. Si el envío ya tiene calificaciones, no se puede reabrir.</p>
        </div>
        <button type="button" onClick={() => load()} className="px-3 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 flex items-center gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Actualizar
        </button>
      </div>

      <div role="tablist" aria-label="Filtrar por estado" className="flex flex-wrap gap-2">
        {(['pending', 'approved', 'rejected', 'all'] as const).map((f) => (
          <button key={f} role="tab" aria-selected={filter === f} type="button" onClick={() => setFilter(f)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-bold border ${filter === f ? 'bg-amber-500 border-amber-500 text-slate-950' : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
            {f === 'all' ? 'Todas' : STATUS_LABEL[f]}
          </button>
        ))}
      </div>

      {error && (
        <div role="alert" className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
        </div>
      )}

      {loading ? (
        <div className="py-16 flex items-center justify-center gap-2 text-sm text-slate-500"><Loader2 className="w-5 h-5 animate-spin" /> Cargando…</div>
      ) : items.length === 0 ? (
        <p className="py-16 text-center text-sm text-slate-500">No hay solicitudes en este estado.</p>
      ) : (
        <ul className="space-y-4">
          {items.map((r) => (
            <li key={r.id} className="bg-white border border-slate-200 rounded-2xl p-5 space-y-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-base font-bold text-slate-900">{r.actor_label}</p>
                  <p className="text-xs text-slate-500">{r.form_code} · {r.form_label}</p>
                </div>
                <span className={`px-3 py-1 rounded-full border text-xs font-bold ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>
              </div>
              <p className="text-xs text-slate-500">Solicitada por {r.requested_by_name || 'usuario eliminado'} · {fmt(r.requested_at)}</p>
              <blockquote className="text-sm text-slate-800 bg-slate-50 border-l-4 border-amber-400 rounded-r-xl px-4 py-3 whitespace-pre-line">{r.reason}</blockquote>

              {r.status === 'pending' ? (
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-slate-600" htmlFor={`note-${r.id}`}>Nota para la entidad (opcional)</label>
                  <textarea id={`note-${r.id}`} rows={2} value={notes[r.id] ?? ''} onChange={(e) => setNotes((n) => ({ ...n, [r.id]: e.target.value }))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-amber-400 outline-none" />
                  <div className="flex flex-wrap gap-2">
                    <button type="button" disabled={busy === r.id} onClick={() => resolve(r, true)} className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-2 disabled:opacity-50">
                      {busy === r.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Aprobar y reabrir
                    </button>
                    <button type="button" disabled={busy === r.id} onClick={() => resolve(r, false)} className="px-4 py-2 rounded-xl border border-rose-200 text-rose-700 hover:bg-rose-50 text-xs font-bold flex items-center gap-2 disabled:opacity-50">
                      <XCircle className="w-4 h-4" /> Rechazar
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500">Resuelta {fmt(r.resolved_at)}{r.resolution_note ? ` — «${r.resolution_note}»` : ''}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
