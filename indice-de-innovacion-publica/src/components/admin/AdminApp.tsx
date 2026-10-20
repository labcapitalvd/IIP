import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { FormsManager } from './FormsManager';
import { EntityUsersManager } from './EntityUsersManager';
import { FormAssignmentsManager } from './FormAssignmentsManager';
import { SubmissionsMonitor } from './SubmissionsMonitor';
import { ActorsManager } from './ActorsManager';
import {
  Building2,
  FileCheck2,
  FileText,
  BarChart3,
  Users,
  LogOut,
  ShieldCheck,
} from 'lucide-react';

type AdminTab = 'forms' | 'users' | 'assignments' | 'submissions' | 'actors';

const NAV: { id: AdminTab; label: string; icon: React.ElementType }[] = [
  { id: 'forms', label: 'Formularios', icon: FileText },
  { id: 'users', label: 'Usuarios de entidades', icon: Users },
  { id: 'assignments', label: 'Asignaciones', icon: FileCheck2 },
  { id: 'submissions', label: 'Monitor de radicados', icon: BarChart3 },
  { id: 'actors', label: 'Entidades y sectores', icon: Building2 },
];

/**
 * Panel de administración (rol `admin`). Layout propio con barra lateral,
 * independiente del portal de entidades.
 */
export const AdminApp: React.FC = () => {
  const { user, logout } = useAuth();
  const { setActiveFormById } = useApp();
  const [tab, setTab] = useState<AdminTab>('forms');

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 font-sans antialiased flex flex-col md:flex-row">
      <aside className="md:w-64 md:min-h-screen md:sticky md:top-0 md:h-screen bg-slate-950 text-slate-300 flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2 text-amber-400 text-[10px] font-bold uppercase tracking-widest">
            <ShieldCheck className="w-4 h-4" />
            Administración
          </div>
          <h1 className="mt-1 text-white font-extrabold leading-tight">
            Índice de Innovación Pública
          </h1>
          <p className="text-[11px] text-slate-500">Veeduría Distrital • LabCapital</p>
        </div>

        <nav className="flex md:flex-col gap-1 p-3 overflow-x-auto md:overflow-visible md:flex-1">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-3 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2.5 whitespace-nowrap transition-colors text-left ${
                tab === id
                  ? 'bg-amber-500 text-slate-950'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="p-3 border-t border-slate-800 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500 text-slate-950 font-black text-sm flex items-center justify-center shrink-0">
            {user?.username?.charAt(0).toUpperCase() || 'A'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-xs font-bold text-white truncate">{user?.username}</div>
            <div className="text-[10px] text-slate-500 truncate">{user?.email}</div>
          </div>
          <button
            onClick={() => logout()}
            title="Cerrar sesión"
            className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-900"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0 pb-16">
        {tab === 'forms' && (
          <FormsManager
            onGoToAssign={(formId) => {
              setActiveFormById(formId);
              setTab('assignments');
            }}
          />
        )}
        {tab === 'users' && <EntityUsersManager onAssignFormToUser={() => setTab('assignments')} />}
        {tab === 'assignments' && <FormAssignmentsManager />}
        {tab === 'submissions' && <SubmissionsMonitor />}
        {tab === 'actors' && <ActorsManager />}
      </main>
    </div>
  );
};
