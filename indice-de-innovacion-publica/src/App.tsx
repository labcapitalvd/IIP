/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import { FormSubmissionProvider } from './context/FormSubmissionContext';
import { LoginView } from './components/auth/LoginView';
import { AdminApp, adminTabFromPath } from './components/admin/AdminApp';
import { EntityApp, entityTabFromPath } from './components/entity/EntityApp';
import { ROUTES, homeFor, navigate, useLocation } from './utils/router';

const FullScreenLoader: React.FC<{ text: string }> = ({ text }) => (
  <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center gap-3 text-slate-300">
    <Loader2 className="w-10 h-10 text-amber-400 animate-spin" />
    <p className="text-sm font-semibold">{text}</p>
  </div>
);

/**
 * Rutas:
 *   /login                      → inicio de sesión
 *   /admin/formularios | usuarios-entidades | asignaciones | monitor-radicados | entidades
 *   /entidad/diagnostico | panel | historial | ficha
 * Sin sesión, cualquier ruta protegida redirige a /login?next=<ruta> y vuelve a ella al entrar.
 */
const MainContent: React.FC = () => {
  const { user, role, isInitializing } = useAuth();
  const { pathname, search } = useLocation();

  const isAdminPath = pathname.startsWith('/admin');
  const isEntityPath = pathname.startsWith('/entidad');
  const validTab = isAdminPath ? !!adminTabFromPath(pathname) : isEntityPath ? !!entityTabFromPath(pathname) : false;

  useEffect(() => {
    if (isInitializing) return; // aún se verifica la sesión: no decidir nada todavía

    if (!user) {
      if (pathname !== ROUTES.login) {
        const next = pathname !== '/' ? `?next=${encodeURIComponent(pathname + search)}` : '';
        navigate(`${ROUTES.login}${next}`, { replace: true });
      }
      return;
    }

    // Con sesión: /login, / o rutas desconocidas llevan al inicio del rol; cada rol solo ve lo suyo.
    if (pathname === ROUTES.login) {
      const next = new URLSearchParams(search).get('next');
      const allowed = next && next.startsWith(role === 'admin' ? '/admin' : '/entidad');
      navigate(allowed ? next! : homeFor(role!), { replace: true });
    } else if (
      (role === 'admin' && !isAdminPath) ||
      (role === 'entity' && !isEntityPath) ||
      !validTab
    ) {
      navigate(homeFor(role!), { replace: true });
    }
  }, [isInitializing, user, role, pathname, search, isAdminPath, isEntityPath, validTab]);

  // Mientras se verifica la sesión guardada nunca se muestra el login.
  if (isInitializing) return <FullScreenLoader text="Verificando sesión…" />;

  if (!user) return pathname === ROUTES.login ? <LoginView /> : <FullScreenLoader text="Redirigiendo…" />;

  if (role === 'admin' && isAdminPath && validTab) return <AdminApp pathname={pathname} />;
  if (role === 'entity' && isEntityPath && validTab) return <EntityApp pathname={pathname} />;

  return <FullScreenLoader text="Cargando…" />;
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
