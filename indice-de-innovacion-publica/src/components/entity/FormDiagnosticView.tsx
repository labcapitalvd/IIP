import React, { useState } from 'react';
import { useFormSubmission } from '../../context/FormSubmissionContext';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { SubmissionReviewModal } from './SubmissionReviewModal';
import {
  Building2,
  Sparkles,
  Cpu,
  Rocket,
  CheckCircle2,
  AlertCircle,
  Plus,
  Trash2,
  ChevronRight,
  ChevronLeft,
  Send,
  Save,
  Info,
  Calendar,
  Layers,
  HelpCircle,
  FolderOpen,
} from 'lucide-react';
import { FormField } from '../../types';

interface FormDiagnosticViewProps {
  onBackToDashboard: () => void;
}

export const FormDiagnosticView: React.FC<FormDiagnosticViewProps> = ({ onBackToDashboard }) => {
  const {
    activeForm,
    activeSectionIndex,
    activeSection,
    answers,
    cardEntries,
    errors,
    progress,
    setActiveSectionIndex,
    nextSection,
    prevSection,
    setFieldValue,
    addCardEntry,
    removeCardEntry,
    setCardEntryFieldValue,
    setCardEntryTitle,
    validateCurrentSection,
    validateAllSections,
    resetFormState,
    lastSubmittedId,
    submitSuccess,
  } = useFormSubmission();

  const { actors } = useApp();
  const { user } = useAuth();
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [draftSavedToast, setDraftSavedToast] = useState(false);

  const currentActor = actors.find((a) => a.id === user?.actor_id) || actors[0];

  const handleManualSaveDraft = () => {
    setDraftSavedToast(true);
    setTimeout(() => setDraftSavedToast(false), 2000);
  };

  const handleOpenReview = () => {
    const isValid = validateAllSections();
    if (!isValid) {
      alert('Por favor complete todos los campos obligatorios antes de continuar.');
      return;
    }
    setShowReviewModal(true);
  };

  // Get icon component based on section icon_name
  const getSectionIcon = (name?: string) => {
    switch (name) {
      case 'Building2':
        return <Building2 className="w-4 h-4" />;
      case 'Sparkles':
        return <Sparkles className="w-4 h-4" />;
      case 'Cpu':
        return <Cpu className="w-4 h-4" />;
      case 'Rocket':
      default:
        return <Rocket className="w-4 h-4" />;
    }
  };

  // Render individual form field
  const renderField = (
    field: FormField,
    value: any,
    onChange: (val: any) => void,
    errorKey?: string
  ) => {
    const hasError = errorKey ? !!errors[errorKey] : !!errors[field.id];
    const errorMessage = errorKey ? errors[errorKey] : errors[field.id];

    return (
      <div key={field.id} className="space-y-1.5 pt-2 first:pt-0">
        <div className="flex items-start justify-between gap-2">
          <label className="text-xs font-semibold text-slate-800 leading-snug">
            {field.label}
            {field.is_required && <span className="text-rose-500 ml-1 font-bold">*</span>}
          </label>
        </div>

        {field.help_text && (
          <p className="text-[11px] text-slate-500 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
            {field.help_text}
          </p>
        )}

        {/* Dynamic field types */}
        {field.field_type_code === 'boolean' && (
          <div className="flex items-center gap-3 pt-1">
            <button
              type="button"
              onClick={() => onChange(true)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all flex items-center gap-2 ${
                value === true
                  ? 'bg-emerald-600 border-emerald-600 text-white shadow-xs'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Sí / Cumple</span>
            </button>
            <button
              type="button"
              onClick={() => onChange(false)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold border transition-all flex items-center gap-2 ${
                value === false
                  ? 'bg-slate-700 border-slate-700 text-white shadow-xs'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
              }`}
            >
              <span>No / En Proceso</span>
            </button>
          </div>
        )}

        {field.field_type_code === 'numeric' && (
          <div className="relative max-w-xs">
            <input
              type="number"
              min={field.min_value ?? 0}
              max={field.max_value}
              value={value ?? ''}
              onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder={field.placeholder || '0'}
              className={`w-full px-3.5 py-2 rounded-xl border text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none transition-colors ${
                hasError ? 'border-rose-300 bg-rose-50/50' : 'border-slate-300 bg-white'
              }`}
            />
            {field.unit && (
              <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-medium">
                {field.unit}
              </span>
            )}
          </div>
        )}

        {field.field_type_code === 'text' && (
          <div>
            <textarea
              rows={3}
              value={value ?? ''}
              onChange={(e) => onChange(e.target.value)}
              placeholder={field.placeholder || 'Escriba una respuesta detallada...'}
              className={`w-full px-3.5 py-2 rounded-xl border text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-colors ${
                hasError ? 'border-rose-300 bg-rose-50/50' : 'border-slate-300 bg-white'
              }`}
            />
          </div>
        )}

        {field.field_type_code === 'date' && (
          <div className="max-w-xs">
            <input
              type="date"
              value={value ?? ''}
              onChange={(e) => onChange(e.target.value)}
              className={`w-full px-3.5 py-2 rounded-xl border text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-colors ${
                hasError ? 'border-rose-300 bg-rose-50/50' : 'border-slate-300 bg-white'
              }`}
            />
          </div>
        )}

        {field.field_type_code === 'singlechoice' && field.choices && (
          <div className="space-y-2 pt-1">
            {field.choices.map((choice) => {
              const isSelected = value === choice.id || value === choice.code;
              return (
                <button
                  key={choice.id}
                  type="button"
                  onClick={() => onChange(choice.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                    isSelected
                      ? 'bg-indigo-50/70 border-indigo-600 ring-1 ring-indigo-600 text-indigo-950 font-medium'
                      : 'bg-white border-slate-200 hover:border-slate-300 text-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        isSelected ? 'border-indigo-600 bg-indigo-600' : 'border-slate-300'
                      }`}
                    >
                      {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </div>
                    <span className="text-xs">{choice.label}</span>
                  </div>
                  {choice.score_weight !== undefined && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-mono">
                      {choice.score_weight} pts
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {hasError && (
          <p className="text-[11px] text-rose-600 flex items-center gap-1 font-medium mt-1">
            <AlertCircle className="w-3 h-3 shrink-0" />
            {errorMessage}
          </p>
        )}
      </div>
    );
  };

  // Success screen when form was submitted
  if (submitSuccess) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
        <div className="bg-white rounded-3xl p-8 sm:p-12 text-center border border-slate-200 shadow-xl space-y-6 animate-in zoom-in-95 duration-200">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold tracking-wider text-emerald-700 uppercase">
              Envío Oficial Registrado con Éxito
            </span>
            <h2 className="text-2xl font-bold text-slate-900">
              ¡Diagnóstico del IIP 2026 Completado!
            </h2>
            <p className="text-sm text-slate-600 max-w-lg mx-auto">
              La información suministrada por <span className="font-semibold text-slate-900">{currentActor.label}</span>{' '}
              ha sido registrada y consolidada en la plataforma del Índice de Innovación Pública.
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 inline-block text-left text-xs space-y-1.5 font-mono">
            <div className="text-slate-500">Formulario: <span className="text-slate-800 font-semibold">{activeForm.label}</span></div>
            <div className="text-slate-500">ID de Envío: <span className="text-indigo-600">{lastSubmittedId}</span></div>
            <div className="text-slate-500">Fecha y Hora: <span className="text-slate-800">{new Date().toLocaleString()}</span></div>
          </div>

          <div className="flex items-center justify-center gap-3 pt-4">
            <button
              onClick={() => {
                resetFormState();
                onBackToDashboard();
              }}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors"
            >
              Volver al Panel de la Entidad
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!activeSection) return null;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Banner with Entity Context & Progress */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-indigo-50 text-indigo-700 rounded-xl mt-0.5">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider">
                Diligenciamiento Oficial
              </span>
              <span className="text-[10px] px-2 py-0.2 rounded font-mono bg-slate-100 text-slate-600">
                {activeForm.code}
              </span>
            </div>
            <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-tight">
              {currentActor.label}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">{currentActor.actor_segment?.label || 'Distrito Capital'}</p>
          </div>
        </div>

        {/* Progress Bar & Actions */}
        <div className="flex items-center gap-4">
          <div className="w-48 sm:w-56 text-right">
            <div className="flex items-center justify-between text-xs font-semibold mb-1">
              <span className="text-slate-500">Progreso Total</span>
              <span className="text-indigo-600">{progress}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <button
            onClick={handleManualSaveDraft}
            title="Guardar borrador local"
            className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-50 border border-slate-200 rounded-xl transition-colors text-xs flex items-center gap-1.5"
          >
            <Save className="w-4 h-4" />
            <span className="hidden sm:inline">Borrador</span>
          </button>
        </div>
      </div>

      {draftSavedToast && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Borrador guardado localmente de forma segura.</span>
        </div>
      )}

      {/* Stepper Navigation: 4 Dimensions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {activeForm.sections.map((section, idx) => {
          const isActive = idx === activeSectionIndex;
          const isDone = idx < activeSectionIndex;

          return (
            <button
              key={section.id}
              onClick={() => setActiveSectionIndex(idx)}
              className={`p-3 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                isActive
                  ? 'bg-indigo-900 border-indigo-900 text-white shadow-xs ring-2 ring-indigo-600 ring-offset-2'
                  : 'bg-white border-slate-200 hover:border-indigo-300 text-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`p-1.5 rounded-lg ${
                    isActive ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {getSectionIcon(section.icon_name)}
                </div>
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    isActive ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  Dim {idx + 1}
                </span>
              </div>
              <span className={`text-xs font-semibold line-clamp-2 ${isActive ? 'text-white' : 'text-slate-800'}`}>
                {section.label.split(':')[1]?.trim() || section.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Section Body */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Section Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-700">
              Dimensión #{activeSectionIndex + 1} de {activeForm.sections.length}
            </span>
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 mt-0.5">{activeSection.label}</h3>
          {activeSection.description && (
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">{activeSection.description}</p>
          )}
        </div>

        {/* Section Questions & Fields */}
        <div className="p-6 space-y-8 divide-y divide-slate-100">
          {activeSection.questions?.map((question) => {
            const isRepeatable = question.card_template.is_repeatable;

            if (isRepeatable) {
              // Dimensión 4: Repeatable Initiatives Card Entries
              const entries = cardEntries[question.id] || [];

              return (
                <div key={question.id} className="pt-6 first:pt-0 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <Rocket className="w-4 h-4 text-indigo-600" />
                        {question.label}
                      </h4>
                      {question.description && (
                        <p className="text-xs text-slate-500 mt-0.5">{question.description}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => addCardEntry(question.id, question.card_template.id)}
                      className="px-3.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors self-start"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Registrar Otra Iniciativa</span>
                    </button>
                  </div>

                  {errors[question.id] && (
                    <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{errors[question.id]}</span>
                    </div>
                  )}

                  {/* Cards List */}
                  <div className="space-y-4">
                    {entries.map((entry, entryIndex) => (
                      <div
                        key={entry.id}
                        className="bg-slate-50/70 border border-slate-200 rounded-2xl p-5 space-y-4 relative group hover:border-slate-300 transition-colors"
                      >
                        <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
                          <div className="flex items-center gap-2.5 flex-1">
                            <span className="w-6 h-6 rounded-lg bg-indigo-600 text-white font-bold flex items-center justify-center text-xs">
                              {entryIndex + 1}
                            </span>
                            <input
                              type="text"
                              value={entry.title}
                              onChange={(e) => setCardEntryTitle(question.id, entry.id, e.target.value)}
                              placeholder={`Título de la Iniciativa #${entryIndex + 1}`}
                              className="font-bold text-slate-900 text-sm bg-transparent border-b border-transparent hover:border-slate-300 focus:border-indigo-500 outline-none w-full max-w-lg"
                            />
                          </div>

                          {entries.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeCardEntry(question.id, entry.id)}
                              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                              title="Eliminar esta ficha"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>

                        {/* Fields inside card */}
                        <div className="space-y-4">
                          {question.card_template.field_groups.map((fg) => (
                            <div key={fg.id} className="space-y-3">
                              {fg.label && (
                                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                                  {fg.label}
                                </span>
                              )}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {fg.fields.map((field) => (
                                  <div
                                    key={field.id}
                                    className={field.field_type_code === 'text' ? 'md:col-span-2' : ''}
                                  >
                                    {renderField(
                                      field,
                                      entry.answers[field.id],
                                      (val) =>
                                        setCardEntryFieldValue(question.id, entry.id, field.id, val),
                                      `${entry.id}_${field.id}`
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
              );
            }

            // Standard Single Card Template Questions
            return (
              <div key={question.id} className="pt-6 first:pt-0 space-y-4">
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{question.label}</h4>
                  {question.description && (
                    <p className="text-xs text-slate-500 mt-0.5">{question.description}</p>
                  )}
                </div>

                <div className="space-y-6">
                  {question.card_template.field_groups.map((fg) => (
                    <div key={fg.id} className="space-y-4">
                      {fg.label && (
                        <div className="border-b border-slate-100 pb-1">
                          <span className="text-xs font-bold text-indigo-900">{fg.label}</span>
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {fg.fields.map((field) => (
                          <div
                            key={field.id}
                            className={field.field_type_code === 'text' ? 'md:col-span-2' : ''}
                          >
                            {renderField(field, answers[field.id], (val) =>
                              setFieldValue(field.id, val)
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom Navigation Toolbar */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div>
            <button
              type="button"
              onClick={onBackToDashboard}
              className="text-xs text-slate-500 hover:text-slate-800 font-medium"
            >
              ← Volver al Panel
            </button>
          </div>

          <div className="flex items-center gap-3">
            {activeSectionIndex > 0 && (
              <button
                type="button"
                onClick={prevSection}
                className="px-4 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl transition-colors flex items-center gap-1"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Dimensión Anterior</span>
              </button>
            )}

            {activeSectionIndex < activeForm.sections.length - 1 ? (
              <button
                type="button"
                onClick={() => {
                  const valid = validateCurrentSection();
                  if (valid) nextSection();
                }}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors flex items-center gap-1.5"
              >
                <span>Siguiente Dimensión</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleOpenReview}
                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                <span>Revisar y Enviar Diagnóstico</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Review & Confirm Modal */}
      <SubmissionReviewModal
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        onSuccess={() => setShowReviewModal(false)}
      />
    </div>
  );
};
