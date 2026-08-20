import React, { useState } from 'react';
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
} from 'lucide-react';
import { EntitySubmission } from '../../types';

export const SubmissionsMonitor: React.FC = () => {
  const { submissions, actors } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSub, setSelectedSub] = useState<EntitySubmission | null>(null);

  const filteredSubmissions = submissions.filter((s) => {
    return (
      s.actor_label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.form_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.submitted_by.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

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
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600">
              /public/submissions
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">Diagnósticos IIP Radicados</h2>
          <p className="text-xs text-slate-500">
            Registro consolidado de envíos recibidos por parte de las entidades distritales.
          </p>
        </div>

        <button
          onClick={handleDownloadAllJson}
          className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2 self-start"
        >
          <Download className="w-4 h-4" />
          <span>Exportar Todo (JSON)</span>
        </button>
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar por nombre de entidad, radicado o usuario que envió..."
          className="w-full text-xs outline-none bg-transparent"
        />
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
                <th className="px-6 py-3.5">Responsable</th>
                <th className="px-6 py-3.5">Puntaje IIP</th>
                <th className="px-6 py-3.5">Iniciativas</th>
                <th className="px-6 py-3.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredSubmissions.map((sub) => {
                const numCards = sub.card_entries
                  ? Object.values(sub.card_entries).reduce(
                      (acc: number, arr: Array<any>) => acc + (arr?.length || 0),
                      0
                    )
                  : 0;

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
                    <td className="px-6 py-4 font-mono text-slate-600">{sub.submitted_by}</td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-full font-bold text-[11px] bg-emerald-50 text-emerald-700">
                        {sub.score ? `${sub.score} pts` : '100%'}
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
                  {selectedSub.score ?? 85.0} / 100
                </div>
              </div>

              {/* Repeatable Cards */}
              {selectedSub.card_entries && Object.keys(selectedSub.card_entries).length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-bold text-slate-900 uppercase text-xs flex items-center gap-1.5">
                    <Rocket className="w-4 h-4 text-indigo-600" />
                    Iniciativas y Proyectos de Innovación Radicados
                  </h4>
                  <div className="space-y-3">
                    {Object.entries(selectedSub.card_entries).map(([qId, entries]) =>
                      (entries as Array<{ id: string; title: string; answers: Record<string, any> }>).map((entry, idx) => (
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
                                <span className="text-[10px] text-slate-400 block font-mono">{fieldKey}</span>
                                <span className="font-medium text-slate-800">{String(val)}</span>
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
                      <span className="font-mono text-[10px] text-slate-400 block truncate">{fKey}</span>
                      <span className="font-semibold text-slate-800 block mt-0.5">
                        {typeof val === 'boolean' ? (val ? 'Sí' : 'No') : String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50 flex justify-end">
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
