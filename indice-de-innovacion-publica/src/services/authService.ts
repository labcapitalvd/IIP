import { apiClient } from './apiClient';
import { AuthUser, LoginResponse, RegisterPayload } from '../types';
import { DEMO_USERS } from '../data/mockData';
import { decodeJwt } from '../utils/jwt';

export const authService = {
  /**
   * POST /public/auth/login
   */
  async login(username: string, password: string): Promise<{ user: AuthUser; tokens: LoginResponse }> {
    try {
      const { data } = await apiClient.request<LoginResponse>('auth', '/public/auth/login', {
        method: 'POST',
        body: { username, password },
        isAuthAction: 'login',
      });

      // Update tokens in client
      apiClient.setTokens(data.access_token, data.refresh_token);

      // The access token is the only source of truth for "who logged in" —
      // its claims are `sub` (user id) and `username` only. The backend has
      // no /auth/me or role/actor endpoint yet, so role/actor_id can't come
      // from the API. If a profile was previously seen locally (a demo user,
      // or someone who registered from this browser) we enrich the display
      // with it; otherwise we fall back to a generic entity profile.
      const claims = decodeJwt(data.access_token);
      const userId = claims?.sub || `usr-${Date.now()}`;
      const resolvedUsername = claims?.username || username;

      const localUsers: AuthUser[] = JSON.parse(localStorage.getItem('iip_all_users') || '[]');
      const knownProfile = [...localUsers, ...DEMO_USERS].find(
        (u) =>
          u.username.toLowerCase() === resolvedUsername.toLowerCase() ||
          u.email.toLowerCase() === resolvedUsername.toLowerCase()
      );

      const user: AuthUser = knownProfile
        ? {
            ...knownProfile,
            id: userId,
            username: resolvedUsername,
            is_active: true,
            approval_status: 'approved',
          }
        : {
            id: userId,
            username: resolvedUsername,
            email: `${resolvedUsername}@entidad.gov.co`,
            role: resolvedUsername.toLowerCase().includes('admin') ? 'admin' : 'entity',
            is_active: true,
          };

      return { user, tokens: data };
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        // Mock login response
        const matched = DEMO_USERS.find(
          (u) =>
            u.username.toLowerCase() === username.toLowerCase() ||
            u.email.toLowerCase() === username.toLowerCase()
        );

        if (!matched && password !== 'admin1234' && password !== '12345678') {
          // Allow mock demo login with standard passwords or create entity session
        }

        const user: AuthUser = matched || {
          id: `usr-${Date.now()}`,
          username,
          email: username.includes('@') ? username : `${username}@bogota.gov.co`,
          role: username.toLowerCase().includes('admin') ? 'admin' : 'entity',
          actor_id: 'act-001',
          actor_label: 'Entidad Pública Distrital',
        };

        const mockTokens: LoginResponse = {
          access_token: `mock_ed25519_jwt_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          refresh_token: `mock_refresh_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          message: 'Auth successful (mock mode - Ed25519 simulation)',
          token_type: 'bearer',
        };

        apiClient.setTokens(mockTokens.access_token, mockTokens.refresh_token);
        return { user, tokens: mockTokens };
      }
      throw err;
    }
  },

  /**
   * POST /public/auth/register
   */
  async register(payload: RegisterPayload): Promise<{ status: string; message: string }> {
    try {
      const { data } = await apiClient.request('auth', '/public/auth/register', {
        method: 'POST',
        body: payload,
        isAuthAction: 'register',
      });
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        return { status: 'success', message: 'Usuario registrado exitosamente (Modo Local).' };
      }
      throw err;
    }
  },

  /**
   * POST /public/auth/reauth
   */
  async reauth(): Promise<LoginResponse> {
    try {
      const { data } = await apiClient.request<LoginResponse>('auth', '/public/auth/reauth', {
        method: 'POST',
        isAuthAction: 'reauth',
      });
      apiClient.setTokens(data.access_token, data.refresh_token);
      return data;
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') {
        const refreshed: LoginResponse = {
          access_token: `mock_ed25519_reauth_${Date.now()}`,
          refresh_token: `mock_refresh_rotated_${Date.now()}`,
          message: 'Token rotated successfully (mock mode)',
          token_type: 'bearer',
        };
        apiClient.setTokens(refreshed.access_token, refreshed.refresh_token);
        return refreshed;
      }
      throw err;
    }
  },

  /**
   * POST /public/auth/logout
   */
  async logout(): Promise<void> {
    try {
      await apiClient.request('auth', '/public/auth/logout', {
        method: 'POST',
        isAuthAction: 'logout',
      });
    } catch (err: any) {
      // ignore network errors on logout
    } finally {
      apiClient.clearTokens();
    }
  },
};
