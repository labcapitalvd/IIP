import React from 'react';
import { useApp } from '../../context/AppContext';
import {
  Building2,
  Layers,
  FileCheck2,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Plus,
  BarChart3,
  Server,
  FileSpreadsheet,
  CheckCircle2,
  Users,
} from 'lucide-react';

interface AdminDashboardProps {
  onNavigate: (tab: 'actors' | 'segments' | 'forms' | 'submissions') => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate }) => {
  const { actors, segments, submissions, activeForm } = useApp();

  const totalActors = actors.length;
  const totalSubmissions = submissions.length;
  const participationRate = totalActors > 0 ? Math.round((totalSubmissions / totalActors) * 100) : 0;
  const avgScore =
    submissions.length > 0
      ? (
          submissions.reduce((acc, curr) => acc + (curr.score || 0), 0) / submissions.length
        ).toFixed(1)
      : '0.0';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 uppercase">
                Panel de Administración Distrital
              </span>
              <span className="text-xs text-slate-400">Veeduría Distrital</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Gestión Integral del Índice de Innovación Pública (IIP)
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              Consola centralizada para la administración de entidades distritales (actores), sectores,
              estructura de formularios y monitoreo de evidencias de innovación.
            </p>
          </div>

          <div className="flex flex-wrap gap-2.5 shrink-0">
            <button
              onClick={() => onNavigate('submissions')}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-950/50 transition-all flex items-center gap-2"
            >
              <FileCheck2 className="w-4 h-4" />
              <span>Ver Envíos Recibidos</span>
            </button>
            <button
              onClick={() => onNavigate('actors')}
              className="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-semibold text-xs rounded-xl backdrop-blur-xs transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              <span>Gestionar Actores</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Actors */}
        <div
          onClick={() => onNavigate('actors')}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Entidades (Actores)
            </span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
              <Building2 className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{totalActors}</div>
          <p className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>{segments.length} Sectores clasificados</span>
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
          </p>
        </div>

        {/* Submissions Received */}
        <div
          onClick={() => onNavigate('submissions')}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Diagnósticos Recibidos
            </span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
              <FileCheck2 className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">{totalSubmissions}</div>
          <p className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>Tasa de respuesta: {participationRate}%</span>
            <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
          </p>
        </div>

        {/* Average IIP Score */}
        <div
          onClick={() => onNavigate('submissions')}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Promedio IIP Distrital
            </span>
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="text-2xl font-black text-slate-900">
            {avgScore} <span className="text-xs font-normal text-slate-400">/ 100</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Nivel: Innovación Avanzada</p>
        </div>

        {/* Active Form Instrument */}
        <div
          onClick={() => onNavigate('forms')}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Estructura de Cuestionario
            </span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition-colors">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="text-base font-bold text-slate-900 truncate">{activeForm.code}</div>
          <p className="text-xs text-slate-500 mt-1 flex items-center justify-between">
            <span>{activeForm.sections.length} Dimensiones</span>
            <span className="text-indigo-600 font-semibold text-[11px]">POST /forms</span>
          </p>
        </div>
      </div>

      {/* Administration Modules Grid */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-slate-400">
          Módulos de Gestión
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Module 1: Actores */}
          <div
            onClick={() => onNavigate('actors')}
            className="bg-white p-6 rounded-3xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <Building2 className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-900 text-base group-hover:text-indigo-900">
                Gestión de Actores (Entidades)
              </h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Administre el directorio de secretarías, organismos adscritos y entidades del Distrito.
                Conectado con los endpoints <code className="font-mono text-indigo-600">GET /actors/all</code> y <code className="font-mono text-indigo-600">POST /actors/new</code>.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
              <span>{actors.length} entidades registradas</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 2: Segmentos */}
          <div
            onClick={() => onNavigate('segments')}
            className="bg-white p-6 rounded-3xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <Layers className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-900 text-base group-hover:text-indigo-900">
                Segmentos de Actor (Sectores)
              </h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Clasificación por sectores administrativos distritales (Nivel Central, Movilidad, Hacienda,
                Educación). Conectado con <code className="font-mono text-indigo-600">/actor_segments/*</code>.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
              <span>{segments.length} sectores activos</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 3: Submissions */}
          <div
            onClick={() => onNavigate('submissions')}
            className="bg-white p-6 rounded-3xl border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-900 text-base group-hover:text-indigo-900">
                Monitor de Envíos y Diagnósticos
              </h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Inspeccione las respuestas recibidas de cada entidad, las fichas de proyectos registradas
                (card_entry) y exporte consolidados en JSON y formato de reporte.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600">
              <span>{submissions.length} respuestas recibidas</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
