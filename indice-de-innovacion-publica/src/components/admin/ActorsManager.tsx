import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import {
  Building2,
  Plus,
  Trash2,
  Search,
  Filter,
  UserCheck,
  X,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Layers,
} from 'lucide-react';
import { Actor, ActorCreatePayload } from '../../types';

interface ActorsManagerProps {
  onImpersonateEntity?: (actor: Actor) => void;
}

export const ActorsManager: React.FC<ActorsManagerProps> = ({ onImpersonateEntity }) => {
  const { actors, segments, createActor, deleteActor } = useApp();
  const { switchRole, switchEntity } = useAuth();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSegmentFilter, setSelectedSegmentFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New Actor Form state
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [mission, setMission] = useState('');
  const [vision, setVision] = useState('');
  const [actorSegmentId, setActorSegmentId] = useState('');

  const filteredActors = actors.filter((actor) => {
    const matchesSearch =
      actor.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (actor.description && actor.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesSegment =
      selectedSegmentFilter === 'all' || actor.actor_segment_id === selectedSegmentFilter;
    return matchesSearch && matchesSegment;
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!label.trim()) {
      setErrorMsg('El nombre de la entidad es obligatorio.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: ActorCreatePayload = {
        label: label.trim(),
        description: description.trim() || null,
        mission: mission.trim() || null,
        vision: vision.trim() || null,
        actor_segment_id: actorSegmentId || null,
      };

      await createActor(payload);
      setSuccessMsg('Entidad creada y registrada exitosamente.');
      setShowCreateModal(false);
      // Reset form
      setLabel('');
      setDescription('');
      setMission('');
      setVision('');
      setActorSegmentId('');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err?.message || 'Error al crear la entidad.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string, actorLabel: string) => {
    if (confirm(`¿Está seguro de eliminar la entidad "${actorLabel}"? (DELETE /actors/delete/${id})`)) {
      try {
        await deleteActor(id);
        setSuccessMsg(`Entidad "${actorLabel}" eliminada.`);
        setTimeout(() => setSuccessMsg(null), 3000);
      } catch (err: any) {
        alert(err?.message || 'Error al eliminar');
      }
    }
  };

  const handleImpersonate = (actor: Actor) => {
    switchRole('entity');
    switchEntity(actor.id, actor.label);
    if (onImpersonateEntity) onImpersonateEntity(actor);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
              Directorio Institucional
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600">
              /public/actors
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">Gestión de Actores (Entidades)</h2>
          <p className="text-xs text-slate-500">
            Administre las entidades distritales participantes en la medición del Índice de Innovación Pública.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2 self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Registrar Nueva Entidad</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar entidad por nombre o descripción..."
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={selectedSegmentFilter}
            onChange={(e) => setSelectedSegmentFilter(e.target.value)}
            className="w-full sm:w-64 px-3 py-2 text-xs border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
          >
            <option value="all">Todos los Sectores / Segmentos ({actors.length})</option>
            {segments.map((seg) => (
              <option key={seg.id} value={seg.id}>
                {seg.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Actors Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredActors.map((actor) => {
          const seg = segments.find((s) => s.id === actor.actor_segment_id);

          return (
            <div
              key={actor.id}
              className="bg-white rounded-2xl border border-slate-200 hover:border-slate-300 p-5 shadow-xs flex flex-col justify-between space-y-4 hover:shadow-md transition-all group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2 bg-indigo-50 text-indigo-700 rounded-xl">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 truncate max-w-[140px]">
                    {actor.id}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-snug group-hover:text-indigo-900 transition-colors">
                    {actor.label}
                  </h3>
                  <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700">
                    {seg?.label || actor.actor_segment?.label || 'Sin Sector Asignado'}
                  </span>
                </div>

                <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed">
                  {actor.description || actor.mission || 'Sin descripción registrada.'}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => handleImpersonate(actor)}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-indigo-50 text-indigo-700 hover:text-indigo-900 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  title="Diligenciar diagnóstico como esta entidad"
                >
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>Diligenciar IIP</span>
                </button>

                <button
                  onClick={() => handleDelete(actor.id, actor.label)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  title="Eliminar entidad"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {filteredActors.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-xs text-slate-500">
          No se encontraron entidades con los filtros seleccionados.
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-sm">Registrar Nueva Entidad (POST /actors/new)</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4 text-xs">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Nombre de la Entidad (label) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="ej: Secretaría Distrital de Salud (SDS)"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Sector o Segmento de Actor</label>
                <select
                  value={actorSegmentId}
                  onChange={(e) => setActorSegmentId(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                >
                  <option value="">Seleccionar Sector / Segmento...</option>
                  {segments.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Descripción de la Entidad</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Breve resumen de las funciones misionales..."
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Misión Institucional</label>
                <textarea
                  rows={2}
                  value={mission}
                  onChange={(e) => setMission(e.target.value)}
                  placeholder="Misión oficial de la entidad..."
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Visión Institucional</label>
                <textarea
                  rows={2}
                  value={vision}
                  onChange={(e) => setVision(e.target.value)}
                  placeholder="Visión estratégica..."
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl font-semibold"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold shadow-xs flex items-center gap-2 disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Crear Actor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
