import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  Layers,
  Plus,
  Trash2,
  Building2,
  X,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { ActorSegmentCreatePayload } from '../../types';

export const SegmentsManager: React.FC = () => {
  const { segments, actors, createSegment, deleteSegment } = useApp();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [label, setLabel] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!label.trim()) {
      setErrorMsg('El nombre del segmento es obligatorio.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: ActorSegmentCreatePayload = {
        label: label.trim(),
        description: description.trim() || null,
      };

      await createSegment(payload);
      setSuccessMsg('Segmento / Sector distrital registrado.');
      setShowCreateModal(false);
      setLabel('');
      setDescription('');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err?.message || 'Error al crear segmento.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string, segmentLabel: string) => {
    if (confirm(`¿Eliminar el segmento "${segmentLabel}"? (DELETE /actor_segments/delete/${id})`)) {
      try {
        await deleteSegment(id);
        setSuccessMsg(`Segmento "${segmentLabel}" eliminado.`);
        setTimeout(() => setSuccessMsg(null), 3000);
      } catch (err: any) {
        alert(err?.message || 'Error al eliminar segmento.');
      }
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
              Clasificación Sectorial
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600">
              /public/actor_segments
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">Segmentos de Actor (Sectores)</h2>
          <p className="text-xs text-slate-500">
            Agrupe entidades públicas por sectores administrativos o niveles de coordinación distrital.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2 self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Crear Nuevo Sector</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Segments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {segments.map((segment) => {
          const associatedActors = actors.filter((a) => a.actor_segment_id === segment.id);

          return (
            <div
              key={segment.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between space-y-4 hover:shadow-md transition-all group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2 bg-indigo-50 text-indigo-700 rounded-xl">
                    <Layers className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                    {segment.id}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-snug">{segment.label}</h3>
                  <span className="text-xs text-indigo-600 font-semibold mt-1 inline-block">
                    {associatedActors.length} entidades vinculadas
                  </span>
                </div>

                <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed">
                  {segment.description || 'Sin descripción sectorial.'}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  {associatedActors.slice(0, 2).map((a) => a.label.split('(')[1]?.replace(')', '') || a.label.slice(0, 10)).join(', ')}
                  {associatedActors.length > 2 && '...'}
                </span>
                <button
                  onClick={() => handleDelete(segment.id, segment.label)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  title="Eliminar sector"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-sm">Nuevo Segmento (POST /actor_segments/new)</h3>
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
                  Nombre del Sector / Segmento (label) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="ej: Sector Hábitat, Ambiente y Catastro"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Descripción del Segmento</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Alcance institucional y tipos de entidades agrupadas..."
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
                  {isSubmitting ? 'Guardando...' : 'Crear Segmento'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
