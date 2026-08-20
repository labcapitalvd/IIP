import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { FormAssignment } from '../../types';
import {
  FileCheck2,
  Plus,
  Building2,
  Users,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  Search,
  Filter,
  Trash2,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Award,
  Send,
} from 'lucide-react';

interface FormAssignmentsManagerProps {
  onInspectSubmission?: (submissionId: string) => void;
}

export const FormAssignmentsManager: React.FC<FormAssignmentsManagerProps> = ({
  onInspectSubmission,
}) => {
  const {
    assignments,
    forms,
    users,
    actors,
    segments,
    createAssignment,
    batchAssignForm,
    removeAssignment,
  } = useApp();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('all');
  const [selectedFormFilter, setSelectedFormFilter] = useState<string>('all');

  // Assignment Modal State
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignMode, setAssignMode] = useState<'single' | 'sector' | 'all'>('single');
  const [targetFormId, setTargetFormId] = useState(forms[0]?.id || '');
  const [targetUserId, setTargetUserId] = useState(
    users.find((u) => u.role === 'entity')?.id || ''
  );
  const [targetSectorId, setTargetSectorId] = useState(segments[0]?.id || '');
  const [dueDate, setDueDate] = useState('2026-10-31');
  const [notes, setNotes] = useState('');
  const [feedback, setFeedback] = useState<{ success: boolean; message: string } | null>(null);

  const entityUsers = users.filter((u) => u.role === 'entity');

  // Filtered assignments
  const filteredAssignments = assignments.filter((asg) => {
    const matchesSearch =
      asg.form_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asg.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asg.actor_label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (asg.radicado_number && asg.radicado_number.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus =
      selectedStatusFilter === 'all' ? true : asg.status === selectedStatusFilter;

    const matchesForm = selectedFormFilter === 'all' ? true : asg.form_id === selectedFormFilter;

    return matchesSearch && matchesStatus && matchesForm;
  });

  // Calculate Metrics
  const totalCount = assignments.length;
  const submittedCount = assignments.filter((a) => a.status === 'submitted').length;
  const inProgressCount = assignments.filter((a) => a.status === 'in_progress').length;
  const pendingCount = assignments.filter((a) => a.status === 'pending').length;

  const handleCreateAssignment = (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);

    const form = forms.find((f) => f.id === targetFormId) || forms[0];
    if (!form) return;

    if (assignMode === 'single') {
      const user = users.find((u) => u.id === targetUserId);
      if (!user || !user.actor_id) {
        setFeedback({ success: false, message: 'Seleccione un usuario válido.' });
        return;
      }

      createAssignment({
        form_id: form.id,
        user_id: user.id,
        actor_id: user.actor_id,
        due_date: `${dueDate}T23:59:59Z`,
        notes: notes.trim() || undefined,
      });

      setFeedback({
        success: true,
        message: `Formulario "${form.label}" asignado exitosamente a ${user.actor_label}.`,
      });
    } else if (assignMode === 'sector') {
      const sectorUsers = entityUsers.filter((u) => {
        const actor = actors.find((a) => a.id === u.actor_id);
        return actor?.actor_segment_id === targetSectorId;
      });

      if (sectorUsers.length === 0) {
        setFeedback({
          success: false,
          message: 'No hay usuarios de entidades registrados en el sector seleccionado.',
        });
        return;
      }

      batchAssignForm(
        form.id,
        sectorUsers.map((u) => u.id),
        `${dueDate}T23:59:59Z`
      );

      const sector = segments.find((s) => s.id === targetSectorId);
      setFeedback({
        success: true,
        message: `Formulario asignado masivamente a ${sectorUsers.length} entidades del sector "${sector?.label}".`,
      });
    } else if (assignMode === 'all') {
      if (entityUsers.length === 0) {
        setFeedback({
          success: false,
          message: 'No hay usuarios de entidades disponibles para asignar.',
        });
        return;
      }

      batchAssignForm(
        form.id,
        entityUsers.map((u) => u.id),
        `${dueDate}T23:59:59Z`
      );

      setFeedback({
        success: true,
        message: `Formulario asignado a TODAS las ${entityUsers.length} entidades registradas en el Distrito.`,
      });
    }

    setShowAssignModal(false);
  };

  const handleRemoveAssignment = (id: string, actorLabel: string) => {
    if (confirm(`¿Desea revocar la asignación de este formulario para ${actorLabel}?`)) {
      removeAssignment(id);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
              Administración • LabCapital
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600">
              Asignación Oficial de Instrumentos
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
            Asignación de Formularios a Entidades
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Asigne los cuestionarios del IIP de forma individual, sectorial o masiva con fechas límite y directrices técnicas.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAssignModal(true)}
            className="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2"
          >
            <FileCheck2 className="w-4 h-4" />
            <span>Asignar Formulario a Usuarios</span>
          </button>
        </div>
      </div>

      {feedback && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center gap-2 animate-in fade-in ${
            feedback.success
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {feedback.success ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center font-bold">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Total Asignaciones
            </span>
            <div className="text-2xl font-black text-slate-900">{totalCount}</div>
          </div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Radicadas Oficialmente
            </span>
            <div className="text-2xl font-black text-emerald-600">{submittedCount}</div>
          </div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              En Diligenciamiento
            </span>
            <div className="text-2xl font-black text-sky-600">{inProgressCount}</div>
          </div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Pendientes por Iniciar
            </span>
            <div className="text-2xl font-black text-amber-600">{pendingCount}</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por entidad, formulario o radicado..."
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedFormFilter}
            onChange={(e) => setSelectedFormFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
          >
            <option value="all">Todos los Formularios</option>
            {forms.map((f) => (
              <option key={f.id} value={f.id}>
                {f.label} ({f.code})
              </option>
            ))}
          </select>

          <select
            value={selectedStatusFilter}
            onChange={(e) => setSelectedStatusFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
          >
            <option value="all">Todos los Estados</option>
            <option value="pending">Pendientes (0%)</option>
            <option value="in_progress">En Progreso</option>
            <option value="submitted">Radicadas Oficialmente</option>
          </select>
        </div>
      </div>

      {/* Assignments Table */}
      <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-4">Entidad Distrital & Usuario</th>
                <th className="px-6 py-4">Formulario IIP Asignado</th>
                <th className="px-6 py-4">Sector Administrativo</th>
                <th className="px-6 py-4">Fecha Límite</th>
                <th className="px-6 py-4 text-center">Avance / Progreso</th>
                <th className="px-6 py-4 text-center">Estado & Radicado</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredAssignments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    No se encontraron asignaciones de formularios con los filtros actuales.
                  </td>
                </tr>
              ) : (
                filteredAssignments.map((asg) => {
                  const percent = asg.completion_percentage || 0;
                  const isSubmitted = asg.status === 'submitted';

                  return (
                    <tr key={asg.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4">
                        <div className="space-y-0.5">
                          <div className="font-bold text-slate-900 flex items-center gap-1.5">
                            <Building2 className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                            <span>{asg.actor_label}</span>
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono">
                            @{asg.user_name}
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="space-y-0.5 max-w-xs">
                          <div className="font-semibold text-slate-900 truncate">
                            {asg.form_title}
                          </div>
                          <div className="text-[10px] font-mono text-amber-700">
                            {asg.form_code} (Vigencia {asg.form_year})
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          {asg.actor_segment_label || 'Distrital'}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1 text-[11px] text-slate-600">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>
                            {new Date(asg.due_date).toLocaleDateString('es-CO', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                            })}
                          </span>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-center">
                        <div className="w-32 mx-auto space-y-1">
                          <div className="flex items-center justify-between text-[10px] font-bold">
                            <span className="text-slate-500">Progreso:</span>
                            <span
                              className={
                                isSubmitted
                                  ? 'text-emerald-600'
                                  : percent > 0
                                  ? 'text-sky-600'
                                  : 'text-slate-400'
                              }
                            >
                              {percent}%
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                isSubmitted
                                  ? 'bg-emerald-500'
                                  : percent > 0
                                  ? 'bg-sky-500'
                                  : 'bg-slate-300'
                              }`}
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-center">
                        {isSubmitted ? (
                          <div className="space-y-1 inline-flex flex-col items-center">
                            <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Radicado</span>
                            </span>
                            {asg.radicado_number && (
                              <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                {asg.radicado_number}
                              </span>
                            )}
                            {asg.score !== undefined && (
                              <span className="text-[10px] text-amber-700 font-bold">
                                Índice: {asg.score.toFixed(1)} / 100
                              </span>
                            )}
                          </div>
                        ) : percent > 0 ? (
                          <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-sky-50 text-sky-700 border border-sky-200">
                            En Diligenciamiento
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-amber-50 text-amber-700 border border-amber-200">
                            Pendiente por Iniciar
                          </span>
                        )}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleRemoveAssignment(asg.id, asg.actor_label)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                            title="Revocar asignación"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal to Assign Form to Users/Entities */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white w-full max-w-2xl rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-500 text-slate-950 flex items-center justify-center font-bold shadow-md">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">
                    Veeduría Distrital • LabCapital
                  </span>
                  <h3 className="text-base font-bold text-white">
                    Asignar Formulario IIP a Entidades
                  </h3>
                </div>
              </div>
              <button
                onClick={() => setShowAssignModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAssignment} className="p-6 space-y-4">
              {/* Form to Assign */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  1. Formulario de Medición IIP a Asignar <span className="text-rose-500">*</span>
                </label>
                <select
                  value={targetFormId}
                  onChange={(e) => setTargetFormId(e.target.value)}
                  className="w-full text-xs font-semibold px-3 py-2 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                >
                  {forms.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label} ({f.code}) — Vigencia {f.year}
                    </option>
                  ))}
                </select>
              </div>

              {/* Assignment Mode Selector */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  2. Modalidad de Asignación <span className="text-rose-500">*</span>
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setAssignMode('single')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors ${
                      assignMode === 'single'
                        ? 'bg-slate-900 text-white border-slate-900'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    Entidad Individual
                  </button>
                  <button
                    type="button"
                    onClick={() => setAssignMode('sector')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors ${
                      assignMode === 'sector'
                        ? 'bg-slate-900 text-white border-slate-900'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    Por Sector Distrital
                  </button>
                  <button
                    type="button"
                    onClick={() => setAssignMode('all')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors ${
                      assignMode === 'all'
                        ? 'bg-slate-900 text-white border-slate-900'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    Todas las Entidades ({entityUsers.length})
                  </button>
                </div>
              </div>

              {/* Conditional Target Selector */}
              {assignMode === 'single' && (
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Usuario / Entidad Destinataria <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={targetUserId}
                    onChange={(e) => setTargetUserId(e.target.value)}
                    className="w-full text-xs font-semibold px-3 py-2 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  >
                    {entityUsers.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.actor_label} (@{u.username})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {assignMode === 'sector' && (
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Seleccionar Sector Distrital <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={targetSectorId}
                    onChange={(e) => setTargetSectorId(e.target.value)}
                    className="w-full text-xs font-semibold px-3 py-2 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  >
                    {segments.map((seg) => (
                      <option key={seg.id} value={seg.id}>
                        {seg.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {assignMode === 'all' && (
                <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900">
                  ⚠️ Se generará una asignación oficial para cada una de las{' '}
                  <strong>{entityUsers.length} entidades</strong> registradas en el sistema.
                </div>
              )}

              {/* Due Date & Notes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Fecha Límite de Radicación <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="date"
                    required
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Directrices o Notas para la Entidad
                  </label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Ej. Adjuntar soporte de comités de innovación..."
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl bg-white focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl border border-slate-300 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold rounded-xl shadow-md transition-all flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  <span>Confirmar Asignación</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
