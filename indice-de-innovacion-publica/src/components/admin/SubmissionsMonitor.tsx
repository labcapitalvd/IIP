import React, { useEffect, useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  FileCheck2,
  Search,
  Filter,
  Download,
  Eye,
  Building2,
  Calendar,
  Layers,
  Award,
  Rocket,
  CheckCircle2,
  X,
  Trash2,
} from 'lucide-react';
import { EntitySubmission } from '../../types';

export const SubmissionsMonitor: React.FC = () => {
  const { submissions, loadSubmissionDetail, deleteSubmission } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [actorFilter, setActorFilter] = useState('all');
  const [formFilter, setFormFilter] = useState('all');
  const [feedback, setFeedback] = useState<{ ok: boolean; message: string } | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const selectedSub: EntitySubmission | null = submissions.find((s) => s.id === selectedId) ?? null;
  const setSelectedSub = (sub: EntitySubmission | null) => setSelectedId(sub?.id ?? null);

  // Las respuestas no vienen en la lista: se piden al servidor al inspeccionar un radicado.
  useEffect(() => {
    if (!selectedId) return;
    const current = submissions.find((s) => s.id === selectedId);
    if (!current || current.detail_loaded) return;
    setDetailError(null);
    loadSubmissionDetail(selectedId).catch((err: any) =>
      setDetailError(err?.message || 'No se pudo cargar el detalle del radicado.')
    );
  }, [selectedId]);

  const actorOptions = [...new Map<string, string>(submissions.map((s) => [s.actor_id, s.actor_label] as [string, string])).entries()].sort((a, b) =>
    a[1].localeCompare(b[1])
  );
  const formOptions = [...new Map<string, string>(
      submissions.map((s) => [s.form_id, `${s.form_code} — ${s.form_title}`] as [string, string])
    ).entries()].sort(
    (a, b) => a[1].localeCompare(b[1])
  );

  const filteredSubmissions = submissions.filter((s) => {
    const q = searchTerm.toLowerCase();
    return (
      (actorFilter === 'all' || s.actor_id === actorFilter) &&
      (formFilter === 'all' || s.form_id === formFilter) &&
      (!q ||
        s.actor_label.toLowerCase().includes(q) ||
        s.form_title.toLowerCase().includes(q) ||
        s.form_code.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q))
    );
  });

  const handleDelete = async (sub: EntitySubmission) => {
    if (
      !confirm(
        `¿Eliminar TODAS las respuestas de «${sub.actor_label}» al formulario «${sub.form_code}»?\n\n` +
          'Esta acción no se puede deshacer. La asignación de esa entidad volverá a quedar pendiente.'
      )
    )
      return;
    setDeletingId(sub.id);
    setFeedback(null);
    try {
      try {
        await deleteSubmission(sub.id);
      } catch (err: any) {
        if (err?.data?.code !== 'SUBMISSION_HAS_GRADES_ERROR') throw err;
        if (!confirm('Este radicado ya tiene calificaciones. ¿Eliminarlo junto con sus calificaciones?')) return;
        await deleteSubmission(sub.id, true);
      }
      if (selectedId === sub.id) setSelectedId(null);
      setFeedback({ ok: true, message: `Se eliminaron las respuestas de ${sub.actor_label} (${sub.form_code}).` });
    } catch (err: any) {
      setFeedback({ ok: false, message: err?.message || 'No se pudo eliminar el radicado.' });
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownloadAllJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(submissions, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `IIP_All_Submissions_Export_2026.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
              Monitoreo y Auditoría de Evidencias
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">Diagnósticos IIP Radicados</h2>
          <p className="text-xs text-slate-500">
            Registro consolidado de los radicados guardados en el servidor. El detalle de respuestas se
            consulta al inspeccionar cada radicado.
          </p>
        </div>

        <button
          onClick={handleDownloadAllJson}
          className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2 self-start"
        >
          <Download className="w-4 h-4" />
          <span>Exportar lista (JSON)</span>
        </button>
      </div>

      {feedback && (
        <div
          className={`p-3 rounded-xl border text-xs ${
            feedback.ok ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {feedback.message}
        </div>
      )}

      {/* Search + filtros entidad × formulario */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs grid grid-cols-1 md:grid-cols-[1fr_16rem_16rem] gap-3 items-center">
        <div className="flex items-center gap-3">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por entidad, formulario o número de radicado..."
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
          {formOptions.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div className="text-[11px] text-slate-500 -mt-3">
        {filteredSubmissions.length} de {submissions.length} radicado(s)
      </div>

      {/* Submissions Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-3.5">Entidad / Actor</th>
                <th className="px-6 py-3.5">Sector</th>
                <th className="px-6 py-3.5">Fecha de Envío</th>
                <th className="px-6 py-3.5">Formulario</th>
                <th className="px-6 py-3.5">Puntaje IIP</th>
                <th className="px-6 py-3.5">Iniciativas</th>
                <th className="px-6 py-3.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredSubmissions.map((sub) => {
                const numCards =
                  sub.card_count ??
                  (sub.card_entries
                    ? Object.values(sub.card_entries).reduce(
                        (acc: number, arr: Array<any>) => acc + (arr?.length || 0),
                        0
                      )
                    : 0);

                return (
                  <tr key={sub.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-bold text-slate-900">
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-700">
                          <Building2 className="w-4 h-4" />
                        </div>
                        <div>
                          <span>{sub.actor_label}</span>
                          <span className="block font-mono text-[10px] text-slate-400 font-normal">
                            {sub.id}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {sub.actor_segment_label || 'Distrito Capital'}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-500">
                      {new Date(sub.submitted_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-slate-700">
                      <span className="font-mono font-bold">{sub.form_code}</span>
                      <span className="block text-[10px] text-slate-400 max-w-[14rem] truncate">{sub.form_title}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-full font-bold text-[11px] bg-emerald-50 text-emerald-700">
                        {sub.score !== undefined ? `${sub.score} pts` : 'Sin calificar'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[10px]">
                        {numCards} iniciativa(s)
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedSub(sub)}
                        className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspeccionar</span>
                      </button>
                      <button
                        onClick={() => handleDelete(sub)}
                        disabled={deletingId === sub.id}
                        title="Eliminar las respuestas de esta entidad para este formulario"
                        className="ml-2 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>{deletingId === sub.id ? 'Eliminando…' : 'Eliminar'}</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filteredSubmissions.length === 0 && (
          <div className="p-12 text-center text-xs text-slate-500">
            No se encontraron envíos con los criterios de búsqueda.
          </div>
        )}
      </div>

      {/* Drill-down Detail Modal */}
      {selectedSub && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-900 text-white">
              <div>
                <span className="text-[10px] font-bold text-indigo-300 uppercase">
                  Inspección de Respuestas
                </span>
                <h3 className="font-bold text-sm text-white mt-0.5">{selectedSub.actor_label}</h3>
                <span className="text-xs text-slate-300 block">Formulario: {selectedSub.form_code} — {selectedSub.form_title}</span>
                <span className="text-xs text-slate-400">Radicado: {selectedSub.id}</span>
              </div>
              <button
                onClick={() => setSelectedSub(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              {/* Score summary */}
              <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-200 flex items-center justify-between">
                <div>
                  <span className="font-bold text-emerald-900 text-xs">Puntaje Oficial Registrado</span>
                  <p className="text-[11px] text-emerald-700">Calculado para el Índice de Innovación</p>
                </div>
                <div className="text-xl font-bold text-emerald-700 font-mono">
                  {selectedSub.score !== undefined ? `${selectedSub.score} / 100` : 'Sin calificar'}
                </div>
              </div>

              {detailError && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700">{detailError}</div>
              )}
              {!selectedSub.detail_loaded && !detailError && (
                <div className="p-3 text-slate-500">Cargando respuestas del servidor…</div>
              )}

              {/* Repeatable Cards */}
              {selectedSub.card_entries && Object.keys(selectedSub.card_entries).length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-bold text-slate-900 uppercase text-xs flex items-center gap-1.5">
                    <Rocket className="w-4 h-4 text-indigo-600" />
                    Iniciativas y Proyectos de Innovación Radicados
                  </h4>
                  <div className="space-y-3">
                    {Object.entries(selectedSub.card_entries).map(([qId, entries]) =>
                      (entries as Array<{ id: string; title: string; answers: Record<string, any>; display?: Record<string, string> }>).map((entry, idx) => (
                        <div
                          key={entry.id}
                          className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-900 text-xs">
                              Iniciativa #{idx + 1}: {entry.title}
                            </span>
                            <span className="text-[10px] font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded font-semibold">
                              card_entry
                            </span>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-700 pt-1">
                            {Object.entries(entry.answers).map(([fieldKey, val]) => (
                              <div key={fieldKey} className="bg-white p-2 rounded-lg border border-slate-100">
                                <span className="text-[10px] text-slate-400 block">{selectedSub.field_labels?.[fieldKey] ?? fieldKey}</span>
                                <span className="font-medium text-slate-800">{entry.display?.[fieldKey] ?? String(val)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Technical Indicator Answers */}
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 uppercase text-xs flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  Indicadores de Capacidades y Cultura
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {Object.entries(selectedSub.raw_answers).map(([fKey, val]) => (
                    <div key={fKey} className="p-2.5 bg-slate-50 rounded-xl border border-slate-100">
                      <span className="text-[10px] text-slate-400 block truncate">{selectedSub.field_labels?.[fKey] ?? fKey}</span>
                      <span className="font-semibold text-slate-800 block mt-0.5">
                        {selectedSub.display_values?.[fKey] ?? (typeof val === 'boolean' ? (val ? 'Sí' : 'No') : String(val))}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex justify-between gap-2">
              <button
                onClick={() => handleDelete(selectedSub)}
                disabled={deletingId === selectedSub.id}
                className="px-4 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-xs rounded-xl inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                <Trash2 className="w-3.5 h-3.5" /> Eliminar respuestas
              </button>
              <button
                onClick={() => setSelectedSub(null)}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold text-xs rounded-xl"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
