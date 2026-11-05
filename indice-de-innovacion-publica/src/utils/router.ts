import { useCallback, useEffect, useState } from 'react';

/**
 * Router mínimo basado en la History API (sin dependencias).
 * La app se sirve con fallback a index.html (nginx `try_files`, Vite en dev), así que
 * cualquier URL como /admin/formularios abre la SPA y ésta decide qué pantalla mostrar.
 */

const NAV_EVENT = 'iip:navigate';

export interface Location {
  pathname: string;
  search: string;
}

const read = (): Location => ({ pathname: window.location.pathname.replace(/\/+$/, '') || '/', search: window.location.search });

export function navigate(to: string, opts: { replace?: boolean } = {}) {
  if (to === window.location.pathname + window.location.search) return;
  if (opts.replace) window.history.replaceState(null, '', to);
  else window.history.pushState(null, '', to);
  window.dispatchEvent(new Event(NAV_EVENT));
}

export function useLocation(): Location & { navigate: typeof navigate } {
  const [loc, setLoc] = useState<Location>(read);
  const sync = useCallback(() => setLoc(read()), []);

  useEffect(() => {
    window.addEventListener('popstate', sync);
    window.addEventListener(NAV_EVENT, sync);
    return () => {
      window.removeEventListener('popstate', sync);
      window.removeEventListener(NAV_EVENT, sync);
    };
  }, [sync]);

  return { ...loc, navigate };
}

/** Rutas de la aplicación. */
export const ROUTES = {
  login: '/login',
  loginEntity: '/login/entidad',
  admin: {
    forms: '/admin/formularios',
    users: '/admin/usuarios-entidades',
    assignments: '/admin/asignaciones',
    submissions: '/admin/monitor-radicados',
    actors: '/admin/entidades',
    parameters: '/admin/parametros',
  },
  entity: {
    forms: '/entidad/formularios',
    progress: '/entidad/proceso',
    account: '/entidad/perfil',
    assignedEntity: '/entidad/mi-entidad',
    diagnostic: '/entidad/diagnostico',
    dashboard: '/entidad/panel',
    history: '/entidad/historial',
    profile: '/entidad/ficha',
  },
} as const;

export const homeFor = (role: 'admin' | 'entity') =>
  role === 'admin' ? ROUTES.admin.forms : ROUTES.entity.forms;
