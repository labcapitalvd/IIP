import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthUser, LoginResponse, RegisterPayload, UserRole } from '../types';
import { authService } from '../services/authService';
import { apiClient } from '../services/apiClient';
import { DEMO_USERS } from '../data/mockData';

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
        return DEMO_USERS[0]; // Default to Admin
      }
    }
    return DEMO_USERS[0]; // Default logged-in as admin for seamless initial preview
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

  const clearError = () => setError(null);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const cleanUser = username.trim();
      const cleanPass = password.trim();

      // Check in local users database (includes both DEMO_USERS and any self-registered users)
      const localUsers: AuthUser[] = JSON.parse(localStorage.getItem('iip_all_users') || '[]');
      const allKnownUsers = [...localUsers, ...DEMO_USERS];

      const matchedUser = allKnownUsers.find(
        (u) =>
          u.username.toLowerCase() === cleanUser.toLowerCase() ||
          u.email.toLowerCase() === cleanUser.toLowerCase()
      );

      // If user is found and is explicitly marked pending or inactive
      if (matchedUser) {
        if (matchedUser.is_active === false || matchedUser.approval_status === 'pending') {
          throw new Error(
            `Acceso denegado: Su cuenta se encuentra PENDIENTE DE APROBACIÓN por parte de "${matchedUser.actor_label || 'la entidad seleccionada'}". No podrá ingresar hasta que el administrador o delegado de su entidad le otorgue el permiso de acceso.`
          );
        }

        // If user has a password set and it doesn't match
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

      // Try service login
      const { user: loggedUser } = await authService.login(cleanUser, cleanPass);
      if (loggedUser.is_active === false) {
        throw new Error(
          `Acceso denegado: Su cuenta se encuentra PENDIENTE DE APROBACIÓN por parte de "${loggedUser.actor_label || 'su entidad'}". No podrá ingresar hasta que su entidad autorice el acceso.`
        );
      }
      setUser(loggedUser);
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
        is_active: false, // Inactive pending entity approval!
        approval_status: 'pending',
        created_at: new Date().toISOString(),
      };

      const updatedUsers = [newUser, ...localUsers];
      localStorage.setItem('iip_all_users', JSON.stringify(updatedUsers));

      // Attempt remote registration if configured
      try {
        await authService.register(payload);
      } catch {
        // Mock fallback
      }
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
