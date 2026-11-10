import React, { useCallback, useEffect, useState } from 'react';
import { Building2, FileText, Loader2, TrendingUp, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { coreService } from '../../services/coreService';
import { EntityAssignment } from '../../types';
import { ROUTES, navigate, useLocation } from '../../utils/router';
import { EntityDashboard } from './EntityDashboard';
import { EntityProfileView } from './EntityProfileView';
import { GuidedDiagnostic } from './wizard/GuidedDiagnostic';
import { WizardHeader } from './wizard/WizardHeader';
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
  const { user } = useAuth();
  const tab = entityTabFromPath(pathname) ?? 'forms';
  const go = (t: EntityTab) => navigate(ROUTES.entity[t]);
  const { search } = useLocation();

  // Formularios asignados a este usuario: viven en el backend (GET /public/forms/assignments/me).
  const [assignments, setAssignments] = useState<EntityAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    (silent = false) => {
      if (!silent) setLoading(true);
      return coreService
        .getMyAssignments()
        .then((list) => {
          setAssignments(list);
          setError(null);
        })
        .catch((e) => setError(e?.message || 'No se pudieron cargar los formularios asignados.'))
        .finally(() => setLoading(false));
    },
    []
  );

  useEffect(() => {
    load();
  }, [user?.id, load]);

  const openAssignment = (a: EntityAssignment) => navigate(`${ROUTES.entity.diagnostic}?asignacion=${a.id}`);

  const state = { assignments, loading, error };

  // Asistente de diligenciamiento: pantalla completa, sin el menú lateral del portal.
  if (tab === 'diagnostic') {
    const wanted = new URLSearchParams(search).get('asignacion');
    const assignment =
      assignments.find((a) => a.id === wanted) ??
      (wanted ? undefined : assignments.find((a) => a.status !== 'submitted') ?? assignments[0]);

    if (loading)
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-iip-bg text-iip-ink">
          <Loader2 className="h-10 w-10 animate-spin text-iip-navy" />
          <p className="font-semibold">Cargando su formulario…</p>
        </div>
      );
    if (!assignment)
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-iip-bg p-6 text-center text-iip-ink">
          <p className="font-semibold">{error || 'No se encontró el formulario asignado.'}</p>
          <button type="button" onClick={() => go('forms')} className="rounded-xl bg-iip-yellow px-5 py-2.5 font-bold">Volver a mis formularios</button>
        </div>
      );
    return (
      <GuidedDiagnostic
        key={assignment.id}
        assignment={assignment}
        onExit={() => go('forms')}
        onSelectionSaved={(id, ids) => setAssignments((list) => list.map((a) => (a.id === id ? { ...a, selected_component_ids: ids } : a)))}
        onProgressChanged={() => load(true)}
      />
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-iip-bg font-sans text-iip-ink">
      <WizardHeader onExit={() => go('forms')} />

      <nav aria-label="Secciones del portal" className="border-b border-iip-line bg-white">
        <ul className="mx-auto flex max-w-[1500px] gap-1 overflow-x-auto px-4 sm:px-6">
          {MENU.map(({ tab: t, label, icon: Icon }) => {
            const active = tab === t || (t === 'forms' && ['dashboard', 'history', 'profile'].includes(tab));
            return (
              <li key={t}>
                <button
                  type="button"
                  onClick={() => go(t)}
                  aria-current={active ? 'page' : undefined}
                  className={`iip-focus flex items-center gap-2 whitespace-nowrap border-b-4 px-4 py-3.5 text-[15px] font-bold transition-colors ${
                    active ? 'border-iip-yellow text-iip-ink' : 'border-transparent text-iip-muted hover:text-iip-ink'
                  }`}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:px-6">
        <div className="rounded-3xl border border-iip-line bg-white p-5 shadow-sm sm:p-8">
          {tab === 'forms' && <EntityFormsView {...state} onFill={openAssignment} />}
          {tab === 'progress' && <EntityProgressView {...state} />}
          {tab === 'account' && <EntityAccountView />}
          {tab === 'assignedEntity' && <EntityAssignedActorView />}

          {/* Otras pantallas de la entidad. */}
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
        </div>
      </main>
    </div>
  );
};
