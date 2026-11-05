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

/** Elemento de GET /public/auth/users (solo admin). */
export interface UserListItem {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  updated_at?: string;
  system_roles: string[];
  actor_id?: string;
  actor_label?: string;
  actor_segment_label?: string;
  contact_person?: string;
  phone?: string;
}

export function mapListItemToAuthUser(u: UserListItem): AuthUser {
  return {
    id: u.id,
    username: u.username,
    email: u.email,
    role: u.system_roles.includes('admin') ? 'admin' : 'entity',
    actor_id: u.actor_id,
    actor_label: u.actor_label,
    actor_segment_label: u.actor_segment_label,
    is_active: u.is_active,
    approval_status: u.is_active ? 'approved' : 'rejected',
    created_at: u.updated_at,
    contact_person: u.contact_person,
    phone: u.phone,
  };
}

export const authService = {
  /** GET /public/auth/users — solo administradores. */
  async listUsers(): Promise<AuthUser[]> {
    const { data } = await apiClient.request<UserListItem[]>('auth', '/public/auth/users', {
      method: 'GET',
      requiresAuth: true,
    });
    return data.map(mapListItemToAuthUser);
  },

  /** PUT /public/auth/users/{id} — activar/desactivar o editar contacto. */
  async updateUser(
    id: string,
    body: { is_active?: boolean; contact_person?: string; phone?: string }
  ): Promise<void> {
    await apiClient.request('auth', `/public/auth/users/${id}`, {
      method: 'PUT',
      body,
      requiresAuth: true,
    });
  },

  /** DELETE /public/auth/users/{id}. */
  async deleteUser(id: string): Promise<void> {
    await apiClient.request('auth', `/public/auth/users/${id}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },

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
