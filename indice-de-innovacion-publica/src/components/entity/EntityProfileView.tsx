import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import {
  Building2,
  Mail,
  Phone,
  User,
  Shield,
  Layers,
  Save,
  CheckCircle2,
  ArrowLeft,
} from 'lucide-react';

interface EntityProfileViewProps {
  onBack: () => void;
}

export const EntityProfileView: React.FC<EntityProfileViewProps> = ({ onBack }) => {
  const { user } = useAuth();
  const { actors, segments } = useApp();

  const currentActor = actors.find((a) => a.id === user?.actor_id) || actors[0];

  const [label, setLabel] = useState(currentActor.label);
  const [description, setDescription] = useState(currentActor.description || '');
  const [mission, setMission] = useState(currentActor.mission || '');
  const [vision, setVision] = useState(currentActor.vision || '');
  const [contactEmail, setContactEmail] = useState(currentActor.contact_email || '');
  const [contactPhone, setContactPhone] = useState(currentActor.contact_phone || '');
  const [headOfEntity, setHeadOfEntity] = useState(currentActor.head_of_entity || '');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const activeSegment = segments.find((s) => s.id === currentActor.actor_segment_id);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1.5"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al Panel</span>
        </button>
        <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">
          Ficha Institucional • Actor Distrital
        </span>
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 sm:p-8 flex items-start gap-4">
          <div className="p-3 bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 rounded-2xl shrink-0">
            <Building2 className="w-8 h-8" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider">
              {activeSegment?.label || 'Sector Distrital'}
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-white mt-1">{currentActor.label}</h2>
            <p className="text-xs text-slate-300 mt-1">ID Único de Actor: <code className="font-mono text-indigo-200">{currentActor.id}</code></p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="p-6 sm:p-8 space-y-6 text-sm">
          {savedSuccess && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Información institucional actualizada correctamente.</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">Nombre Oficial de la Entidad (label)</label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Representante Legal / Directivo</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={headOfEntity}
                  onChange={(e) => setHeadOfEntity(e.target.value)}
                  placeholder="ej: Dr. Fernando Moreno"
                  className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Segmento / Sector Asignado</label>
              <div className="relative">
                <Layers className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  disabled
                  value={activeSegment?.label || 'Nivel Central'}
                  className="w-full pl-9 pr-3.5 py-2 border border-slate-200 bg-slate-50 text-slate-500 rounded-xl text-sm outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Correo Electrónico Institucional</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  placeholder="contacto@entidad.gov.co"
                  className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Teléfono de Contacto</label>
              <div className="relative">
                <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  placeholder="+57 (601) 3358000"
                  className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">Descripción General (description)</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">Misión Institucional (mission)</label>
              <textarea
                rows={3}
                value={mission}
                onChange={(e) => setMission(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">Visión Institucional (vision)</label>
              <textarea
                rows={3}
                value={vision}
                onChange={(e) => setVision(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              <span>Guardar Ficha de la Entidad</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
