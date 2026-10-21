import React from 'react';
import { AlertCircle, CalendarClock, FileText, Loader2, PlayCircle, CheckCircle2 } from 'lucide-react';
import { EntityAssignment } from '../../types';

export const STATUS_LABEL: Record<EntityAssignment['status'], string> = {
  pending: 'Pendiente',
  in_progress: 'En progreso',
  submitted: 'Enviado',
};

const STATUS_STYLE: Record<EntityAssignment['status'], string> = {
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  in_progress: 'bg-blue-50 text-blue-700 border-blue-200',
  submitted: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

export const formatDate = (iso?: string) =>
  iso ? new Date(iso.length === 10 ? `${iso}T00:00:00` : iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' }) : '—';

interface AssignmentsState {
  assignments: EntityAssignment[];
  loading: boolean;
  error: string | null;
}

export const ProgressBar: React.FC<{ value: number; status: EntityAssignment['status'] }> = ({ value, status }) => (
  <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
    <div
      className={`h-full rounded-full transition-all ${status === 'submitted' ? 'bg-emerald-500' : 'bg-blue-600'}`}
      style={{ width: `${value}%` }}
    />
  </div>
);

export const AssignmentsGate: React.FC<AssignmentsState & { children: React.ReactNode }> = ({
  assignments,
  loading,
  error,
  children,
}) => {
  if (loading)
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-gray-500 text-sm">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" /> Cargando formularios asignados…
      </div>
    );
  if (error)
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
        <span>{error}</span>
      </div>
    );
  if (assignments.length === 0)
    return (
      <div className="py-16 text-center text-sm text-gray-500">
        <FileText className="w-10 h-10 mx-auto mb-3 text-gray-300" />
        Aún no tienes formularios asignados. Cuando un administrador te asigne uno, aparecerá aquí.
      </div>
    );
  return <>{children}</>;
};

export const EntityFormsView: React.FC<AssignmentsState & { onFill: (a: EntityAssignment) => void }> = ({
  onFill,
  ...state
}) => (
  <div className="space-y-6">
    <div>
      <h2 className="text-xl font-bold text-gray-800">Formularios asignados</h2>
      <p className="text-sm text-gray-500 mt-1">Formularios que debes diligenciar en nombre de tu entidad.</p>
    </div>

    <AssignmentsGate {...state}>
      <div className="space-y-4">
        {state.assignments.map((a) => (
          <article key={a.id} className="rounded-2xl border border-gray-200 p-5 hover:border-blue-200 hover:shadow-md transition-all">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <span className="text-xs font-semibold text-blue-600">{a.form_code}</span>
                <h3 className="text-base font-bold text-gray-800">{a.form_label}</h3>
              </div>
              <span className={`px-3 py-1 rounded-full border text-xs font-semibold ${STATUS_STYLE[a.status]}`}>
                {STATUS_LABEL[a.status]}
              </span>
            </div>

            {a.form_description && <p className="text-sm text-gray-500 mt-2 line-clamp-2">{a.form_description}</p>}

            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
              <span className="flex items-center gap-1.5">
                <CalendarClock className="w-3.5 h-3.5" /> Asignado: {formatDate(a.assigned_at)}
              </span>
              <span className="flex items-center gap-1.5">
                <CalendarClock className="w-3.5 h-3.5" /> Fecha límite: {formatDate(a.due_date)}
              </span>
            </div>
            {a.notes && <p className="mt-2 text-xs text-gray-500 italic">“{a.notes}”</p>}

            <div className="mt-4 flex items-center gap-4">
              <div className="flex-1">
                <ProgressBar value={a.completion_percentage} status={a.status} />
              </div>
              <span className="text-xs font-semibold text-gray-600 w-10 text-right">{a.completion_percentage}%</span>
              <button
                type="button"
                onClick={() => onFill(a)}
                className="flex items-center gap-2 py-2 px-4 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all cursor-pointer"
              >
                {a.status === 'submitted' ? <CheckCircle2 className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
                {a.status === 'submitted' ? 'Ver' : a.status === 'in_progress' ? 'Continuar' : 'Diligenciar'}
              </button>
            </div>
          </article>
        ))}
      </div>
    </AssignmentsGate>
  </div>
);

export const EntityProgressView: React.FC<AssignmentsState> = (state) => {
  const { assignments } = state;
  const total = assignments.length;
  const overall = total ? Math.round(assignments.reduce((s, a) => s + a.completion_percentage, 0) / total) : 0;
  const count = (s: EntityAssignment['status']) => assignments.filter((a) => a.status === s).length;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Barra de proceso</h2>
        <p className="text-sm text-gray-500 mt-1">Avance de tu entidad en los formularios asignados.</p>
      </div>

      <AssignmentsGate {...state}>
        <div className="rounded-2xl bg-blue-50 border border-blue-100 p-5">
          <div className="flex items-end justify-between mb-3">
            <span className="text-sm font-semibold text-blue-800">Avance general</span>
            <span className="text-3xl font-bold text-blue-700">{overall}%</span>
          </div>
          <div className="w-full h-3 bg-white rounded-full overflow-hidden" role="progressbar" aria-valuenow={overall} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full bg-blue-600 rounded-full transition-all" style={{ width: `${overall}%` }} />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            {(['pending', 'in_progress', 'submitted'] as const).map((s) => (
              <div key={s} className="bg-white rounded-xl py-3 border border-blue-100">
                <div className="text-xl font-bold text-gray-800">{count(s)}</div>
                <div className="text-xs text-gray-500">{STATUS_LABEL[s]}</div>
              </div>
            ))}
          </div>
        </div>

        <ul className="space-y-4">
          {assignments.map((a) => (
            <li key={a.id}>
              <div className="flex items-center justify-between text-sm mb-1.5">
                <span className="font-semibold text-gray-700 truncate pr-3">{a.form_label}</span>
                <span className="text-gray-500 shrink-0">
                  {STATUS_LABEL[a.status]} · {a.completion_percentage}%
                </span>
              </div>
              <ProgressBar value={a.completion_percentage} status={a.status} />
            </li>
          ))}
        </ul>
      </AssignmentsGate>
    </div>
  );
};
