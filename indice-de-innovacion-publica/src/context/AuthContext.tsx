import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthUser, LoginResponse, RegisterPayload, UserRole } from '../types';
import { authService, mapMeToAuthUser } from '../services/authService';
import { apiClient } from '../services/apiClient';
import { DEMO_USERS } from '../data/mockData';
import { isJwtExpired } from '../utils/jwt';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  role: UserRole | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  reauth: () => Promise<void>;
  logout: () => Promise<void>;
  switchRole: (role: UserRole) => void;
  switchEntity: (actorId: string, actorLabel: string) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    // Real-backend mode never seeds a user from local storage — the backend
    // (auth.py) is the only source of truth for who is logged in. The mount
    // effect below re-derives it from GET /auth/me using whatever JWT is
    // still in sessionStorage, if any.
    if (apiClient.getConfig().useRealBackend) return null;

    const saved = sessionStorage.getItem('iip_current_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // fall through to the default below
      }
    }
    return DEMO_USERS[0]; // Mock mode: seamless demo preview.
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock mode only: persist the (fake) user across reloads. Real mode never
  // writes a profile to storage — see the mount effect below.
  useEffect(() => {
    if (apiClient.getConfig().useRealBackend) return;

    if (user) {
      sessionStorage.setItem('iip_current_user', JSON.stringify(user));
    } else {
      sessionStorage.removeItem('iip_current_user');
    }
  }, [user]);

  // On mount, against the real backend, "restoring a session" means asking
  // the backend who we are — never trusting a locally cached profile. If the
  // stored access token expired while the tab was closed, try one silent
  // refresh first; if that also fails (or there's no token at all), the user
  // simply stays logged out.
  useEffect(() => {
    if (!apiClient.getConfig().useRealBackend) return;

    const restoreSession = async () => {
      const { accessToken, refreshToken } = apiClient.getTokens();
      if (!accessToken && !refreshToken) return;

      try {
        if (!accessToken || isJwtExpired(accessToken)) {
          if (!refreshToken) throw new Error('no refresh token');
          await authService.reauth();
        }
        const me = await authService.getMe();
        setUser(mapMeToAuthUser(me));
      } catch {
        setUser(null);
        apiClient.clearTokens();
      }
    };

    restoreSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const clearError = () => setError(null);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const cleanUser = username.trim();
      const cleanPass = password.trim();

      if (apiClient.getConfig().useRealBackend) {
        // Real mode: the backend is the only source of truth. No local
        // shortcuts — this must go through POST /public/auth/login and get
        // back a real Ed25519 JWT, or fail with whatever the API says.
        const { user: loggedUser } = await authService.login(cleanUser, cleanPass);
        setUser(loggedUser);
        return;
      }

      // Mock mode below: local users database (DEMO_USERS + anyone who
      // "registered" in this browser), no network calls at all.
      const localUsers: AuthUser[] = JSON.parse(localStorage.getItem('iip_all_users') || '[]');
      const allKnownUsers = [...localUsers, ...DEMO_USERS];

      const matchedUser = allKnownUsers.find(
        (u) =>
          u.username.toLowerCase() === cleanUser.toLowerCase() ||
          u.email.toLowerCase() === cleanUser.toLowerCase()
      );

      if (matchedUser) {
        if (matchedUser.is_active === false || matchedUser.approval_status === 'pending') {
          throw new Error(
            `Acceso denegado: Su cuenta se encuentra PENDIENTE DE APROBACIÓN por parte de "${matchedUser.actor_label || 'la entidad seleccionada'}". No podrá ingresar hasta que el administrador o delegado de su entidad le otorgue el permiso de acceso.`
          );
        }

        if (
          matchedUser.password &&
          matchedUser.password !== cleanPass &&
          cleanPass !== 'admin1234' &&
          cleanPass !== '12345678' &&
          cleanPass !== 'Bogota2026*'
        ) {
          throw new Error('Contraseña incorrecta. Por favor verifique sus datos.');
        }

        setUser(matchedUser);
        return;
      }

      throw new Error('Usuario no encontrado en el modo local (mock). Verifique sus datos.');
    } catch (err: any) {
      const message = err?.message || 'Error al iniciar sesión. Verifique sus credenciales.';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      if (apiClient.getConfig().useRealBackend) {
        // Real mode: POST /public/auth/register. The backend activates the
        // account immediately (is_active=True, no email verification, no
        // approval workflow) — there is nothing else to do locally.
        await authService.register(payload);
        return;
      }

      // Mock mode below: keep the local "pending approval" simulation.
      const localUsers: AuthUser[] = JSON.parse(localStorage.getItem('iip_all_users') || '[]');
      const allKnownUsers = [...localUsers, ...DEMO_USERS];

      const existing = allKnownUsers.find(
        (u) =>
          u.username.toLowerCase() === payload.username.toLowerCase().trim() ||
          u.email.toLowerCase() === payload.email.toLowerCase().trim()
      );

      if (existing) {
        throw new Error(
          `El usuario "${payload.username}" o correo "${payload.email}" ya se encuentra registrado.`
        );
      }

      const newUser: AuthUser = {
        id: `usr-reg-${Date.now()}`,
        username: payload.username.trim(),
        email: payload.email.trim(),
        password: payload.password,
        role: 'entity',
        actor_id: payload.actor_id || 'act-001',
        actor_label: payload.actor_label || 'Entidad Distrital',
        contact_person: payload.contact_person,
        phone: payload.phone,
        is_active: false, // Inactive pending entity approval! (mock-only concept)
        approval_status: 'pending',
        created_at: new Date().toISOString(),
      };

      const updatedUsers = [newUser, ...localUsers];
      localStorage.setItem('iip_all_users', JSON.stringify(updatedUsers));
    } catch (err: any) {
      const message = err?.message || 'Error al registrar usuario.';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const reauth = async () => {
    try {
      await authService.reauth();
    } catch (err: any) {
      // If reauth fails and returns token error, clear session
      if (err.isTokenError || err.status === 401 || err.status === 500) {
        setUser(null);
        apiClient.clearTokens();
      }
      throw err;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  };

  const switchRole = useCallback((newRole: UserRole) => {
    if (newRole === 'admin') {
      const adminUser = DEMO_USERS.find((u) => u.role === 'admin') || DEMO_USERS[0];
      setUser(adminUser);
    } else {
      const entityUser = DEMO_USERS.find((u) => u.role === 'entity') || DEMO_USERS[1];
      setUser(entityUser);
    }
  }, []);

  const switchEntity = useCallback((actorId: string, actorLabel: string) => {
    setUser((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        actor_id: actorId,
        actor_label: actorLabel,
      };
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        role: user ? user.role : null,
        isLoading,
        error,
        login,
        register,
        reauth,
        logout,
        switchRole,
        switchEntity,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
