import React, { createContext, useContext, useState, useEffect } from 'react';
import { AuthUser, LoginResponse, RegisterPayload, UserRole } from '../types';
import { authService, mapMeToAuthUser } from '../services/authService';
import { apiClient } from '../services/apiClient';
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
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // The backend (auth.py) is the only source of truth for who is logged in.
  // The mount effect below re-derives the user from GET /auth/me using
  // whatever JWT is still in sessionStorage, if any.
  const [user, setUser] = useState<AuthUser | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // On mount, "restoring a session" means asking
  // the backend who we are — never trusting a locally cached profile. If the
  // stored access token expired while the tab was closed, try one silent
  // refresh first; if that also fails (or there's no token at all), the user
  // simply stays logged out.
  useEffect(() => {
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

      // The backend is the only source of truth: POST /public/auth/login
      // (username or email) returns a real JWT, or fails with the API error.
      const { user: loggedUser } = await authService.login(cleanUser, cleanPass);
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
      // POST /public/auth/register. The backend activates the account
      // immediately (no email verification, no approval workflow).
      await authService.register(payload);
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
