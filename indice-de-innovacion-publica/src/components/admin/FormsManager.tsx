import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  Layers,
  Code2,
  Download,
  Copy,
  Check,
  Send,
  Building2,
  Sparkles,
  Cpu,
  Rocket,
  ChevronDown,
  ChevronRight,
  Info,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Plus,
  Edit,
  Copy as CopyIcon,
  Trash2,
  FileText,
  Sliders,
  CheckCircle,
  ExternalLink,
} from 'lucide-react';
import { IIPForm } from '../../types';
import { FormBuilderModal } from './FormBuilderModal';

interface FormsManagerProps {
  onGoToAssign?: (formId: string) => void;
}

export const FormsManager: React.FC<FormsManagerProps> = ({ onGoToAssign }) => {
  const {
    forms,
    activeForm,
    setActiveFormById,
    saveFormDefinition,
    deleteForm,
    duplicateForm,
    config,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'visual' | 'json'>('visual');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    [activeForm.sections[0]?.id || '']: true,
  });
  const [copied, setCopied] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  const [postResult, setPostResult] = useState<{ success: boolean; message: string } | null>(null);

  // Form Builder Modal State
  const [showBuilderModal, setShowBuilderModal] = useState(false);
  const [editingForm, setEditingForm] = useState<IIPForm | null>(null);

  const toggleSection = (id: string) => {
    setExpandedSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(activeForm, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = (form: IIPForm) => {
    const dataStr =
      'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(form, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `IIP_Form_Schema_${form.code}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handlePostToBackend = async () => {
    setIsPosting(true);
    setPostResult(null);
    try {
      await saveFormDefinition(activeForm);
      setPostResult({
        success: true,
        message: `Formulario "${activeForm.label}" registrado y sincronizado exitosamente mediante POST /forms.`,
      });
    } catch (err: any) {
      setPostResult({
        success: false,
        message: err?.message || 'Error al registrar el formulario en el backend.',
      });
    } finally {
      setIsPosting(false);
    }
  };

  const handleOpenCreateModal = () => {
    setEditingForm(null);
    setShowBuilderModal(true);
  };

  const handleOpenEditModal = (form: IIPForm) => {
    setEditingForm(form);
    setShowBuilderModal(true);
  };

  const handleSaveFormFromBuilder = async (form: IIPForm) => {
    await saveFormDefinition(form);
    setActiveFormById(form.id);
  };

  const handleDeleteForm = async (formId: string, formTitle: string) => {
    if (confirm(`¿Está seguro de eliminar el formulario "${formTitle}"?`)) {
      await deleteForm(formId);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header with LabCapital Brand & Primary Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
              Administración • LabCapital
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600">
              POST /forms
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
            Gestor y Creador de Formularios IIP
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Cree, diseñe y gestione los instrumentos de recolección distritales con dimensiones, preguntas, tipos de campos y ponderaciones.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleOpenCreateModal}
            className="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Crear Nuevo Formulario</span>
          </button>

          <button
            onClick={handlePostToBackend}
            disabled={isPosting}
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            {isPosting ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5 text-amber-400" />
            )}
            <span>Sincronizar con API</span>
          </button>
        </div>
      </div>

      {postResult && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center gap-2 animate-in fade-in ${
            postResult.success
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {postResult.success ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{postResult.message}</span>
        </div>
      )}

      {/* Available Forms Carousel / Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-amber-500" />
            <span>Formularios en el Sistema ({forms.length})</span>
          </h3>
          <span className="text-xs text-slate-400">Seleccione un formulario para ver y editar su estructura</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {forms.map((form) => {
            const isSelected = form.id === activeForm.id;
            const totalQuestions = form.sections.reduce(
              (acc, s) => acc + (s.questions?.length || 0),
              0
            );

            return (
              <div
                key={form.id}
                onClick={() => setActiveFormById(form.id)}
                className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-4 ${
                  isSelected
                    ? 'bg-amber-50/40 border-amber-400 ring-2 ring-amber-400/20 shadow-md'
                    : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-xs'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 bg-slate-900 text-amber-400 rounded">
                      {form.code}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {form.is_active ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          <span>Activo</span>
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 text-slate-500 rounded-full">
                          Inactivo
                        </span>
                      )}
                    </div>
                  </div>

                  <h4 className="font-bold text-slate-900 text-sm leading-snug">{form.label}</h4>
                  <p className="text-xs text-slate-500 line-clamp-2">{form.description}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                  <div className="space-y-0.5">
                    <div className="font-semibold text-slate-900">Vigencia {form.year}</div>
                    <div className="text-[11px] text-slate-400">
                      {form.sections.length} dimensiones • {totalQuestions} criterios
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenEditModal(form);
                      }}
                      className="p-1.5 rounded-lg text-slate-600 hover:text-amber-700 hover:bg-amber-100/60 transition-colors"
                      title="Editar estructura"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        duplicateForm(form.id);
                      }}
                      className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-700 hover:bg-indigo-50 transition-colors"
                      title="Duplicar formulario"
                    >
                      <CopyIcon className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownloadJson(form);
                      }}
                      className="p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                      title="Descargar esquema JSON"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    {forms.length > 1 && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteForm(form.id, form.label);
                        }}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        title="Eliminar formulario"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Form Inspector / Hierarchy View */}
      <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs">
        {/* Selected Form Header */}
        <div className="bg-slate-900 text-white p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
              <span>Formulario Seleccionado</span>
              <span>•</span>
              <span className="font-mono">{activeForm.code}</span>
              <span>•</span>
              <span>Versión {activeForm.version}</span>
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white">{activeForm.label}</h3>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleOpenEditModal(activeForm)}
              className="px-3.5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-1.5"
            >
              <Edit className="w-3.5 h-3.5" />
              <span>Editar en Diseñador</span>
            </button>

            {onGoToAssign && (
              <button
                onClick={() => onGoToAssign(activeForm.id)}
                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs rounded-xl border border-slate-700 transition-colors flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5 text-amber-400" />
                <span>Asignar a Entidades</span>
              </button>
            )}
          </div>
        </div>

        {/* View Toggle Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50/70 px-6 pt-3">
          <button
            onClick={() => setActiveTab('visual')}
            className={`py-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'visual'
                ? 'border-amber-500 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Layers className="w-4 h-4 text-amber-500" />
            <span>Explorador Visual de Dimensiones y Preguntas</span>
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`py-2.5 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'json'
                ? 'border-amber-500 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Code2 className="w-4 h-4 text-amber-500" />
            <span>Esquema JSON Completo (POST /forms)</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'visual' ? (
            <div className="space-y-4">
              {activeForm.sections.map((sec, sIdx) => {
                const isExpanded = expandedSections[sec.id];

                return (
                  <div
                    key={sec.id}
                    className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs"
                  >
                    {/* Dimension Section Header */}
                    <div
                      onClick={() => toggleSection(sec.id)}
                      className="p-4 bg-slate-50 hover:bg-slate-100/80 cursor-pointer flex items-center justify-between transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-xs shadow-xs">
                          {sIdx + 1}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold uppercase tracking-wider font-mono text-slate-500">
                              {sec.code}
                            </span>
                            <span className="text-[10px] text-slate-400">•</span>
                            <span className="text-[10px] text-slate-500">
                              {sec.questions?.length || 0} Criterios
                            </span>
                          </div>
                          <h4 className="font-bold text-slate-900 text-sm">{sec.label}</h4>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Section Body */}
                    {isExpanded && (
                      <div className="p-5 space-y-4 border-t border-slate-200">
                        {sec.description && (
                          <p className="text-xs text-slate-600 italic bg-amber-50/50 p-3 rounded-xl border border-amber-100">
                            {sec.description}
                          </p>
                        )}

                        <div className="space-y-4 pl-2 sm:pl-4">
                          {sec.questions?.map((q, qIdx) => (
                            <div
                              key={q.id}
                              className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200 space-y-3"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <span className="text-[10px] font-mono text-amber-700 font-bold uppercase">
                                    {q.code}
                                  </span>
                                  <h5 className="font-bold text-xs text-slate-900 mt-0.5">
                                    {q.label}
                                  </h5>
                                  {q.description && (
                                    <p className="text-[11px] text-slate-500 mt-0.5">
                                      {q.description}
                                    </p>
                                  )}
                                </div>
                                <span className="text-[10px] px-2 py-0.5 bg-white border border-slate-200 text-slate-600 rounded font-semibold shrink-0">
                                  Plantilla: {q.card_template.code}
                                </span>
                              </div>

                              {/* Field Groups */}
                              <div className="space-y-3 pt-2">
                                {q.card_template.field_groups.map((fg) => (
                                  <div key={fg.id} className="space-y-2">
                                    <div className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
                                      {fg.label} ({fg.fields.length} campos)
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                                      {fg.fields.map((f) => (
                                        <div
                                          key={f.id}
                                          className="p-3 bg-white rounded-xl border border-slate-200 text-xs space-y-1.5"
                                        >
                                          <div className="flex items-start justify-between gap-2">
                                            <span className="font-semibold text-slate-800 leading-snug">
                                              {f.label}
                                            </span>
                                            <span className="text-[10px] font-mono font-bold uppercase px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded shrink-0">
                                              {f.field_type_code}
                                            </span>
                                          </div>

                                          {f.help_text && (
                                            <p className="text-[11px] text-slate-500">
                                              {f.help_text}
                                            </p>
                                          )}

                                          {f.choices && f.choices.length > 0 && (
                                            <div className="pt-1.5 space-y-1 border-t border-slate-100">
                                              <div className="text-[10px] font-semibold text-slate-400">
                                                Opciones de ponderación:
                                              </div>
                                              <div className="flex flex-wrap gap-1">
                                                {f.choices.map((ch) => (
                                                  <span
                                                    key={ch.id}
                                                    className="px-2 py-0.5 bg-slate-50 text-slate-700 border border-slate-200 rounded text-[10px]"
                                                  >
                                                    {ch.label}{' '}
                                                    <strong className="text-amber-600">
                                                      ({ch.score_weight} pts)
                                                    </strong>
                                                  </span>
                                                ))}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-slate-900 text-white p-3.5 rounded-t-2xl">
                <div className="flex items-center gap-2 text-xs">
                  <FileCode className="w-4 h-4 text-amber-400" />
                  <span className="font-mono">Payload JSON • POST /forms</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyJson}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white text-xs rounded-lg flex items-center gap-1.5 transition-colors"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                    )}
                    <span>{copied ? 'Copiado' : 'Copiar JSON'}</span>
                  </button>
                  <button
                    onClick={() => handleDownloadJson(activeForm)}
                    className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Descargar</span>
                  </button>
                </div>
              </div>

              <pre className="p-4 bg-slate-950 text-emerald-400 font-mono text-[11px] rounded-b-2xl overflow-x-auto max-h-[500px]">
                {JSON.stringify(activeForm, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Modal for Building / Editing Forms */}
      <FormBuilderModal
        key={editingForm ? `edit-${editingForm.id}-${editingForm.version}` : 'new-form'}
        isOpen={showBuilderModal}
        onClose={() => setShowBuilderModal(false)}
        onSave={handleSaveFormFromBuilder}
        initialForm={editingForm}
      />
    </div>
  );
};
