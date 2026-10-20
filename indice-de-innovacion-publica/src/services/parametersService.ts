import { apiClient } from './apiClient';

export interface ParamColumn {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'integer' | 'number' | 'boolean';
  required: boolean;
  max_length: number | null;
  unit: 'bytes' | null;
  locked_on_edit: boolean;
}

export interface ParamTable {
  key: string;
  label: string;
  group: string;
  description: string;
  can_create: boolean;
  can_delete: boolean;
  columns: ParamColumn[];
}

export type ParamRow = { id: string; usage_count: number } & Record<string, any>;

const base = '/public/parameters';

export const parametersService = {
  async catalog(): Promise<ParamTable[]> {
    const { data } = await apiClient.request<ParamTable[]>('core', base, { requiresAuth: true });
    return data;
  },
  async list(key: string): Promise<ParamRow[]> {
    const { data } = await apiClient.request<ParamRow[]>('core', `${base}/${key}`, { requiresAuth: true });
    return data;
  },
  async create(key: string, body: Record<string, any>): Promise<ParamRow> {
    const { data } = await apiClient.request<ParamRow>('core', `${base}/${key}`, {
      method: 'POST',
      body,
      requiresAuth: true,
    });
    return data;
  },
  async update(key: string, id: string, body: Record<string, any>): Promise<ParamRow> {
    const { data } = await apiClient.request<ParamRow>('core', `${base}/${key}/${id}`, {
      method: 'PUT',
      body,
      requiresAuth: true,
    });
    return data;
  },
  async remove(key: string, id: string): Promise<void> {
    await apiClient.request('core', `${base}/${key}/${id}`, { method: 'DELETE', requiresAuth: true });
  },
};
