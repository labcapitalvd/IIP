import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthUser, LoginResponse, RegisterPayload, UserRole } from '../types';
import { authService } from '../services/authService';
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
    const saved = sessionStorage.getItem('iip_current_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // fall through to the default below
      }
    }
    // Only auto-login as the demo admin in mock mode. Against the real
    // backend there is no session until a real JWT is issued by /auth/login.
    return apiClient.getConfig().useRealBackend ? null : DEMO_USERS[0];
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync user to session storage
  useEffect(() => {
    if (user) {
      sessionStorage.setItem('iip_current_user', JSON.stringify(user));
    } else {
      sessionStorage.removeItem('iip_current_user');
    }
  }, [user]);

  // On mount, if we restored a session against the real backend, make sure
  // the stored access token is still valid. If it expired while the tab was
  // closed, try one silent refresh before giving up and logging out — this
  // is the only way "restore session on reload" can work with JWTs.
  useEffect(() => {
    if (!apiClient.getConfig().useRealBackend || !user) return;

    const { accessToken, refreshToken } = apiClient.getTokens();

    if (accessToken && !isJwtExpired(accessToken)) return;

    if (!refreshToken) {
      setUser(null);
      apiClient.clearTokens();
      return;
    }

    authService.reauth().catch(() => {
      setUser(null);
      apiClient.clearTokens();
    });
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
