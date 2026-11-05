import React, { useEffect, useState } from 'react';
import { Building2, ClipboardList, FileText, Lightbulb, LogOut, TrendingUp, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { coreService } from '../../services/coreService';
import { EntityAssignment } from '../../types';
import { ROUTES, navigate } from '../../utils/router';
import { EntityDashboard } from './EntityDashboard';
import { EntityProfileView } from './EntityProfileView';
import { FormDiagnosticView } from './FormDiagnosticView';
import { SubmissionsHistoryView } from './SubmissionsHistoryView';
import { EntityFormsView, EntityProgressView } from './EntityFormsView';
import { EntityAccountView, EntityAssignedActorView } from './EntityInfoViews';

type EntityTab = keyof typeof ROUTES.entity;

export const entityTabFromPath = (pathname: string): EntityTab | null =>
  (Object.keys(ROUTES.entity) as EntityTab[]).find((k) => ROUTES.entity[k] === pathname) ?? null;

const MENU: { tab: EntityTab; label: string; icon: React.ElementType }[] = [
  { tab: 'forms', label: 'Formularios', icon: FileText },
  { tab: 'progress', label: 'Barra de proceso', icon: TrendingUp },
  { tab: 'account', label: 'Perfil', icon: User },
  { tab: 'assignedEntity', label: 'Entidad asignada', icon: Building2 },
];

export const EntityApp: React.FC<{ pathname: string }> = ({ pathname }) => {
  const { user, logout, isLoading } = useAuth();
  const tab = entityTabFromPath(pathname) ?? 'forms';
  const go = (t: EntityTab) => navigate(ROUTES.entity[t]);

  // Formularios asignados a este usuario: viven en el backend (GET /public/forms/assignments/me).
  const [assignments, setAssignments] = useState<EntityAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    coreService
      .getMyAssignments()
      .then((list) => alive && setAssignments(list))
      .catch((e) => alive && setError(e?.message || 'No se pudieron cargar los formularios asignados.'))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [user?.id]);

  const state = { assignments, loading, error };

  return (
    <div className="min-h-screen w-full relative font-sans text-gray-900">
      <div className="fixed inset-0 z-0">
        <img src="/login-entidad-bg.jpg" alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-white/40 backdrop-blur-sm" />
      </div>

      <div className="relative z-10 min-h-screen max-w-7xl mx-auto p-4 sm:p-6 flex flex-col lg:flex-row gap-4 sm:gap-6">
        {/* Menú */}
        <aside className="lg:w-72 shrink-0 bg-white rounded-3xl shadow-2xl border border-gray-100 p-5 flex flex-col lg:sticky lg:top-6 lg:self-start lg:h-[calc(100vh-3rem)]">
          <div className="flex items-center gap-3 pb-5 border-b border-gray-100">
            <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
              <Lightbulb className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-800 leading-tight">LabCapital</h1>
              <p className="text-xs text-gray-500">Innovación Pública</p>
            </div>
          </div>

          <div className="py-4 border-b border-gray-100">
            <p className="text-sm font-semibold text-gray-800 truncate">{user?.contact_person || user?.username}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            {user?.actor_label && (
              <p className="mt-1 text-xs font-medium text-blue-600 truncate capitalize">{user.actor_label}</p>
            )}
          </div>

          <nav className="py-4 flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-visible">
            {MENU.map(({ tab: t, label, icon: Icon }) => {
              const active = tab === t || (t === 'forms' && ['diagnostic', 'dashboard', 'history', 'profile'].includes(tab));
              return (
                <button
                  key={t}
                  type="button"
                  onClick={() => go(t)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    active
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-200'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-blue-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              );
            })}
          </nav>

          <button
            type="button"
            onClick={() => logout()}
            disabled={isLoading}
            className="mt-auto flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-rose-600 hover:bg-rose-50 transition-all cursor-pointer disabled:opacity-50"
          >
            <LogOut className="w-4 h-4" />
            Salir
          </button>
        </aside>

        {/* Contenido */}
        <main className="flex-1 min-w-0 bg-white rounded-3xl shadow-2xl border border-gray-100 p-6 sm:p-8">
          {tab === 'forms' && <EntityFormsView {...state} onFill={() => go('diagnostic')} />}
          {tab === 'progress' && <EntityProgressView {...state} />}
          {tab === 'account' && <EntityAccountView />}
          {tab === 'assignedEntity' && <EntityAssignedActorView />}

          {/* Pantallas de diligenciamiento existentes (se abren desde "Diligenciar"). */}
          {tab === 'diagnostic' && (
            <div className="-m-6 sm:-m-8 rounded-3xl overflow-hidden bg-slate-100">
              <div className="px-6 pt-4">
                <button
                  type="button"
                  onClick={() => go('forms')}
                  className="flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 cursor-pointer"
                >
                  <ClipboardList className="w-4 h-4" /> Volver a mis formularios
                </button>
              </div>
              <FormDiagnosticView onBackToDashboard={() => go('forms')} />
            </div>
          )}
          {tab === 'dashboard' && (
            <EntityDashboard
              onStartDiagnostic={() => go('diagnostic')}
              onViewHistory={() => go('history')}
              onViewProfile={() => go('profile')}
            />
          )}
          {tab === 'history' && (
            <SubmissionsHistoryView onBack={() => go('forms')} onContinueEditing={() => go('diagnostic')} />
          )}
          {tab === 'profile' && <EntityProfileView onBack={() => go('forms')} />}
        </main>
      </div>
    </div>
  );
};
