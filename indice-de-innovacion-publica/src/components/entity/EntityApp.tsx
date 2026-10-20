import React, { useState } from 'react';
import { Header } from '../layout/Header';
import { ApiSettingsModal } from '../common/ApiSettingsModal';
import { EntityDashboard } from './EntityDashboard';
import { FormDiagnosticView } from './FormDiagnosticView';
import { SubmissionsHistoryView } from './SubmissionsHistoryView';
import { EntityProfileView } from './EntityProfileView';
import { BarChart3, FileSignature, Clock, User } from 'lucide-react';

export const EntityApp: React.FC = () => {
  const [entityTab, setEntityTab] = useState<'diagnostic' | 'dashboard' | 'history' | 'profile'>(
    'diagnostic'
  );

  // Modals state
  const [showApiSettings, setShowApiSettings] = useState(false);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col text-slate-900 font-sans antialiased">
      {/* Global Application Header (LabCapital / Veeduría Distrital Theme) */}
      <Header
        onOpenSettings={() => setShowApiSettings(true)}
      />

      {/* Sub-navigation bar depending on active profile */}
      <div className="bg-white border-b border-slate-200 sticky top-16 sm:top-18 z-20 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between overflow-x-auto py-2 gap-4">
            {/* Entity Navigation Tabs: Solucionar Formulario Asignado, Historial, Ficha */}
              <div className="flex items-center gap-1.5 min-w-max">
                <button
                  onClick={() => setEntityTab('diagnostic')}
                  className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    entityTab === 'diagnostic'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <FileSignature className="w-4 h-4 text-amber-500" />
                  <span>Solucionar Formulario Asignado</span>
                </button>

                <button
                  onClick={() => setEntityTab('dashboard')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    entityTab === 'dashboard'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>Panel de Estado</span>
                </button>

                <button
                  onClick={() => setEntityTab('history')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    entityTab === 'history'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Clock className="w-4 h-4" />
                  <span>Historial de Radicaciones</span>
                </button>

                <button
                  onClick={() => setEntityTab('profile')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    entityTab === 'profile'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <User className="w-4 h-4" />
                  <span>Ficha de la Entidad</span>
                </button>
              </div>
          </div>
        </div>
      </div>

      {/* Main Body Content */}
      <main className="flex-1 pb-16">
        {entityTab === 'diagnostic' && (
              <FormDiagnosticView onBackToDashboard={() => setEntityTab('dashboard')} />
            )}
            {entityTab === 'dashboard' && (
              <EntityDashboard
                onStartDiagnostic={() => setEntityTab('diagnostic')}
                onViewHistory={() => setEntityTab('history')}
                onViewProfile={() => setEntityTab('profile')}
              />
            )}
            {entityTab === 'history' && (
              <SubmissionsHistoryView
                onBack={() => setEntityTab('dashboard')}
                onContinueEditing={() => setEntityTab('diagnostic')}
              />
            )}
            {entityTab === 'profile' && (
              <EntityProfileView onBack={() => setEntityTab('dashboard')} />
            )}
      </main>

      {/* Institutional Footer (LabCapital / Veeduría Distrital Theme) */}
      <footer className="bg-slate-950 text-white text-xs py-6 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-3">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-3">
              <div className="bg-white/95 rounded-lg px-2 py-1 shadow-xs border border-white/20">
                <img
                  src="https://labcapital.veeduriadistrital.gov.co:4282/wp-content/uploads/2026/06/Captura-de-pantalla-2026-06-10-133932.png"
                  alt="LabCapital"
                  className="h-6 w-auto max-w-[140px] object-contain"
                  referrerPolicy="no-referrer"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
              <div>
                <span className="font-bold text-slate-100 text-xs block">
                  Índice de Innovación Pública
                </span>
                <span className="text-amber-400 text-[11px]">
                  Veeduría Distrital • LabCapital • Alcaldía Mayor de Bogotá D.C.
                </span>
              </div>
            </div>

            <div className="text-slate-400 text-[11px] text-center md:text-right">
              Sistema Distrital de Medición de Capacidades de Innovación Pública
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between text-slate-500 text-[10px] gap-2">
            <div>
              Alcaldía Mayor de Bogotá D.C. — Laboratorio de Innovación Pública (LabCapital)
            </div>
            <div>Todos los derechos reservados</div>
          </div>
        </div>
      </footer>

      {/* Global Settings Modal */}
      <ApiSettingsModal
        isOpen={showApiSettings}
        onClose={() => setShowApiSettings(false)}
      />
    </div>
  );
};

