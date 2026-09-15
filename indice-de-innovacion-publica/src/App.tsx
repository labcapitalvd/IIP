/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider, useApp } from './context/AppContext';
import { FormSubmissionProvider } from './context/FormSubmissionContext';
import { Header } from './components/layout/Header';
import { ApiSettingsModal } from './components/common/ApiSettingsModal';

// Entity Views
import { EntityDashboard } from './components/entity/EntityDashboard';
import { FormDiagnosticView } from './components/entity/FormDiagnosticView';
import { SubmissionsHistoryView } from './components/entity/SubmissionsHistoryView';
import { EntityProfileView } from './components/entity/EntityProfileView';

// Admin Views
import { FormsManager } from './components/admin/FormsManager';
import { EntityUsersManager } from './components/admin/EntityUsersManager';
import { FormAssignmentsManager } from './components/admin/FormAssignmentsManager';
import { SubmissionsMonitor } from './components/admin/SubmissionsMonitor';
import { ActorsManager } from './components/admin/ActorsManager';
import { LoginView } from './components/auth/LoginView';

import {
  Building2,
  FileCheck2,
  FileText,
  BarChart3,
  Users,
  FileSignature,
  RotateCcw,
  Sparkles,
  Clock,
  User,
} from 'lucide-react';

const MainContent: React.FC = () => {
  const { role, user } = useAuth();
  const { config, forms, setActiveFormById } = useApp();

  // Navigation states
  const [adminTab, setAdminTab] = useState<
    'forms' | 'users' | 'assignments' | 'submissions' | 'actors'
  >('forms');

  const [entityTab, setEntityTab] = useState<'diagnostic' | 'dashboard' | 'history' | 'profile'>(
    'diagnostic'
  );

  // Modals state
  const [showApiSettings, setShowApiSettings] = useState(false);

  if (!user) {
    return <LoginView />;
  }

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
            {role === 'admin' ? (
              /* Admin Navigation Tabs: Creador de Formularios, Usuarios, Asignaciones, Monitor, Entidades */
              <div className="flex items-center gap-1.5 min-w-max">
                <button
                  onClick={() => setAdminTab('forms')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    adminTab === 'forms'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <FileText className="w-4 h-4 text-amber-500" />
                  <span>1. Crear / Diseñar Formularios</span>
                </button>

                <button
                  onClick={() => setAdminTab('users')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    adminTab === 'users'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Users className="w-4 h-4 text-amber-500" />
                  <span>2. Usuarios de Entidades</span>
                </button>

                <button
                  onClick={() => setAdminTab('assignments')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    adminTab === 'assignments'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <FileCheck2 className="w-4 h-4 text-amber-500" />
                  <span>3. Asignar Formularios</span>
                </button>

                <button
                  onClick={() => setAdminTab('submissions')}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                    adminTab === 'submissions'
                      ? 'bg-slate-900 text-amber-400 shadow-xs border border-slate-800'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 text-amber-500" />
                  <span>4. Monitor de Radicados</span>
                </button>

                <button
                  onClick={() => setAdminTab('actors')}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    adminTab === 'actors'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                  }`}
                >
                  <Building2 className="w-3.5 h-3.5" />
                  <span>Entidades & Sectores</span>
                </button>
              </div>
            ) : (
              /* Entity Navigation Tabs: Solucionar Formulario Asignado, Historial, Ficha */
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
            )}

            {/* Quick Data Mode Pill */}
            <div className="hidden sm:flex items-center gap-2 text-xs shrink-0">
              <span className="text-slate-400 text-[11px]">Modo:</span>
              <button
                onClick={() => setShowApiSettings(true)}
                className={`px-2.5 py-0.5 rounded-full font-semibold text-[11px] border transition-colors ${
                  config.useRealBackend
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                    : 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
                }`}
              >
                {config.useRealBackend ? '● FastAPI Real (4293/4294)' : '○ Simulador Front-End'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Body Content */}
      <main className="flex-1 pb-16">
        {role === 'admin' ? (
          <>
            {adminTab === 'forms' && (
              <FormsManager
                onGoToAssign={(formId) => {
                  setActiveFormById(formId);
                  setAdminTab('assignments');
                }}
              />
            )}
            {adminTab === 'users' && (
              <EntityUsersManager
                onAssignFormToUser={(userId, actorId) => {
                  setAdminTab('assignments');
                }}
              />
            )}
            {adminTab === 'assignments' && <FormAssignmentsManager />}
            {adminTab === 'submissions' && <SubmissionsMonitor />}
            {adminTab === 'actors' && (
              <ActorsManager onImpersonateEntity={() => setEntityTab('diagnostic')} />
            )}
          </>
        ) : (
          <>
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
          </>
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

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <FormSubmissionProvider>
          <MainContent />
        </FormSubmissionProvider>
      </AppProvider>
    </AuthProvider>
  );
}
