import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { useFormSubmission } from '../../context/FormSubmissionContext';
import {
  Building2,
  Sparkles,
  Award,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingUp,
  FileText,
  Rocket,
  ShieldCheck,
  Calendar,
  Layers,
  ChevronRight,
  BookOpen,
  FileCheck2,
  AlertCircle,
  Check,
  Download,
} from 'lucide-react';

interface EntityDashboardProps {
  onStartDiagnostic: () => void;
  onViewHistory: () => void;
  onViewProfile: () => void;
}

export const EntityDashboard: React.FC<EntityDashboardProps> = ({
  onStartDiagnostic,
  onViewHistory,
  onViewProfile,
}) => {
  const { user } = useAuth();
  const { actors, forms, activeForm, assignments, submissions, setActiveFormById } = useApp();
  const { progress } = useFormSubmission();

  const currentActor = actors.find((a) => a.id === user?.actor_id) || actors[0];

  // Find assignments specifically for this entity
  const myAssignments = assignments.filter((a) => a.actor_id === currentActor?.id);

  // Default to first assignment if exists
  const activeAssignment = myAssignments[0];
  const assignedForm = activeAssignment
    ? forms.find((f) => f.id === activeAssignment.form_id) || activeForm
    : activeForm;

  // Submissions for this entity
  const entitySubmissions = submissions.filter((s) => s.actor_id === currentActor?.id);
  const latestSubmission = entitySubmissions[0];

  const completionPercent = activeAssignment
    ? activeAssignment.completion_percentage || progress
    : progress;
  const isSubmitted = activeAssignment?.status === 'submitted' || !!latestSubmission;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Entity Welcome Hero (LabCapital / Veeduría Distrital Theme) */}
      <div className="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-800 relative overflow-hidden">
        {/* Subtle decorative glow */}
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-wider bg-amber-500/20 text-amber-400 border border-amber-400/30 uppercase">
                Portal de la Entidad Distrital
              </span>
              <span className="text-xs text-slate-400">Vigencia Oficial {assignedForm.year}</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              {currentActor?.label}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
              {currentActor?.mission ||
                currentActor?.description ||
                'Entidad distrital comprometida con el fortalecimiento de capacidades, cultura y proyectos de innovación pública en Bogotá D.C.'}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <button
              onClick={() => {
                if (activeAssignment?.form_id) {
                  setActiveFormById(activeAssignment.form_id);
                }
                onStartDiagnostic();
              }}
              className="px-6 py-3.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-black text-xs rounded-xl shadow-lg shadow-amber-500/20 transition-all flex items-center justify-center gap-2"
            >
              <span>
                {isSubmitted
                  ? 'Ver Radicación Oficial'
                  : completionPercent > 0
                  ? 'Continuar Diligenciamiento'
                  : 'Solucionar Formulario Asignado'}
              </span>
              <ArrowRight className="w-4 h-4 text-slate-950" />
            </button>
            <button
              onClick={onViewProfile}
              className="px-4 py-3.5 bg-slate-800/90 hover:bg-slate-800 text-slate-200 font-semibold text-xs rounded-xl border border-slate-700/80 transition-colors text-center"
            >
              Ficha Entidad
            </button>
          </div>
        </div>
      </div>

      {/* Assigned Form Card (High Priority Callout) */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center font-bold">
              <FileCheck2 className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600">
                  Formulario Oficial Asignado por la Veeduría
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                  {assignedForm.code}
                </span>
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 mt-0.5">
                {assignedForm.label}
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {isSubmitted ? (
              <span className="px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full font-bold text-xs flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Radicado Exitosamente</span>
              </span>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 px-3 py-1 rounded-xl border border-slate-200">
                <Calendar className="w-3.5 h-3.5 text-amber-600" />
                <span>
                  Plazo límite:{' '}
                  <strong>
                    {activeAssignment
                      ? new Date(activeAssignment.due_date).toLocaleDateString('es-CO', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : '31 de Octubre, 2026'}
                  </strong>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Progress and Solver CTA Box */}
        <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div className="space-y-2 flex-1">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-700">Estado de Diligenciamiento:</span>
              <span className="font-mono font-bold text-amber-700 text-sm">
                {completionPercent}% Completado
              </span>
            </div>
            <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isSubmitted ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
                style={{ width: `${completionPercent}%` }}
              />
            </div>
            <p className="text-[11px] text-slate-500">
              {isSubmitted
                ? `Formulario radicado el ${
                    latestSubmission?.submitted_at
                      ? new Date(latestSubmission.submitted_at).toLocaleString('es-CO')
                      : 'recientemente'
                  } con radicado oficial ${latestSubmission?.id || 'RAD-2026-DIST'}.`
                : 'Complete las respuestas y evidencias de cada dimensión para formalizar la radicación institucional ante la Veeduría Distrital.'}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-2">
            <button
              onClick={() => {
                if (activeAssignment?.form_id) {
                  setActiveFormById(activeAssignment.form_id);
                }
                onStartDiagnostic();
              }}
              className="w-full sm:w-auto px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2"
            >
              <span>{isSubmitted ? 'Revisar Respuestas' : 'Diligenciar Cuestionario'}</span>
              <ChevronRight className="w-4 h-4 text-amber-400" />
            </button>
          </div>
        </div>

        {/* Form Dimensions Overview Grid */}
        <div className="space-y-3 pt-2">
          <div className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Dimensiones de Evaluación del Formulario Asignado ({assignedForm.sections.length})
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {assignedForm.sections.map((sec, idx) => {
              const qCount = sec.questions?.length || 0;

              return (
                <div
                  key={sec.id}
                  className="p-4 bg-white rounded-2xl border border-slate-200 space-y-2 hover:border-amber-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="w-6 h-6 rounded-lg bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-xs">
                      {idx + 1}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">{sec.code}</span>
                  </div>

                  <h4 className="font-bold text-xs text-slate-900 line-clamp-2 leading-snug">
                    {sec.label}
                  </h4>
                  <p className="text-[11px] text-slate-500 line-clamp-2">{sec.description}</p>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500">
                    <span>{qCount} Criterios</span>
                    <span className="text-amber-600 font-semibold">Vigencia {assignedForm.year}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Official Guidelines & LabCapital Methodology Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900 text-sm">
                Metodología LabCapital • Veeduría Distrital
              </h4>
              <p className="text-[11px] text-slate-500">
                Modelo estandarizado de medición de innovación pública
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            El Índice de Innovación Pública (IIP) evalúa las condiciones institucionales de las
            entidades de Bogotá D.C. para diseñar, experimentar e implementar soluciones innovadoras
            que generen valor público a la ciudadanía.
          </p>
          <ul className="text-xs text-slate-600 space-y-1.5 pl-4 list-disc">
            <li>Diligenciamiento guiado con guardado automático de borradores.</li>
            <li>Inclusión de iniciativas y proyectos en formato de ficha repetible.</li>
            <li>Generación de radicado oficial distrital con firma de tiempo.</li>
          </ul>
        </div>

        <div className="p-6 bg-white rounded-3xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center font-bold">
              <Award className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900 text-sm">Historial & Radicaciones</h4>
              <p className="text-[11px] text-slate-500">Comprobantes y certificados oficiales</p>
            </div>
          </div>

          {latestSubmission ? (
            <div className="p-4 bg-emerald-50/70 rounded-2xl border border-emerald-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-900">
                  Último Radicado Oficial
                </span>
                <span className="text-[10px] font-mono font-bold bg-white px-2 py-0.5 rounded border border-emerald-200 text-emerald-800">
                  {latestSubmission.id}
                </span>
              </div>
              <div className="text-xs text-emerald-800">
                Puntaje Estimado: <strong>{latestSubmission.score?.toFixed(1)} / 100</strong>
              </div>
              <button
                onClick={onViewHistory}
                className="text-xs font-bold text-emerald-800 hover:text-emerald-900 underline flex items-center gap-1 mt-1"
              >
                <span>Ver historial completo y descargar certificado</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-xs text-slate-500 space-y-2">
              <p>No se registran radicaciones completadas para la vigencia actual.</p>
              <button
                onClick={() => {
                  if (activeAssignment?.form_id) {
                    setActiveFormById(activeAssignment.form_id);
                  }
                  onStartDiagnostic();
                }}
                className="text-xs font-bold text-amber-700 hover:text-amber-800 flex items-center gap-1"
              >
                <span>Comenzar a solucionar formulario</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
