import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { coreService } from '../../services/coreService';
import { HistoricalForm, MonitorRecord } from '../../types';
import { ROUTES, navigate } from '../../utils/router';
import { deleteSubmissionWithConfirm } from '../../utils/deleteSubmissionFlow';
import { Download, Eye, Loader2, RefreshCw, Search, Trash2 } from 'lucide-react';

type Coverage = 'all' | 'both' | 'answers' | 'results' | 'missing-results' | 'missing-answers';

const COVERAGE_LABEL: Record<Coverage, string> = {
  all: 'Todo',
  both: 'Con respuestas y resultado',
  answers: 'Con respuestas',
  results: 'Con resultado',
  'missing-results': 'Respuestas sin resultado',
  'missing-answers': 'Resultado sin respuestas',
};

const fmt = (n: number) => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 4 }).format(n);

/**
 * Monitor: una fila por entidad × formulario que tenga respuestas (radicado) y/o resultado
 * estadístico cargado. «Inspeccionar» abre una pantalla propia con ambos.
 */
export const SubmissionsMonitor: React.FC = () => {
  const { actors, deleteSubmission } = useApp();
  const [records, setRecords] = useState<MonitorRecord[]>([]);
  const [forms, setForms] = useState<HistoricalForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [actorFilter, setActorFilter] = useState('all');
  const [formFilter, setFormFilter] = useState('all');
  const [coverage, setCoverage] = useState<Coverage>('all');
  const [feedback, setFeedback] = useState<{ ok: boolean; message: string } | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [recs, fs] = await Promise.all([coreService.listRecords(), coreService.listHistoricalForms()]);
      setRecords(recs);
      setForms(fs);
    } catch (err: any) {
      setLoadError(err?.message || 'No se pudo cargar el monitor.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const actorOptions = useMemo(
    () => [...actors].sort((a, b) => a.label.localeCompare(b.label)).map((a) => [a.id, a.label] as [string, string]),
    [actors]
  );

  const filtered = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    return records
      .filter((r) => {
        if (actorFilter !== 'all' && r.actor_id !== actorFilter) return false;
        if (formFilter !== 'all' && r.form_id !== formFilter) return false;
        const hasAnswers = !!r.submission_id;
        switch (coverage) {
          case 'both':
            if (!(hasAnswers && r.has_results)) return false;
            break;
          case 'answers':
            if (!hasAnswers) return false;
            break;
          case 'results':
            if (!r.has_results) return false;
            break;
          case 'missing-results':
            if (!(hasAnswers && !r.has_results)) return false;
            break;
          case 'missing-answers':
            if (!(!hasAnswers && r.has_results)) return false;
            break;
        }
        return (
          !q ||
          r.actor_label.toLowerCase().includes(q) ||
          r.form_label.toLowerCase().includes(q) ||
          r.form_code.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => a.form_code.localeCompare(b.form_code) || a.actor_label.localeCompare(b.actor_label));
  }, [records, searchTerm, actorFilter, formFilter, coverage]);

  const inspect = (r: MonitorRecord) => navigate(`${ROUTES.admin.submissions}/${r.form_id}/${r.actor_id}`);

  const handleDelete = async (r: MonitorRecord) => {
    if (!r.submission_id) return;
    setDeletingId(r.submission_id);
    setFeedback(null);
    try {
      if (await deleteSubmissionWithConfirm(deleteSubmission, r.submission_id, r.actor_label, r.form_code)) {
        setFeedback({ ok: true, message: `Se eliminaron las respuestas de ${r.actor_label} (${r.form_code}).` });
        await load();
      }
    } catch (err: any) {
      setFeedback({ ok: false, message: err?.message || 'No se pudo eliminar el radicado.' });
    } finally {
      setDeletingId(null);
    }
  };

  const handleExport = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(filtered, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', dataStr);
    a.setAttribute('download', 'IIP_Monitor_Entidad_x_Formulario.json');
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const selectedForm = forms.find((f) => f.id === formFilter);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
            Monitoreo y Auditoría de Evidencias
          </span>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">Entidades por formulario</h2>
          <p className="text-xs text-slate-500 max-w-3xl">
            Una fila por entidad y formulario con respuestas y/o resultado estadístico cargado. Al inspeccionar se
            abre una pantalla con las respuestas de la entidad y su resultado.
          </p>
        </div>
        <div className="flex gap-2 self-start">
          <button
            onClick={() => void load()}
            className="px-3 py-2.5 bg-white hover:bg-slate-50 border border-slate-200 font-semibold text-xs rounded-xl flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Exportar lista (JSON)
          </button>
        </div>
      </div>

      {loadError && (
        <div className="p-3 rounded-xl border bg-rose-50 border-rose-200 text-rose-800 text-xs">{loadError}</div>
      )}
      {feedback && (
        <div
          className={`p-3 rounded-xl border text-xs ${
            feedback.ok ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {feedback.message}
        </div>
      )}

      <div className="bg-white p-4 rounded-2xl border border-slate-200 grid grid-cols-1 md:grid-cols-[1fr_14rem_16rem_14rem] gap-3 items-center">
        <div className="flex items-center gap-3">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por entidad o formulario..."
            className="w-full text-xs outline-none bg-transparent"
          />
        </div>
        <select
          value={actorFilter}
          onChange={(e) => setActorFilter(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-xl text-xs bg-white"
        >
          <option value="all">Todas las entidades</option>
          {actorOptions.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
        <select
          value={formFilter}
          onChange={(e) => setFormFilter(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-xl text-xs bg-white"
        >
          <option value="all">Todos los formularios</option>
          {forms.map((f) => (
            <option key={f.id} value={f.id}>
              {f.code} — {f.label}
            </option>
          ))}
        </select>
        <select
          value={coverage}
          onChange={(e) => setCoverage(e.target.value as Coverage)}
          className="px-3 py-2 border border-slate-300 rounded-xl text-xs bg-white"
        >
          {(Object.keys(COVERAGE_LABEL) as Coverage[]).map((k) => (
            <option key={k} value={k}>
              {COVERAGE_LABEL[k]}
            </option>
          ))}
        </select>
      </div>
      <div className="text-[11px] text-slate-500 -mt-3">
        {filtered.length} de {records.length} fila(s) · {forms.length} formulario(s) en el servidor
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
              <th className="px-4 py-3 font-bold">Entidad</th>
              <th className="px-4 py-3 font-bold">Formulario</th>
              <th className="px-4 py-3 font-bold">Respuestas</th>
              <th className="px-4 py-3 font-bold text-right">Resultado (total)</th>
              <th className="px-4 py-3 font-bold">Actualizado</th>
              <th className="px-4 py-3 font-bold text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((r) => (
              <tr key={`${r.form_id}:${r.actor_id}`} className="hover:bg-slate-50/60">
                <td className="px-4 py-3">
                  <div className="font-bold text-slate-900">{r.actor_label}</div>
                  {r.actor_segment_label && <div className="text-[11px] text-slate-500">{r.actor_segment_label}</div>}
                </td>
                <td className="px-4 py-3">
                  <div className="font-semibold text-slate-800">{r.form_label}</div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    {r.form_code}
                    {r.form_year ? ` · ${r.form_year}` : ''}
                  </div>
                </td>
                <td className="px-4 py-3">
                  {r.submission_id ? (
                    <div>
                      <span
                        className={`inline-block px-2 py-0.5 rounded-lg font-semibold ${
                          r.status === 'draft'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}
                      >
                        {r.status === 'draft' ? 'Borrador' : 'Enviado'}
                      </span>
                      <div className="text-[11px] text-slate-500 mt-1">
                        {r.answer_count} respuesta(s) · {r.card_count} tarjeta(s)
                      </div>
                    </div>
                  ) : (
                    <span className="text-slate-400 italic">Sin respuestas</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  {r.has_results ? (
                    <span className="font-bold text-slate-900">{r.total != null ? fmt(r.total) : 'cargado'}</span>
                  ) : (
                    <span className="text-slate-400 italic font-sans">Sin resultado</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {r.updated_at ? new Date(r.updated_at).toLocaleDateString() : '—'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1.5">
                    <button
                      onClick={() => inspect(r)}
                      className="px-2.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      Inspeccionar
                    </button>
                    {r.submission_id && (
                      <button
                        disabled={deletingId === r.submission_id}
                        onClick={() => void handleDelete(r)}
                        title="Eliminar las respuestas de esta entidad en este formulario"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                      >
                        {deletingId === r.submission_id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-slate-400">
                  {formFilter !== 'all' && records.every((r) => r.form_id !== formFilter)
                    ? `«${selectedForm?.label ?? 'Este formulario'}» no tiene respuestas ni resultado cargado todavía.`
                    : 'No hay filas que coincidan con los filtros.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
