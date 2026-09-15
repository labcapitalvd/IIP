import React, { useState } from 'react';
import { useFormSubmission } from '../../context/FormSubmissionContext';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import {
  X,
  Send,
  Code2,
  ListOrdered,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Building2,
  Calendar,
  Layers,
  Sparkles,
  Download,
} from 'lucide-react';

interface SubmissionReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const SubmissionReviewModal: React.FC<SubmissionReviewModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { activeForm, answers, cardEntries, compileSubmissionPayload, submitForm, isSubmitting } =
    useFormSubmission();
  const { config, actors } = useApp();
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'visual' | 'json'>('visual');
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentActor = actors.find((a) => a.id === user?.actor_id) || actors[0];
  const payload = compileSubmissionPayload();

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(payload, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `IIP_Submission_${currentActor.label.replace(/\s+/g, '_')}_2026.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleConfirmSubmit = async () => {
    setErrorMsg(null);
    try {
      await submitForm();
      onSuccess();
    } catch (err: any) {
      setErrorMsg(
        err?.message || 'Error al procesar el envío del formulario. Verifique la conexión con el Core Service.'
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
                Paso Final • Confirmación de Envío
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-indigo-100 text-indigo-800">
                POST /submissions/forms/{activeForm.id}
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-900 mt-0.5">
              Revisión del Diagnóstico de Innovación Pública
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Entity Card summary */}
        <div className="bg-indigo-900 text-white px-6 py-3 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2.5">
            <Building2 className="w-4 h-4 text-indigo-300" />
            <div>
              <span className="font-semibold block">{currentActor.label}</span>
              <span className="text-[11px] text-indigo-200">{currentActor.actor_segment?.label || 'Distrito Capital'}</span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-indigo-200 block text-[11px]">Total de Respuestas e Iniciativas</span>
            <span className="font-bold text-sm text-indigo-100">{payload.length} elementos estructurados</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 bg-white">
          <button
            onClick={() => setActiveTab('visual')}
            className={`flex-1 py-3 text-xs font-semibold flex items-center justify-center gap-2 border-b-2 transition-colors ${
              activeTab === 'visual'
                ? 'border-indigo-600 text-indigo-700 bg-indigo-50/40'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <ListOrdered className="w-4 h-4" />
            Resumen de Respuestas por Dimensión
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`flex-1 py-3 text-xs font-semibold flex items-center justify-center gap-2 border-b-2 transition-colors ${
              activeTab === 'json'
                ? 'border-indigo-600 text-indigo-700 bg-indigo-50/40'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Code2 className="w-4 h-4" />
            Payload JSON (Esquema Backend FastAPI)
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6 text-sm">
          {errorMsg && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600" />
              <div>
                <span className="font-semibold block">Error al enviar formulario</span>
                <span>{errorMsg}</span>
              </div>
            </div>
          )}

          {activeTab === 'visual' ? (
            <div className="space-y-6">
              {activeForm.sections.map((section, sIdx) => {
                return (
                  <div key={section.id} className="border border-slate-200 rounded-xl overflow-hidden">
                    <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                      <span className="font-semibold text-xs text-slate-800">
                        {section.label}
                      </span>
                      <span className="text-[10px] text-slate-500">Dimensión #{sIdx + 1}</span>
                    </div>

                    <div className="p-4 space-y-4 divide-y divide-slate-100 text-xs">
                      {section.questions?.map((q) => {
                        if (q.card_template.is_repeatable) {
                          const entries = cardEntries[q.id] || [];
                          return (
                            <div key={q.id} className="pt-2 first:pt-0 space-y-2">
                              <div className="font-medium text-slate-700 flex items-center justify-between">
                                <span>{q.label}</span>
                                <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[10px]">
                                  {entries.length} iniciativa(s)
                                </span>
                              </div>
                              <div className="space-y-2 pl-2 border-l-2 border-indigo-200">
                                {entries.map((entry, eIdx) => (
                                  <div key={entry.id} className="p-2.5 bg-slate-50 rounded-lg space-y-1">
                                    <div className="font-semibold text-indigo-950">
                                      #{eIdx + 1}: {entry.title}
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600 pt-1">
                                      {Object.entries(entry.answers).map(([fId, val]) => (
                                        <div key={fId} className="truncate">
                                          <span className="text-slate-400 font-mono">{fId}:</span>{' '}
                                          <span className="font-medium text-slate-800">{String(val)}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        }

                        // Regular fields
                        return (
                          <div key={q.id} className="pt-3 first:pt-0 space-y-2">
                            <span className="font-medium text-slate-700 block">{q.label}</span>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-2">
                              {q.card_template.field_groups.flatMap((fg) => fg.fields).map((field) => {
                                const val = answers[field.id];
                                return (
                                  <div key={field.id} className="p-2 bg-slate-50/70 rounded-lg border border-slate-100">
                                    <span className="text-[11px] text-slate-500 block truncate">{field.label}</span>
                                    <span className="font-semibold text-slate-800 text-xs mt-0.5 block">
                                      {val !== undefined && val !== null && val !== '' ? (
                                        typeof val === 'boolean' ? (
                                          val ? (
                                            <span className="text-emerald-600">Sí</span>
                                          ) : (
                                            <span className="text-slate-500">No</span>
                                          )
                                        ) : (
                                          String(val) + (field.unit ? ` ${field.unit}` : '')
                                        )
                                      ) : (
                                        <span className="text-slate-400 italic">No diligenciado</span>
                                      )}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  Este es el arreglo sin tipar (<code className="font-mono text-indigo-600">List[Any]</code>) que se
                  enviará a <code className="font-mono text-indigo-600">POST /submissions/forms/{activeForm.id}</code>.
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleDownloadJson}
                    className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Descargar
                  </button>
                  <button
                    type="button"
                    onClick={handleCopyJson}
                    className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copiado' : 'Copiar JSON'}
                  </button>
                </div>
              </div>

              <pre className="p-4 bg-slate-900 text-emerald-400 font-mono text-xs rounded-xl overflow-x-auto max-h-[360px]">
                {JSON.stringify(payload, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-xl transition-colors"
          >
            Volver a Editar
          </button>

          <button
            onClick={handleConfirmSubmit}
            disabled={isSubmitting}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Confirmar y Enviar Diagnóstico Oficial</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
