import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { useFormSubmission } from '../../context/FormSubmissionContext';
import {
  FileText,
  Clock,
  CheckCircle2,
  Download,
  Eye,
  ArrowLeft,
  Calendar,
  Layers,
  Sparkles,
  Rocket,
  Award,
} from 'lucide-react';
import { EntitySubmission } from '../../types';

interface SubmissionsHistoryViewProps {
  onBack: () => void;
  onContinueEditing: () => void;
}

export const SubmissionsHistoryView: React.FC<SubmissionsHistoryViewProps> = ({
  onBack,
  onContinueEditing,
}) => {
  const { user } = useAuth();
  const { submissions, actors } = useApp();
  const { loadSubmissionForReview } = useFormSubmission();

  const currentActor = actors.find((a) => a.id === user?.actor_id) || actors[0];
  const entitySubmissions = submissions.filter((s) => s.actor_id === currentActor?.id);

  const [selectedSub, setSelectedSub] = useState<EntitySubmission | null>(
    entitySubmissions[0] || null
  );

  const handleDownload = (sub: EntitySubmission) => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(sub, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `IIP_Envio_${sub.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1.5"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al Panel</span>
        </button>
        <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
          Historial y Certificados de Envío
        </span>
      </div>

      {entitySubmissions.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-4">
          <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto">
            <FileText className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-900">No hay envíos registrados todavía</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Tu entidad aún no ha enviado el cuestionario del Índice de Innovación Pública 2026.
          </p>
          <button
            onClick={onContinueEditing}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors"
          >
            Iniciar Diligenciamiento Ahora
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Submissions List */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Envíos Realizados ({entitySubmissions.length})
            </h3>
            <div className="space-y-2">
              {entitySubmissions.map((sub) => {
                const isSelected = selectedSub?.id === sub.id;
                return (
                  <button
                    key={sub.id}
                    onClick={() => setSelectedSub(sub)}
                    className={`w-full text-left p-4 rounded-2xl border transition-all block ${
                      isSelected
                        ? 'bg-indigo-900 text-white border-indigo-900 shadow-md ring-2 ring-indigo-600'
                        : 'bg-white text-slate-800 border-slate-200 hover:border-indigo-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        isSelected ? 'bg-indigo-800 text-indigo-200' : 'bg-emerald-50 text-emerald-700'
                      }`}>
                        {sub.status.toUpperCase()}
                      </span>
                      <span className={`text-[11px] font-mono ${isSelected ? 'text-indigo-200' : 'text-slate-400'}`}>
                        {new Date(sub.submitted_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="font-bold text-xs truncate mt-1">{sub.form_title}</div>
                    <div className={`text-[11px] mt-1 flex items-center justify-between ${
                      isSelected ? 'text-indigo-200' : 'text-slate-500'
                    }`}>
                      <span>Por: {sub.submitted_by}</span>
                      <span className="font-semibold">{sub.score ? `${sub.score} pts` : '100%'}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Submission Details Inspector */}
          <div className="lg:col-span-2">
            {selectedSub ? (
              <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden space-y-6">
                {/* Header */}
                <div className="bg-slate-900 text-white p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">
                      Comprobante Oficial de Radicación
                    </span>
                    <h2 className="text-lg font-bold text-white mt-0.5">{selectedSub.form_title}</h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Radicado: <code className="text-emerald-400 font-mono">{selectedSub.id}</code> • {new Date(selectedSub.submitted_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDownload(selectedSub)}
                      className="px-3.5 py-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-xl backdrop-blur-xs transition-colors flex items-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Descargar JSON</span>
                    </button>
                  </div>
                </div>

                {/* Body Details */}
                <div className="p-6 space-y-6">
                  {/* Score banner */}
                  <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 bg-emerald-600 text-white rounded-xl">
                        <Award className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-emerald-900">Puntaje Obtenido en el IIP</span>
                        <p className="text-[11px] text-emerald-700">Índice sintético de capacidades y cultura de innovación</p>
                      </div>
                    </div>
                    <div className="text-2xl font-black text-emerald-700 font-mono">
                      {selectedSub.score ?? 85.0} <span className="text-sm font-normal text-emerald-600">/ 100</span>
                    </div>
                  </div>

                  {/* Repeatable Cards Registered */}
                  {selectedSub.card_entries && Object.keys(selectedSub.card_entries).length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                        <Rocket className="w-4 h-4 text-indigo-600" />
                        Iniciativas de Innovación Radicadas
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
                                  #{idx + 1}: {entry.title}
                                </span>
                                <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                                  card_entry
                                </span>
                              </div>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600 pt-1">
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

                  {/* Summary of Technical Answers */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-indigo-600" />
                      Respuestas a Indicadores Técnicos
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {Object.entries(selectedSub.raw_answers).map(([fKey, val]) => (
                        <div key={fKey} className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 text-xs">
                          <span className="font-mono text-[10px] text-slate-400 block truncate">{fKey}</span>
                          <span className="font-semibold text-slate-800 mt-0.5 block">
                            {typeof val === 'boolean' ? (val ? 'Sí' : 'No') : String(val)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
