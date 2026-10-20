import { apiClient } from './apiClient';
import { AuthUser, LoginResponse, MeResponse, RegisterPayload } from '../types';

/**
 * Maps the backend's /auth/me response into the shape the UI renders.
 * This is the ONLY place a real AuthUser gets built — no localStorage
 * profile database, no guessing from the JWT. The database (via auth.py)
 * is the single source of truth for who a user is.
 */
export function mapMeToAuthUser(me: MeResponse): AuthUser {
  const primaryActorLink = me.actor_links[0];
  return {
    id: me.id,
    username: me.username,
    email: me.email,
    role: me.system_roles.includes('admin') ? 'admin' : 'entity',
    actor_id: primaryActorLink?.actor_id,
    actor_label: primaryActorLink?.actor_label,
    is_active: me.is_active,
    approval_status: 'approved',
    contact_person: me.name || undefined,
    phone: me.phone || undefined,
  };
}

export const authService = {
  /**
   * GET /public/auth/me
   */
  async getMe(): Promise<MeResponse> {
    const { data } = await apiClient.request<MeResponse>('auth', '/public/auth/me', {
      method: 'GET',
      requiresAuth: true,
    });
    return data;
  },

  /**
   * POST /public/auth/login
   */
  async login(username: string, password: string): Promise<{ user: AuthUser; tokens: LoginResponse }> {
    const { data } = await apiClient.request<LoginResponse>('auth', '/public/auth/login', {
      method: 'POST',
      body: { username, password },
      isAuthAction: 'login',
    });

    // Update tokens in client
    apiClient.setTokens(data.access_token, data.refresh_token);

    // Fetch the real profile from the backend right away — this is the
    // only source of truth for role/actor/contact info.
    const me = await this.getMe();
    const user = mapMeToAuthUser(me);

    return { user, tokens: data };
  },

  /**
   * POST /public/auth/register
   */
  async register(payload: RegisterPayload): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.request('auth', '/public/auth/register', {
      method: 'POST',
      body: payload,
      isAuthAction: 'register',
    });
    return data;
  },

  /**
   * POST /public/auth/reauth
   */
  async reauth(): Promise<LoginResponse> {
    const { data } = await apiClient.request<LoginResponse>('auth', '/public/auth/reauth', {
      method: 'POST',
      isAuthAction: 'reauth',
    });
    apiClient.setTokens(data.access_token, data.refresh_token);
    return data;
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
